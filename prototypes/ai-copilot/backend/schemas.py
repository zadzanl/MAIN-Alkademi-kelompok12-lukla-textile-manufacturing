from typing import List, Dict, Any, Optional, Literal
import uuid
from pydantic import BaseModel, Field

class ActionShortcut(BaseModel):
    """
    User-facing action shortcut deep-link.
    Allows the read-only assistant to guide users to write-oriented screens 
    without executing autonomous mutations.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    url: str
    prefill_params: Optional[Dict[str, Any]] = None
    icon: Optional[str] = "external-link"

class ToolCallRequest(BaseModel):
    id: str
    tool_name: str
    arguments: Dict[str, Any]

class ToolCallResult(BaseModel):
    tool_call_id: str
    tool_name: str
    status_code: int
    data: Any

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system", "tool"]
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCallRequest]] = None
    tool_call_id: Optional[str] = None

class ChatTurnRequest(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str
    history: List[ChatMessage] = Field(default_factory=list)

class ChatTurnResponse(BaseModel):
    session_id: str
    reply: str
    shortcuts: List[ActionShortcut] = Field(default_factory=list)
    tool_invocations: List[ToolCallResult] = Field(default_factory=list)

class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
    allowed_roles: List[str]
    operation_id: str
    method: Literal["GET"] = "GET"
    endpoint_path: str
