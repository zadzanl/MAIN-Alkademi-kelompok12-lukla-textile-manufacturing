import os
from typing import Literal
from pydantic import BaseModel, Field

class CopilotSettings(BaseModel):
    AI_COPILOT_ENABLED: bool = Field(
        default_factory=lambda: os.getenv("AI_COPILOT_ENABLED", "true").lower() in ("true", "1", "yes")
    )
    COPILOT_DEFAULT_PROVIDER: Literal["mock", "ollama", "openai", "anthropic", "openrouter"] = Field(
        default_factory=lambda: os.getenv("COPILOT_DEFAULT_PROVIDER", os.getenv("COPILOT_LLM_PROVIDER", "mock"))
    )
    COPILOT_TIMEOUT_SECONDS: float = Field(
        default_factory=lambda: float(os.getenv("COPILOT_TIMEOUT_SECONDS", "30.0"))
    )
    COPILOT_MODEL_NAME: str = Field(
        default_factory=lambda: os.getenv("COPILOT_MODEL_NAME", "meta-llama/llama-3.3-70b-instruct:free")
    )
    COPILOT_API_KEY: str = Field(
        default_factory=lambda: os.getenv("COPILOT_API_KEY", os.getenv("OPENROUTER_API_KEY", ""))
    )
    COPILOT_BASE_URL: str = Field(
        default_factory=lambda: os.getenv("COPILOT_BASE_URL", "https://openrouter.ai/api/v1")
    )
    INTERNAL_API_BASE_URL: str = Field(
        default_factory=lambda: os.getenv("INTERNAL_API_BASE_URL", "http://localhost:8000/api/v1")
    )
    temperature: float = 0.1
    max_tokens: int = 2048
    system_prompt_locale: Literal["id", "en"] = "id"

copilot_settings = CopilotSettings()
