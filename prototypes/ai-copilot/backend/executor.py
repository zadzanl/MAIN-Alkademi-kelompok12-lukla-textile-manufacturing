import httpx
from typing import Dict, Any, Optional
from .registry import READ_TOOL_CATALOG
from .schemas import ToolCallResult

class ReadOnlyToolExecutor:
    """
    Safely dispatches authorized read queries against the core Lukla API.
    Guarantees:
    1. Zero write capability (POST/PUT/DELETE are strictly rejected).
    2. Bearer token passthrough ensures RLS and RBAC are enforced natively by FastAPI.
    3. Handles RFC 7807 problem payloads without leaking stack traces.
    """
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        authorization_header: Optional[str],
        request_id: Optional[str]
    ) -> ToolCallResult:
        # 1. Invariant: Tool must exist in read catalog
        tool_def = next((t for t in READ_TOOL_CATALOG if t.name == tool_name), None)
        if not tool_def:
            return ToolCallResult(
                tool_call_id=tool_name,
                tool_name=tool_name,
                status_code=403,
                data={"error": f"Tool '{tool_name}' is not in the approved read-only catalog."}
            )

        if tool_def.method != "GET":
            return ToolCallResult(
                tool_call_id=tool_name,
                tool_name=tool_name,
                status_code=403,
                data={"error": f"Execution of mutating method '{tool_def.method}' is blocked by security policy."}
            )

        # 2. Prepare headers with auth context passthrough
        headers = {
            "Accept": "application/json",
        }
        if authorization_header:
            headers["Authorization"] = authorization_header
        if request_id:
            headers["X-Request-Id"] = request_id

        target_url = f"{self.base_url}{tool_def.endpoint_path}"

        # 3. Perform HTTP query
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
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
