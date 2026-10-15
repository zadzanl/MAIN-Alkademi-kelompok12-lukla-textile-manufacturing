import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

class ActionShortcut(BaseModel):
    """
    User-facing action shortcut deep-link.
    Directs operators to state-mutating UI forms with prefilled parameters
    while enforcing zero autonomous write execution for LLMs.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    title: str
    description: str
    url: str
    icon: Optional[str] = "link"

class ChatMessage(BaseModel):
    """
    Single message in the conversational history.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender: Literal["user", "assistant"]
    text: str
    shortcuts: Optional[List[ActionShortcut]] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ChatTurnRequest(BaseModel):
    """
    Incoming chat payload from client widget.
    """
    message: str = Field(..., min_length=1, max_length=4000)
    history: Optional[List[ChatMessage]] = Field(default=None, max_length=10)
    roles: Optional[List[str]] = None
    stream: bool = False

class TokenUsage(BaseModel):
    """
    Inference token usage breakdown.
    """
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class ChatTurnResponse(BaseModel):
    """
    Completed turn response returned to the client.
    """
    reply: str
    shortcuts: List[ActionShortcut] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
    usage: TokenUsage = Field(default_factory=TokenUsage)

class ToolDefinition(BaseModel):
    """
    Declarative representation of an approved OpenAPI read operation.
    """
    name: str
    description: str
    endpoint_path: str
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = "GET"
    allowed_roles: List[str]
    parameters: Dict[str, Any] = Field(default_factory=dict)
    operation_id: Optional[str] = None

class ToolCallRequest(BaseModel):
    id: str
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)

class ToolCallResult(BaseModel):
    tool_call_id: str
    tool_name: str
    status_code: int
    data: Any = None
