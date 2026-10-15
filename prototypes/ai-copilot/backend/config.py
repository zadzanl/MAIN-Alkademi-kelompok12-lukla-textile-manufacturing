import os
from typing import Literal
from pydantic import BaseModel, Field

class CopilotSettings(BaseModel):
    provider: Literal["ollama", "openai", "anthropic", "mock"] = Field(
        default_factory=lambda: os.getenv("COPILOT_LLM_PROVIDER", "mock")
    )
    model_name: str = Field(
        default_factory=lambda: os.getenv("COPILOT_MODEL_NAME", "qwen2.5:7b")
    )
    api_key: str = Field(
        default_factory=lambda: os.getenv("COPILOT_API_KEY", "")
    )
    base_url: str = Field(
        default_factory=lambda: os.getenv("COPILOT_BASE_URL", "http://localhost:11434/v1")
    )
    temperature: float = 0.1
    max_tokens: int = 2048
    system_prompt_locale: Literal["id", "en"] = "id"
    internal_api_base_url: str = Field(
        default_factory=lambda: os.getenv("INTERNAL_API_BASE_URL", "http://localhost:8000/api/v1")
    )

copilot_settings = CopilotSettings()
