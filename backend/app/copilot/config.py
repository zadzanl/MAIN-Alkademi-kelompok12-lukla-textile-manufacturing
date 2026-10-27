import os
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

class CopilotSettings(BaseModel):
    COPILOT_DEMO_MODE: bool = Field(
        default_factory=lambda: os.getenv("COPILOT_DEMO_MODE", "true").lower() in ("true", "1", "yes")
    )
    AI_COPILOT_ENABLED: bool = Field(
        default_factory=lambda: os.getenv("AI_COPILOT_ENABLED", "true").lower() in ("true", "1", "yes")
    )
    COPILOT_DEFAULT_PROVIDER: Literal["mock", "ollama", "openai", "anthropic", "openrouter", "bedrock"] = Field(
        default_factory=lambda: os.getenv("COPILOT_DEFAULT_PROVIDER", os.getenv("COPILOT_LLM_PROVIDER", "openrouter"))
    )
    COPILOT_TIMEOUT_SECONDS: float = Field(
        default_factory=lambda: float(os.getenv("COPILOT_TIMEOUT_SECONDS", "30.0"))
    )
    COPILOT_MODEL_NAME: str = Field(
        default_factory=lambda: os.getenv(
            "COPILOT_MODEL_NAME",
            os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-super-120b-a12b:free"),
        )
    )
    AWS_REGION: str = Field(
        default_factory=lambda: os.getenv("AWS_REGION", "us-east-1")
    )
    BEDROCK_MODEL_ID: str = Field(
        default_factory=lambda: os.getenv("BEDROCK_MODEL_ID", "us.amazon.nova-micro-v1:0")
    )
    COPILOT_API_KEY: str = Field(
        # Owner-reported restriction: OpenRouter free-tier routes only, with an approximately USD 0.05 spend cap.
        default_factory=lambda: os.getenv("COPILOT_API_KEY", os.getenv("OPENROUTER_API_KEY", "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"))
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
