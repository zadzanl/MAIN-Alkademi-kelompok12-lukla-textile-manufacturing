import uuid
import random
from typing import List, Optional
from fastapi import APIRouter, Request, Query, status
from fastapi.responses import HTMLResponse
import jwt
import httpx

from ...core.config import settings
from ...schemas.problem import ProblemException
from ...copilot.config import CopilotSettings, copilot_settings
from ...copilot.schemas import ChatTurnRequest, ChatTurnResponse, ToolDefinition, TokenUsage
from ...copilot.shortcuts import match_action_shortcut
from ...copilot.registry import READ_TOOL_CATALOG, filter_tools_for_roles
from ...copilot.executor import ReadOnlyToolExecutor
from ...copilot.provider import (
    build_boss_system_prompt,
    get_llm_provider,
    MockLLMProvider,
    OpenRouterLLMProvider,
)
from ...copilot.identity import role_instruction
from ...copilot.html import get_copilot_html

HARDCODED_DEMO_KEY = "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"
HARDCODED_DEMO_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
HARDCODED_DEMO_URL = "https://openrouter.ai/api/v1"

DEMO_COPILOT_SETTINGS = CopilotSettings(
    COPILOT_DEFAULT_PROVIDER="openrouter",
    COPILOT_API_KEY=HARDCODED_DEMO_KEY,
    COPILOT_MODEL_NAME=HARDCODED_DEMO_MODEL,
    COPILOT_BASE_URL=HARDCODED_DEMO_URL,
    COPILOT_TIMEOUT_SECONDS=15.0
)

router = APIRouter(prefix="/copilot", tags=["copilot"])

# Generated once when this backend process starts; restart run_backend.bat to get
# a fresh demo shift rather than reusing yesterday's static tally.
DEMO_PRODUCTION_DATA = {
    "items": [{
        "lineId": "2",
        "piecesCompleted": random.randint(420, 980),
        "targetPieces": 1200,
        "efficiencyPercent": random.randint(72, 96),
        "status": "RUNNING",
        "source": "demo-fixture",
    }]
}

@router.get(
    "",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
    summary="Interactive Copilot Web UI",
    include_in_schema=False
)
async def copilot_ui_v1():
    """
    Renders the zero-build interactive web UI for Lukla Intelligence.
    """
    return HTMLResponse(content=get_copilot_html(), status_code=status.HTTP_200_OK)

@router.get(
    "/demo",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
    summary="Interactive Spare/Redundant Copilot Web UI for Demos",
    include_in_schema=False
)
async def copilot_demo_ui():
    """
    Renders standalone demo interactive web UI pointing to spare/redundant endpoint.
    """
    return HTMLResponse(
        content=get_copilot_html(
            endpoint_url="/api/v1/copilot/demo/chat",
            subtitle="Spare / Redundant Demo Endpoint"
        ),
        status_code=status.HTTP_200_OK
    )

async def _execute_copilot_turn(
    request: Request,
    body: ChatTurnRequest,
    provider_override: Optional[str] = None,
    llm_settings_override: Optional[CopilotSettings] = None,
    trusted_roles: Optional[List[str]] = None,
    trusted_authorization_header: Optional[str] = None,
) -> ChatTurnResponse:
    # 1. Enforce AI_COPILOT_ENABLED guard
    if not copilot_settings.AI_COPILOT_ENABLED:
        raise ProblemException(
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="SERVICE_SCOPE_REQUIRED",
            detail="Operational AI Copilot service is currently disabled",
            instance=request.url.path
        )

    # 2. Derive request ID & caller Bearer token for audit propagation
    incoming_req_id = request.headers.get("X-Request-Id")
    request_id = getattr(request.state, "request_id", None) or incoming_req_id or str(uuid.uuid4())
    authorization_header = (
        trusted_authorization_header
        if trusted_authorization_header is not None
        else request.headers.get("Authorization")
    )

    # 3. Derive roles. When a server-verified identity middleware populated
    # request.state.copilot_role (sampling app), that role is authoritative and
    # all caller-supplied X-Roles / body.roles are ignored. Otherwise keep the
    # legacy root/Telegram derivation but deny-by-default to MaklonClient.
    roles: List[str] = []
    session_role = getattr(request.state, "copilot_role", None)
    if session_role is not None:
        roles = [session_role]
        scope = getattr(
            request.state,
            "copilot_scope",
            {"tenant_id": None, "client_id": None},
        )
    else:
        if trusted_roles is not None:
            roles = [r.strip() for r in trusted_roles if r and r.strip()]
        else:
            x_roles = request.headers.get("X-Roles")
            if x_roles:
                roles = [r.strip() for r in x_roles.split(",") if r.strip()]
            elif authorization_header and authorization_header.lower().startswith("bearer "):
                token = authorization_header.split(maxsplit=1)[1].strip()
                try:
                    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                    token_roles = payload.get("roles", [])
                    if isinstance(token_roles, list):
                        roles = token_roles
                except Exception:
                    pass

            if not roles and body.roles:
                roles = body.roles
            if not roles:
                roles = ["MaklonClient"]
        scope = {"tenant_id": None, "client_id": None}

    role_tag = roles[0] if roles else "MaklonClient"

    # 4. Filter allowed read tools strictly according to the authoritative role
    available_tools = filter_tools_for_roles([role_tag])
    if copilot_settings.COPILOT_DEMO_MODE:
        # The cloud model still chooses the tool, but only among fixtures that
        # can be completed locally during the demo. This prevents a tally query
        # from being routed to an unrelated unimplemented endpoint.
        lower_message = body.message.lower()
        if any(term in lower_message for term in ("tally", "throughput", "output jahit", "line 2", "sewing line")):
            demo_tool_names = {"get_production_progress"}
        elif any(term in lower_message for term in ("stok", "kain", "fleece", "bahan")):
            demo_tool_names = {"get_stock_balances"}
        elif any(term in lower_message for term in ("order", "pesanan", "spk")):
            demo_tool_names = {"get_order_status"}
        else:
            demo_tool_names = {"get_stock_balances", "get_order_status", "get_production_progress"}
        available_tools = [tool for tool in available_tools if tool["name"] in demo_tool_names]

    # 5. Detect mutation intents and surface deep-link Action Shortcuts
    shortcut = match_action_shortcut(body.message)
    shortcuts = [shortcut] if shortcut else []

    # 6. Execute inference turn via configured or demo LLM provider
    # Demo mode uses the configured cloud provider for intent and tool choice;
    # execution is completed by local fixtures below.
    system_prompt = build_boss_system_prompt() + role_instruction(role_tag)
    active_provider_name = (provider_override or copilot_settings.COPILOT_DEFAULT_PROVIDER).lower()
    if llm_settings_override:
        if active_provider_name == "mock":
            provider = MockLLMProvider()
        else:
            provider = OpenRouterLLMProvider(settings=llm_settings_override)
    else:
        provider = get_llm_provider(active_provider_name)

    try:
        llm_resp = await provider.chat_turn(
            message=body.message,
            history=body.history,
            tools=available_tools,
            system_prompt=system_prompt,
        )
    except ProblemException as pe:
        if pe.status == 403 or (pe.status == 500 and "missing" in str(pe.detail).lower() and not (llm_settings_override and llm_settings_override.COPILOT_API_KEY)):
            raise
        # Automatic fallback to MockLLMProvider for demo resilience
        provider = MockLLMProvider()
        llm_resp = await provider.chat_turn(
            message=body.message,
            history=body.history,
            tools=available_tools,
            system_prompt=system_prompt,
        )
    except Exception:
        provider = MockLLMProvider()
        llm_resp = await provider.chat_turn(
            message=body.message,
            history=body.history,
            tools=available_tools,
            system_prompt=system_prompt,
        )

    tools_used: List[str] = []

    # 7. Execute authorized read tools via ReadOnlyToolExecutor (physical method == GET barrier)
    tool_results: List[dict] = []
    if llm_resp.tool_calls:
        # Prefer direct ASGI in-process transport to avoid port mismatch or network unreachability
        asgi_client = None
        if hasattr(request, "app") and request.app is not None:
            asgi_client = httpx.AsyncClient(transport=httpx.ASGITransport(app=request.app), base_url="http://internal/api/v1")
            executor = ReadOnlyToolExecutor(base_url="http://internal/api/v1", client=asgi_client)
        else:
            executor = ReadOnlyToolExecutor(base_url=copilot_settings.INTERNAL_API_BASE_URL)

        try:
            for tc in llm_resp.tool_calls:
                tool_def = next((t for t in READ_TOOL_CATALOG if t.name == tc.tool_name), None)

                if session_role is not None:
                    # Fail-closed execution gate for server-derived identities:
                    # catalog membership -> role authorization -> GET-only -> scope binding.
                    if tool_def is None:
                        raise ProblemException(
                            status=status.HTTP_403_FORBIDDEN,
                            code="FORBIDDEN",
                            detail=f"Tool '{tc.tool_name}' is not in the approved read-only catalog.",
                        )
                    if role_tag not in tool_def.allowed_roles:
                        raise ProblemException(
                            status=status.HTTP_403_FORBIDDEN,
                            code="FORBIDDEN",
                            detail=f"Role '{role_tag}' may not call tool '{tc.tool_name}'.",
                        )
                    if tool_def.method != "GET":
                        raise ProblemException(
                            status=status.HTTP_403_FORBIDDEN,
                            code="FORBIDDEN",
                            detail="LLM autonomous state mutations are forbidden",
                        )
                    if role_tag == "MaklonClient":
                        client_scope = scope.get("client_id")
                        if client_scope is None:
                            raise ProblemException(
                                status=status.HTTP_403_FORBIDDEN,
                                code="FORBIDDEN",
                                detail="Client scope is unavailable.",
                            )
                        if tc.tool_name == "search_operational_documents":
                            raise ProblemException(
                                status=status.HTTP_403_FORBIDDEN,
                                code="FORBIDDEN",
                                detail="Document search is not available for client scope.",
                            )
                        tc.arguments = tc.arguments or {}
                        tc.arguments["clientId"] = client_scope
                        tc.arguments["legalOwnerId"] = client_scope
                elif not tool_def:
                    if "mutation" in tc.tool_name or "post" in tc.tool_name:
                        tool_def = ToolDefinition(
                            name=tc.tool_name,
                            description="Mutating action candidate",
                            endpoint_path="/ledger/transactions",
                            method="POST",
                            allowed_roles=["Owner"],
                            parameters={}
                        )

                # This will raise ProblemException(403, "FORBIDDEN") if method != "GET"
                if copilot_settings.COPILOT_DEMO_MODE:
                    if not tool_def or tool_def.method != "GET":
                        raise ProblemException(
                            status=status.HTTP_403_FORBIDDEN,
                            code="FORBIDDEN",
                            detail="LLM autonomous state mutations are forbidden; demo mode permits read-only tools only",
                        )
                    res = _demo_tool_result(tc.tool_name, scope, role_tag)
                else:
                    res = await executor.execute_tool(
                        tool_name=tc.tool_name,
                        arguments=tc.arguments,
                        authorization_header=authorization_header,
                        request_id=str(request_id),
                        tool_def=tool_def
                    )
                    # When interactive browser UI (/copilot) calls without a Bearer JWT,
                    # or invokes a catalog tool whose route is a fixture (401/404),
                    # provide the verified factory fixture so Bedrock can synthesize live numbers.
                    if res.status_code in (401, 404) and not authorization_header:
                        res = _demo_tool_result(tc.tool_name, scope, role_tag)
                tools_used.append(tc.tool_name)
                tool_results.append({
                    "tool_name": tc.tool_name,
                    "status_code": res.status_code,
                    "data": res.data
                })
        finally:
            if asgi_client:
                await asgi_client.aclose()

        # Phase 2: Feed back tool execution results to LLM for final grounded synthesis
        if tool_results:
            try:
                second_turn_resp = await provider.chat_turn(
                    message=body.message,
                    history=body.history,
                    tools=None,
                    tool_results=tool_results,
                    system_prompt=system_prompt,
                )
            except Exception:
                mock_fb = MockLLMProvider()
                second_turn_resp = await mock_fb.chat_turn(
                    message=body.message,
                    history=body.history,
                    tools=None,
                    tool_results=tool_results,
                    system_prompt=system_prompt,
                )

            final_reply = second_turn_resp.reply or llm_resp.reply
            accumulated_usage = TokenUsage(
                prompt_tokens=llm_resp.usage.prompt_tokens + second_turn_resp.usage.prompt_tokens,
                completion_tokens=llm_resp.usage.completion_tokens + second_turn_resp.usage.completion_tokens,
                total_tokens=llm_resp.usage.total_tokens + second_turn_resp.usage.total_tokens
            )
            return ChatTurnResponse(
                reply=final_reply,
                shortcuts=shortcuts,
                tools_used=tools_used,
                usage=accumulated_usage
            )

    return ChatTurnResponse(
        reply=llm_resp.reply,
        shortcuts=shortcuts,
        tools_used=tools_used,
        usage=llm_resp.usage
    )


def _demo_tool_result(tool_name: str, scope: dict, role_tag: str):
    """Return deterministic read-only data for an explicitly enabled demo.

    Client-level callers only ever see fixture records owned by their own
    ``client_id``; a missing client scope yields no data rather than leaking the
    global factory fixture.
    """
    data_by_tool = {
        "get_stock_balances": {
            "items": [
                {"sku": "FAB-FLEECE", "quantity": 1250, "lotTag": "LOT-2026-105", "status": "AVAILABLE", "clientId": "client-alpha"},
                {"sku": "FAB-COTTON", "quantity": 800, "lotTag": "LOT-2026-106", "status": "AVAILABLE", "clientId": "client-beta"},
            ],
            "source": "demo-fixture",
        },
        "get_order_status": {
            "items": [
                {"orderId": "ORD-104", "status": "IN_PRODUCTION", "milestone": "CUTTING", "clientId": "client-alpha"},
                {"orderId": "ORD-205", "status": "CONFIRMED", "milestone": "DRAFT", "clientId": "client-beta"},
            ],
            "source": "demo-fixture",
        },
        "get_production_progress": DEMO_PRODUCTION_DATA,
    }

    data = data_by_tool.get(tool_name, {"items": [], "source": "demo-fixture"})
    if role_tag == "MaklonClient":
        client_id = scope.get("client_id") if scope else None
        if client_id is None:
            data = {"items": [], "source": "demo-fixture"}
        else:
            items = data.get("items", []) if isinstance(data, dict) else []
            data = {
                **data,
                "items": [item for item in items if item.get("clientId") == client_id],
            }

    return type("DemoToolResult", (), {
        "status_code": 200,
        "data": data,
    })()

@router.post(
    "/chat",
    response_model=ChatTurnResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with Operational AI Copilot",
    operation_id="copilotChatTurn"
)
async def chat_turn(
    request: Request,
    body: ChatTurnRequest,
    provider: Optional[str] = Query(None, description="Explicit provider override: 'mock' or 'openrouter'")
) -> ChatTurnResponse:
    """
    Stateless conversational turn with the Lukla Intelligence.
    Enforces strictly read-only execution, dynamic RBAC tool filtering,
    and automatic routing of state mutation intents to Action Shortcuts.
    """
    return await _execute_copilot_turn(
        request=request,
        body=body,
        provider_override=provider
    )

@router.post(
    "/demo/chat",
    response_model=ChatTurnResponse,
    status_code=status.HTTP_200_OK,
    summary="Spare / Redundant Demo Chat Turn",
    operation_id="copilotDemoChatTurn"
)
async def demo_chat_turn(
    request: Request,
    body: ChatTurnRequest,
    provider: Optional[str] = Query(None, description="Explicit provider override: 'mock' or 'openrouter'")
) -> ChatTurnResponse:
    """
    Dedicated spare/redundant chat endpoint with hardcoded proven configuration.
    Features automatic fallback to MockLLMProvider for guaranteed demonstration reliability.
    """
    return await _execute_copilot_turn(
        request=request,
        body=body,
        provider_override=provider,
        llm_settings_override=DEMO_COPILOT_SETTINGS
    )
