from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import httpx
from .schemas import ChatMessage, ToolCallRequest
from .config import CopilotSettings

class BaseLLMClient(ABC):
    @abstractmethod
    async def chat_complete(
        self,
        messages: List[ChatMessage],
        tools: List[Dict[str, Any]],
        system_prompt: str
    ) -> Dict[str, Any]:
        """Generate response with optional tool calls."""
        pass

class MockLLMClient(BaseLLMClient):
    """Deterministic mock client for offline testing and initial prototype verification."""
    async def chat_complete(
        self,
        messages: List[ChatMessage],
        tools: List[Dict[str, Any]],
        system_prompt: str
    ) -> Dict[str, Any]:
        last_user_msg = next((m.content for m in reversed(messages) if m.role == "user"), "")
        lower_msg = last_user_msg.lower() if last_user_msg else ""

        # If user asks about stock and tools are available, trigger tool call
        if ("stok" in lower_msg or "kain" in lower_msg or "bahan" in lower_msg) and any(t["function"]["name"] == "get_stock_balances" for t in tools):
            return {
                "content": None,
                "tool_calls": [
                    ToolCallRequest(
                        id="call_mock_stock_01",
                        tool_name="get_stock_balances",
                        arguments={"status": "AVAILABLE"}
                    )
                ]
            }

        # If user asks about cutting or action
        if "potong" in lower_msg or "cutting" in lower_msg:
            return {
                "content": "Untuk mencatat pemotongan kain dan input persentase buangan (waste), silakan gunakan tautan pintas di bawah ini menuju modul Cutting.",
                "tool_calls": None
            }

        return {
            "content": f"Halo! Saya Asisten Operasional Lukla. Saya dapat membantu memeriksa status pesanan, stok gudang, dan throughput lantai jahit secara langsung.",
            "tool_calls": None
        }

class OpenAICompatibleLLMClient(BaseLLMClient):
    """Compatible with OpenAI, Anthropic adapters, Ollama (v1), and vLLM."""
    def __init__(self, settings: CopilotSettings):
        self.settings = settings
        self.base_url = settings.base_url.rstrip("/")
        self.api_key = settings.api_key
        self.model_name = settings.model_name

    async def chat_complete(
        self,
        messages: List[ChatMessage],
        tools: List[Dict[str, Any]],
        system_prompt: str
    ) -> Dict[str, Any]:
        payload_messages = [{"role": "system", "content": system_prompt}]
        for m in messages:
            msg_dict: Dict[str, Any] = {"role": m.role, "content": m.content or ""}
            if m.tool_calls:
                msg_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.tool_name, "arguments": str(tc.arguments)}
                    }
                    for tc in m.tool_calls
                ]
            if m.tool_call_id:
                msg_dict["tool_call_id"] = m.tool_call_id
            payload_messages.append(msg_dict)

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": payload_messages,
            "temperature": self.settings.temperature,
            "max_tokens": self.settings.max_tokens
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            choice = data["choices"][0]["message"]

            tool_calls = None
            if "tool_calls" in choice and choice["tool_calls"]:
                tool_calls = [
                    ToolCallRequest(
                        id=tc["id"],
                        tool_name=tc["function"]["name"],
                        arguments=tc["function"].get("arguments", {})
                    )
                    for tc in choice["tool_calls"]
                ]

            return {
                "content": choice.get("content"),
                "tool_calls": tool_calls
            }
