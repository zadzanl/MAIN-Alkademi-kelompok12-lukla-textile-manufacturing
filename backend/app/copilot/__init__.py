"""
Lukla Intelligence Package.
Provides conversational operational assistance with strictly read-only execution,
per-turn role-based tool filtering, and mutation intent routing via Action Shortcuts.
"""

from .config import CopilotSettings, copilot_settings
from .schemas import (
    ActionShortcut,
    ChatMessage,
    ChatTurnRequest,
    ChatTurnResponse,
    TokenUsage,
    ToolDefinition,
    ToolCallRequest,
    ToolCallResult,
)
from .shortcuts import (
    match_action_shortcut,
    match_action_shortcuts,
    SHORTCUT_ROUTES,
)
from .registry import (
    READ_TOOL_CATALOG,
    filter_tools_for_roles,
    export_tools_to_openai_schema,
)
from .executor import ReadOnlyToolExecutor
from .provider import (
    BaseLLMProvider,
    BaseLLMClient,
    MockLLMProvider,
    MockLLMClient,
    OllamaLLMProvider,
    OpenAILLMProvider,
    OpenRouterLLMProvider,
    get_llm_provider,
)

__all__ = [
    "CopilotSettings",
    "copilot_settings",
    "ActionShortcut",
    "ChatMessage",
    "ChatTurnRequest",
    "ChatTurnResponse",
    "TokenUsage",
    "ToolDefinition",
    "ToolCallRequest",
    "ToolCallResult",
    "match_action_shortcut",
    "match_action_shortcuts",
    "SHORTCUT_ROUTES",
    "READ_TOOL_CATALOG",
    "filter_tools_for_roles",
    "export_tools_to_openai_schema",
    "ReadOnlyToolExecutor",
    "BaseLLMProvider",
    "BaseLLMClient",
    "MockLLMProvider",
    "MockLLMClient",
    "OllamaLLMProvider",
    "OpenAILLMProvider",
    "get_llm_provider",
]
