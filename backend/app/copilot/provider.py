import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import httpx
from pydantic import BaseModel, Field

from .schemas import ChatMessage, ToolCallRequest, TokenUsage
from .config import CopilotSettings, copilot_settings
from .registry import export_tools_to_openai_schema

class LLMResponse(BaseModel):
    reply: str
    tool_calls: List[ToolCallRequest] = Field(default_factory=list)
    usage: TokenUsage = Field(default_factory=TokenUsage)

class BaseLLMProvider(ABC):
    @abstractmethod
    async def chat_turn(
        self,
        message: str,
        history: Optional[List[ChatMessage]] = None,
        tools: Optional[List[dict]] = None,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """Execute a conversational turn and return candidate reply, tool invocations, and token usage."""
        pass

# Backward compatibility alias
BaseLLMClient = BaseLLMProvider

class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic offline provider recognizing apparel manufacturing keywords:
    - kain, stok, bahan -> triggers get_stock_balances
    - order, pesanan -> triggers get_order_status
    - potong, cutting -> directs to cutting action shortcut
    - tally, jahit -> directs to sewing tally action shortcut
    - gaji, payroll, upah -> directs to payroll approval action shortcut
    - force_non_get_mutation -> triggers non-GET tool for testing physical barrier
    """
    async def chat_turn(
        self,
        message: str,
        history: Optional[List[ChatMessage]] = None,
        tools: Optional[List[dict]] = None,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        lower = message.lower()
        tools = tools or []
        tool_names = {t["name"] for t in tools}

        # Test trigger for testing non-GET rejection
        if "force_non_get_mutation" in lower or "test_mutation" in lower:
            return LLMResponse(
                reply="Mencoba menjalankan mutasi state...",
                tool_calls=[
                    ToolCallRequest(
                        id="call_mock_mutation_01",
                        tool_name="post_ledger_mutation",
                        arguments={"amount": 500000}
                    )
                ],
                usage=TokenUsage(prompt_tokens=25, completion_tokens=10, total_tokens=35)
            )

        # Inquiries regarding inventory / fabric stock
        if any(kw in lower for kw in ["stok", "kain", "bahan", "fleece"]):
            if "get_stock_balances" in tool_names:
                return LLMResponse(
                    reply="Stok kain fleece saat ini tersedia 1,250 meter di Gudang Bahan (Lot FL-09). Status persediaan mencukupi untuk pesanan produksi berjalan.",
                    tool_calls=[
                        ToolCallRequest(
                            id="call_mock_stock_01",
                            tool_name="get_stock_balances",
                            arguments={"status": "AVAILABLE"}
                        )
                    ],
                    usage=TokenUsage(prompt_tokens=45, completion_tokens=35, total_tokens=80)
                )

        # Inquiries regarding orders
        if any(kw in lower for kw in ["order", "pesanan", "spk"]):
            if "get_order_status" in tool_names:
                return LLMResponse(
                    reply="Status order aktif saat ini berada dalam tahap konfirmasi dan persiapan material cutting.",
                    tool_calls=[
                        ToolCallRequest(
                            id="call_mock_order_01",
                            tool_name="get_order_status",
                            arguments={}
                        )
                    ],
                    usage=TokenUsage(prompt_tokens=40, completion_tokens=25, total_tokens=65)
                )

        # Mutation intents - return polite redirection to Action Shortcuts
        if any(kw in lower for kw in ["potong", "cutting"]):
            return LLMResponse(
                reply="Untuk mencatat hasil pemotongan kain dan input persentase buangan (waste), silakan gunakan tautan pintas di bawah ini menuju modul Cutting.",
                tool_calls=[],
                usage=TokenUsage(prompt_tokens=30, completion_tokens=30, total_tokens=60)
            )

        if any(kw in lower for kw in ["tally", "sewing", "jahit"]):
            return LLMResponse(
                reply="Untuk mencatat tally output sewing 30 menit per operator, silakan buka formulir terminal sewing melalui tautan pintas di bawah ini.",
                tool_calls=[],
                usage=TokenUsage(prompt_tokens=30, completion_tokens=30, total_tokens=60)
            )

        if any(kw in lower for kw in ["payroll", "gaji", "upah", "borongan"]):
            return LLMResponse(
                reply="Untuk rekapitulasi penggajian borongan mingguan dan persetujuan transfer Sabtu, silakan akses halaman Payroll Mingguan melalui tautan pintas di bawah.",
                tool_calls=[],
                usage=TokenUsage(prompt_tokens=35, completion_tokens=30, total_tokens=65)
            )

        # Default greeting / assistance response
        return LLMResponse(
            reply="Halo! Saya Asisten Operasional Lukla. Saya dapat membantu memeriksa stok bahan kain, status order pesanan, dan progres lantai jahit secara langsung.",
            tool_calls=[],
            usage=TokenUsage(prompt_tokens=20, completion_tokens=30, total_tokens=50)
        )

# Backward compatibility alias
MockLLMClient = MockLLMProvider

class OpenAILLMProvider(BaseLLMProvider):
    """Production provider connecting to OpenAI or any standard OpenAI-compatible inference server."""
    def __init__(self, settings: Optional[CopilotSettings] = None):
        self.settings = settings or copilot_settings
        self.base_url = self.settings.COPILOT_BASE_URL.rstrip("/")
        self.api_key = self.settings.COPILOT_API_KEY
        self.model_name = self.settings.COPILOT_MODEL_NAME

    async def chat_turn(
        self,
        message: str,
        history: Optional[List[ChatMessage]] = None,
        tools: Optional[List[dict]] = None,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        sys_prompt = system_prompt or "You are Lukla Operational AI Copilot. Always be concise, helpful, and never attempt unauthorized writes."
        messages = [{"role": "system", "content": sys_prompt}]

        if history:
            for h in history:
                messages.append({"role": h.sender, "content": h.text})

        messages.append({"role": "user", "content": message})

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.settings.temperature,
            "max_tokens": self.settings.max_tokens
        }

        if tools:
            payload["tools"] = export_tools_to_openai_schema(tools)
            payload["tool_choice"] = "auto"

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(timeout=self.settings.COPILOT_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()

            choice = data["choices"][0]["message"]
            raw_usage = data.get("usage", {})
            usage = TokenUsage(
                prompt_tokens=raw_usage.get("prompt_tokens", 0),
                completion_tokens=raw_usage.get("completion_tokens", 0),
                total_tokens=raw_usage.get("total_tokens", 0)
            )

            tool_calls: List[ToolCallRequest] = []
            if "tool_calls" in choice and choice["tool_calls"]:
                for tc in choice["tool_calls"]:
                    args = tc["function"].get("arguments", {})
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except Exception:
                            args = {}
                    tool_calls.append(
                        ToolCallRequest(
                            id=tc.get("id", "call_openai"),
                            tool_name=tc["function"]["name"],
                            arguments=args
                        )
                    )

            return LLMResponse(
                reply=choice.get("content") or "",
                tool_calls=tool_calls,
                usage=usage
            )

class OllamaLLMProvider(OpenAILLMProvider):
    """Production provider tailored for local Ollama deployments."""
    def __init__(self, settings: Optional[CopilotSettings] = None):
        super().__init__(settings)
        if not self.base_url or "openai" in self.base_url:
            self.base_url = "http://localhost:11434/v1"

def get_llm_provider(provider_type: Optional[str] = None) -> BaseLLMProvider:
    """Factory creating LLM provider based on configuration."""
    ptype = (provider_type or copilot_settings.COPILOT_DEFAULT_PROVIDER).lower()
    if ptype == "ollama":
        return OllamaLLMProvider()
    if ptype in ("openai", "anthropic"):
        return OpenAILLMProvider()
    return MockLLMProvider()
