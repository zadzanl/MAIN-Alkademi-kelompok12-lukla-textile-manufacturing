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
        system_prompt: Optional[str] = None,
        tool_results: Optional[List[Dict[str, Any]]] = None
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
        system_prompt: Optional[str] = None,
        tool_results: Optional[List[Dict[str, Any]]] = None
    ) -> LLMResponse:
        lower = message.lower()
        tools = tools or []
        tool_names = {t["name"] for t in tools}

        # If tool results are provided (2nd pass of tool-call loop)
        if tool_results:
            # Check for error status in tool results
            has_error = any(
                tr.get("status_code", 200) >= 400
                or (isinstance(tr.get("data"), dict) and tr.get("data", {}).get("status", 200) in (404, 500, 502, 503))
                for tr in tool_results
            )
            if has_error:
                return LLMResponse(
                    reply="Maaf, data inventaris kain saat ini tidak dapat diambil dari sistem operasional (layanan gudang mengembalikan galat atau data belum tercatat).",
                    tool_calls=[],
                    usage=TokenUsage(prompt_tokens=50, completion_tokens=25, total_tokens=75)
                )

            # Success path: synthesize from verified tool data
            if "stok" in lower or "kain" in lower or "fleece" in lower:
                fleece_qty = 1250
                lot_tag = "LOT-2026-105"
                for tr in tool_results:
                    data = tr.get("data", {})
                    items = data.get("items", []) if isinstance(data, dict) else []
                    for it in items:
                        if isinstance(it, dict) and "fleece" in it.get("sku", "").lower():
                            fleece_qty = it.get("quantity", fleece_qty)
                            lot_tag = it.get("lotTag", lot_tag)

                return LLMResponse(
                    reply=f"Stok kain fleece saat ini terverifikasi melalui data sistem: tersedia {fleece_qty:,.0f} meter di Gudang Bahan (Lot: {lot_tag}). Persediaan mencukupi.",
                    tool_calls=[],
                    usage=TokenUsage(prompt_tokens=50, completion_tokens=30, total_tokens=80)
                )

            if "production" in {tr.get("tool_name") for tr in tool_results} or "get_production_progress" in {tr.get("tool_name") for tr in tool_results}:
                progress = next((tr.get("data", {}) for tr in tool_results if tr.get("tool_name") == "get_production_progress"), {})
                item = (progress.get("items") or [{}])[0]
                return LLMResponse(
                    reply=(
                        f"Tally Sewing Line {item.get('lineId', '2')} saat ini: "
                        f"{item.get('piecesCompleted', 0):,} pcs selesai dari target "
                        f"{item.get('targetPieces', 0):,} pcs "
                        f"({item.get('efficiencyPercent', 0)}% efisiensi). "
                        f"Status line: {item.get('status', 'UNKNOWN')}."
                    ),
                    tool_calls=[],
                    usage=TokenUsage(prompt_tokens=50, completion_tokens=35, total_tokens=85)
                )

            summary = []
            for tr in tool_results:
                t_name = tr.get("tool_name", "tool")
                data = tr.get("data", {})
                summary.append(f"{t_name}: {json.dumps(data) if isinstance(data, (dict, list)) else str(data)}")
            return LLMResponse(
                reply=f"Berdasarkan data sistem terkini: {'; '.join(summary)}",
                tool_calls=[],
                usage=TokenUsage(prompt_tokens=50, completion_tokens=30, total_tokens=80)
            )

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

        # Read-only production tally inquiry. Recording a tally remains an action shortcut.
        if any(kw in lower for kw in ["tally", "throughput", "output jahit", "produksi line", "line 2"]):
            if "get_production_progress" in tool_names:
                return LLMResponse(
                    reply="Saya akan memeriksa progress produksi Sewing Line 2.",
                    tool_calls=[ToolCallRequest(
                        id="call_mock_production_01",
                        tool_name="get_production_progress",
                        arguments={"lineId": "LINE-02"}
                    )],
                    usage=TokenUsage(prompt_tokens=40, completion_tokens=20, total_tokens=60)
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
        system_prompt: Optional[str] = None,
        tool_results: Optional[List[Dict[str, Any]]] = None
    ) -> LLMResponse:
        sys_prompt = system_prompt or (
            "You are Lukla Intelligence for apparel manufacturing operations.\n"
            "Your role is to assist operators, supervisors, and owners by providing verified, real-time factory data.\n\n"
            "=== READ-ONLY ACCESS & TOOL USAGE GUIDELINES ===\n"
            "1. You have strictly read-only access to factory data. You can never mutate, insert, or delete state.\n"
            "2. Whenever a user inquires about factory metrics, inventory, orders, or progress, always invoke the appropriate read tool first rather than guessing or fabricating numbers.\n"
            "3. If a tool returns data, answer directly and concisely referencing the verified live numbers.\n"
            "4. If a tool fails or returns an error (such as 404, 500, or problem payload), DO NOT invent figures or state that items are verified or sufficient. Honestly notify the user that live operational data is currently unavailable.\n\n"
            "=== AVAILABLE READ TOOLS & EXAMPLES ===\n"
            "Here are examples of read tools you can call when available in your catalog:\n"
            "- `get_stock_balances(status='AVAILABLE', legalOwnerId=...)`: Query warehouse inventory for raw fabrics (fleece, rib, cotton), WIP rolls, or finished goods. Example inquiry: 'Berapa stok kain fleece?' or 'Check inventory balance'.\n"
            "- `get_order_status(status=..., clientId=...)`: Check production orders, delivery commitments, and fulfillment milestones. Example inquiry: 'Bagaimana status pesanan ORD-104?' or 'Show active orders'.\n"
            "- `get_production_progress(lineId=..., orderId=...)`: Check line output rates, sewing throughput, and 30-minute interval pacing. Example inquiry: 'Cek progres jalur jahit Line 2' or 'Sewing output throughput'.\n"
            "- `get_qc_bonus_pool_status(periodId=...)`: Inspect weekly quality bonus pool accumulation and defect tolerances. Example inquiry: 'Berapa akumulasi bonus pool QC minggu ini?'.\n"
            "- `get_ledger_entries(accountCode=..., limit=...)`: Inspect double-entry journal logs, debit/credit balances, and financial trail. Example inquiry: 'Lihat mutasi jurnal akun kas'.\n"
            "- `search_operational_documents(q=...)`: Search technical tech packs, factory SOPs, and sewing specifications. Example inquiry: 'Cari SOP standar toleransi jahitan kerah'.\n"
            "- `get_sample_specs(sampleId=...)`: Query prototype sample grading, tech pack specs, and revision histories.\n\n"
            "=== MUTATION INTENTS ===\n"
            "If the user asks to modify data (such as cutting fabric, logging tallies, or posting journal entries), politely inform them that you are read-only and direct them to the appropriate action screen or form."
        )
        messages: List[Dict[str, Any]] = [{"role": "system", "content": sys_prompt}]

        if history:
            for h in history:
                messages.append({"role": h.sender, "content": h.text})

        messages.append({"role": "user", "content": message})

        if tool_results:
            # Append tool results into context so model can produce grounded answer
            results_str = "\n".join([
                f"- Tool '{tr.get('tool_name')}': {json.dumps(tr.get('data')) if isinstance(tr.get('data'), (dict, list)) else tr.get('data')}"
                for tr in tool_results
            ])
            messages.append({
                "role": "system",
                "content": f"The read-only factory tools returned the following live operational data:\n{results_str}\nPlease provide a concise answer directly addressing the user inquiry using this verified live data."
            })

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.settings.temperature,
            "max_tokens": self.settings.max_tokens
        }

        # If tool results already returned, do not require tool choice again to avoid loops
        if tools and not tool_results:
            payload["tools"] = export_tools_to_openai_schema(tools)
            payload["tool_choice"] = "auto"

        headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": "https://lukla.app",
            "X-Title": "Lukla Operations Engine Copilot"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(timeout=self.settings.COPILOT_TIMEOUT_SECONDS) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as exc:
                from ..schemas.problem import ProblemException
                detail_msg = f"LLM provider error ({exc.response.status_code})"
                try:
                    err_json = exc.response.json()
                    if "error" in err_json:
                        err_detail = err_json["error"].get("message") or str(err_json["error"])
                        detail_msg = f"LLM Provider: {err_detail}"
                except Exception:
                    detail_msg = f"LLM provider error: {exc.response.text[:200]}"

                raise ProblemException(
                    status=502 if exc.response.status_code >= 500 else 400,
                    code="SERVICE_SCOPE_REQUIRED" if exc.response.status_code == 401 else "BAD_GATEWAY",
                    detail=detail_msg
                )
            except httpx.RequestError as exc:
                from ..schemas.problem import ProblemException
                raise ProblemException(
                    status=504,
                    code="GATEWAY_TIMEOUT",
                    detail=f"Connection timeout reaching LLM provider: {str(exc)}"
                )

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
        if not self.base_url or "openai" in self.base_url or "openrouter" in self.base_url:
            self.base_url = "http://localhost:11434/v1"

class OpenRouterLLMProvider(OpenAILLMProvider):
    """Production provider connecting to OpenRouter inference gateway."""
    def __init__(self, settings: Optional[CopilotSettings] = None):
        super().__init__(settings)
        if not self.base_url or "localhost" in self.base_url:
            self.base_url = "https://openrouter.ai/api/v1"

    async def chat_turn(
        self,
        message: str,
        history: Optional[List[ChatMessage]] = None,
        tools: Optional[List[dict]] = None,
        system_prompt: Optional[str] = None,
        tool_results: Optional[List[Dict[str, Any]]] = None
    ) -> LLMResponse:
        if not self.api_key:
            from ..schemas.problem import ProblemException
            raise ProblemException(
                status=500,
                code="SERVICE_SCOPE_REQUIRED",
                detail="OpenRouter API key is missing. Please set COPILOT_API_KEY or OPENROUTER_API_KEY environment variable."
            )
        return await super().chat_turn(
            message=message,
            history=history,
            tools=tools,
            system_prompt=system_prompt,
            tool_results=tool_results
        )

class BedrockLLMProvider(BaseLLMProvider):
    """
    Production provider connecting to Amazon Bedrock Runtime.
    Leverages IAM Role / Instance Profile auto-detected credentials on AWS EC2.
    """
    def __init__(self, settings: Optional[CopilotSettings] = None):
        self.settings = settings or copilot_settings
        self.region_name = self.settings.AWS_REGION or "us-east-1"
        self.model_id = self.settings.BEDROCK_MODEL_ID or "us.amazon.nova-micro-v1:0"
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client("bedrock-runtime", region_name=self.region_name)
            except ImportError:
                from ..schemas.problem import ProblemException
                raise ProblemException(
                    status=500,
                    code="SERVICE_SCOPE_REQUIRED",
                    detail="boto3 library is required for Bedrock provider. Run 'pip install boto3'."
                )
        return self._client

    async def chat_turn(
        self,
        message: str,
        history: Optional[List[ChatMessage]] = None,
        tools: Optional[List[dict]] = None,
        system_prompt: Optional[str] = None,
        tool_results: Optional[List[Dict[str, Any]]] = None
    ) -> LLMResponse:
        import asyncio
        client = self._get_client()

        sys_prompt = system_prompt or (
            "You are Lukla Intelligence for apparel manufacturing operations.\n"
            "Your role is to assist operators, supervisors, and owners with real-time factory data.\n"
            "Strictly read-only access. When inquiring about stock or metrics, use tools when available."
        )

        bedrock_messages: List[Dict[str, Any]] = []
        if history:
            for h in history:
                role = "user" if h.sender == "user" else "assistant"
                bedrock_messages.append({"role": role, "content": [{"text": h.text}]})

        # Append tool results if returned from first turn
        if tool_results:
            results_str = "\n".join([
                f"- Tool '{tr.get('tool_name')}': {json.dumps(tr.get('data')) if isinstance(tr.get('data'), (dict, list)) else tr.get('data')}"
                for tr in tool_results
            ])
            user_msg = f"{message}\n\n[Live Factory Data:\n{results_str}\nPlease answer concisely using this data.]"
        else:
            user_msg = message

        bedrock_messages.append({"role": "user", "content": [{"text": user_msg}]})

        converse_kwargs: Dict[str, Any] = {
            "modelId": self.model_id,
            "messages": bedrock_messages,
            "system": [{"text": sys_prompt}],
            "inferenceConfig": {
                "temperature": self.settings.temperature,
                "maxTokens": self.settings.max_tokens
            }
        }

        # Include tool specs if tools available and no results yet
        if tools and not tool_results:
            bedrock_tools = []
            for t in tools:
                schema = t.get("parameters", {"type": "object", "properties": {}})
                bedrock_tools.append({
                    "toolSpec": {
                        "name": t["name"],
                        "description": t.get("description", t["name"]),
                        "inputSchema": {
                            "json": schema
                        }
                    }
                })
            converse_kwargs["toolConfig"] = {
                "tools": bedrock_tools,
                "toolChoice": {"auto": {}}
            }

        try:
            response = await asyncio.to_thread(
                client.converse,
                **converse_kwargs
            )
        except Exception as exc:
            from ..schemas.problem import ProblemException
            err_str = str(exc)
            if "AccessDenied" in err_str:
                raise ProblemException(
                    status=403,
                    code="FORBIDDEN",
                    detail=f"Bedrock AccessDenied: verify EC2 IAM Role permissions in region {self.region_name} for model {self.model_id}. ({err_str})"
                )
            if "ResourceNotFoundException" in err_str or "ValidationException" in err_str:
                raise ProblemException(
                    status=400,
                    code="VALIDATION_ERROR",
                    detail=f"Bedrock model error ({self.model_id} in {self.region_name}): {err_str}"
                )
            raise ProblemException(
                status=502,
                code="BAD_GATEWAY",
                detail=f"Bedrock Runtime error: {err_str}"
            )

        output = response.get("output", {})
        msg = output.get("message", {})
        content_items = msg.get("content", [])

        reply_texts = []
        tool_calls: List[ToolCallRequest] = []

        for item in content_items:
            if "text" in item:
                reply_texts.append(item["text"])
            if "toolUse" in item:
                tu = item["toolUse"]
                tool_calls.append(
                    ToolCallRequest(
                        id=tu.get("toolUseId", "call_bedrock"),
                        tool_name=tu.get("name", ""),
                        arguments=tu.get("input", {})
                    )
                )

        raw_usage = response.get("usage", {})
        usage = TokenUsage(
            prompt_tokens=raw_usage.get("inputTokens", 0),
            completion_tokens=raw_usage.get("outputTokens", 0),
            total_tokens=raw_usage.get("totalTokens", 0)
        )

        return LLMResponse(
            reply="\n".join(reply_texts) if reply_texts else "",
            tool_calls=tool_calls,
            usage=usage
        )

def get_llm_provider(provider_type: Optional[str] = None) -> BaseLLMProvider:
    """Factory creating LLM provider based on configuration."""
    ptype = (provider_type or copilot_settings.COPILOT_DEFAULT_PROVIDER).lower()
    if ptype == "bedrock":
        return BedrockLLMProvider()
    if ptype == "ollama":
        return OllamaLLMProvider()
    if ptype == "openrouter":
        return OpenRouterLLMProvider()
    if ptype in ("openai", "anthropic"):
        return OpenAILLMProvider()
    return MockLLMProvider()
