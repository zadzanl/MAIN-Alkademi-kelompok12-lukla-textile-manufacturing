import httpx
from typing import Dict, Any, Optional
from ..schemas.problem import ProblemException
from .registry import READ_TOOL_CATALOG
from .schemas import ToolCallResult, ToolDefinition

class ReadOnlyToolExecutor:
    """
    Safely dispatches authorized read queries against the core Lukla API.
    Guarantees:
    1. Zero write capability (POST/PUT/DELETE/PATCH are strictly rejected with 403 Forbidden).
    2. Bearer token passthrough ensures RLS and RBAC are enforced natively by FastAPI/PostgreSQL.
    3. Propagates X-Request-Id for distributed audit tracing.
    4. Handles RFC 7807 problem payloads without leaking stack traces.
    """
    def __init__(self, base_url: str = "http://127.0.0.1:8000/api/v1", client: Optional[httpx.AsyncClient] = None):
        self.base_url = base_url.rstrip("/")
        self.client = client

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        authorization_header: Optional[str] = None,
        request_id: Optional[str] = None,
        tool_def: Optional[ToolDefinition] = None
    ) -> ToolCallResult:
        """
        Executes a single read tool invocation with strict method guard and auth context passthrough.
        """
        # 1. Look up tool definition if not explicitly provided
        if tool_def is None:
            tool_def = next((t for t in READ_TOOL_CATALOG if t.name == tool_name), None)

        if not tool_def:
            raise ProblemException(
                status=403,
                code="FORBIDDEN",
                detail=f"Tool '{tool_name}' is not in the approved read-only catalog."
            )

        # 2. Hard physical invariant: Mutating HTTP methods are strictly rejected
        if tool_def.method != "GET":
            raise ProblemException(
                status=403,
                code="FORBIDDEN",
                detail="LLM autonomous state mutations are forbidden"
            )

        # 3. Prepare headers with caller security context passthrough
        headers = {
            "Accept": "application/json",
        }
        if authorization_header:
            headers["Authorization"] = authorization_header
        if request_id:
            headers["X-Request-Id"] = request_id

        target_url = f"{self.base_url}{tool_def.endpoint_path}"
        arguments = arguments or {}

        # 4. Perform async HTTP query
        try:
            if self.client:
                response = await self.client.get(target_url, params=arguments, headers=headers)
            else:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(target_url, params=arguments, headers=headers)

            return ToolCallResult(
                tool_call_id=tool_name,
                tool_name=tool_name,
                status_code=response.status_code,
                data=response.json() if response.content else {}
            )
        except httpx.HTTPError as exc:
            return ToolCallResult(
                tool_call_id=tool_name,
                tool_name=tool_name,
                status_code=502,
                data={"error": "API gateway error connecting to operational engine", "detail": str(exc)}
            )
