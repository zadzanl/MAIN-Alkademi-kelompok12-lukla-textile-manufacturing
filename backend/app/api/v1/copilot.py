import uuid
from typing import List, Optional
from fastapi import APIRouter, Request, status
from fastapi.responses import HTMLResponse
import jwt

from ...core.config import settings
from ...schemas.problem import ProblemException
from ...copilot.config import copilot_settings
from ...copilot.schemas import ChatTurnRequest, ChatTurnResponse, ToolDefinition
from ...copilot.shortcuts import match_action_shortcut
from ...copilot.registry import READ_TOOL_CATALOG, filter_tools_for_roles
from ...copilot.executor import ReadOnlyToolExecutor
from ...copilot.provider import get_llm_provider
from ...copilot.html import get_copilot_html

router = APIRouter(prefix="/copilot", tags=["copilot"])

@router.get(
    "",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
    summary="Interactive Copilot Web UI",
    include_in_schema=False
)
async def copilot_ui_v1():
    """
    Renders the zero-build interactive web UI for Lukla Operations Copilot.
    """
    return HTMLResponse(content=get_copilot_html(), status_code=status.HTTP_200_OK)

@router.post(
    "/chat",
    response_model=ChatTurnResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with Operational AI Copilot",
    operation_id="copilotChatTurn"
)
async def chat_turn(
    request: Request,
    body: ChatTurnRequest
) -> ChatTurnResponse:
    """
    Stateless conversational turn with the Lukla Operational AI Copilot.
    Enforces strictly read-only execution, dynamic RBAC tool filtering,
    and automatic routing of state mutation intents to Action Shortcuts.
    """
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
    authorization_header = request.headers.get("Authorization")

    # 3. Derive roles from X-Roles header, Bearer JWT claims, or request body fallback
    roles: List[str] = []
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
        roles = ["Owner"]

    # 4. Filter allowed read tools strictly according to caller RBAC claims
    available_tools = filter_tools_for_roles(roles)

    # 5. Detect mutation intents and surface deep-link Action Shortcuts
    shortcut = match_action_shortcut(body.message)
    shortcuts = [shortcut] if shortcut else []

    # 6. Execute inference turn via configured LLM provider
    provider = get_llm_provider(copilot_settings.COPILOT_DEFAULT_PROVIDER)
    llm_resp = await provider.chat_turn(
        message=body.message,
        history=body.history,
        tools=available_tools
    )

    tools_used: List[str] = []

    # 7. Execute authorized read tools via ReadOnlyToolExecutor (physical method == GET barrier)
    if llm_resp.tool_calls:
        executor = ReadOnlyToolExecutor(base_url=copilot_settings.INTERNAL_API_BASE_URL)
        for tc in llm_resp.tool_calls:
            tool_def = next((t for t in READ_TOOL_CATALOG if t.name == tc.tool_name), None)
            if not tool_def:
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
            await executor.execute_tool(
                tool_name=tc.tool_name,
                arguments=tc.arguments,
                authorization_header=authorization_header,
                request_id=str(request_id),
                tool_def=tool_def
            )
            tools_used.append(tc.tool_name)

    return ChatTurnResponse(
        reply=llm_resp.reply,
        shortcuts=shortcuts,
        tools_used=tools_used,
        usage=llm_resp.usage
    )
