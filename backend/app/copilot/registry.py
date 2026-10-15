from typing import List, Dict, Any
from .schemas import ToolDefinition

# Curated catalog of strictly read-only endpoints derived from contracts/openapi.yaml
READ_TOOL_CATALOG: List[ToolDefinition] = [
    ToolDefinition(
        name="get_stock_balances",
        description="Query current inventory stock balance across raw materials, WIP bundles, and finished SKUs. Filterable by client or material ID.",
        operation_id="getStock",
        endpoint_path="/stock",
        method="GET",
        allowed_roles=["Owner", "Warehouse", "FinancePayroll", "MaklonClient"],
        parameters={
            "type": "object",
            "properties": {
                "legalOwnerId": {
                    "type": "string",
                    "description": "Optional UUID filter for custodial client stock."
                },
                "status": {
                    "type": "string",
                    "enum": ["AVAILABLE", "RESERVED", "DEPLETED"],
                    "description": "Filter by stock availability status."
                }
            }
        }
    ),
    ToolDefinition(
        name="get_production_progress",
        description="Retrieve real-time floor throughput, line pacing, and 30-minute interval output stats.",
        operation_id="listProductionProgress",
        endpoint_path="/sewing/production-progress",
        method="GET",
        allowed_roles=["Owner", "ProductionHead", "Tailor"],
        parameters={
            "type": "object",
            "properties": {
                "lineId": {
                    "type": "string",
                    "description": "Filter by sewing line UUID."
                },
                "orderId": {
                    "type": "string",
                    "description": "Filter by specific production order UUID."
                }
            }
        }
    ),
    ToolDefinition(
        name="get_order_status",
        description="Check status, milestone completion, and delivery schedules for manufacturing orders.",
        operation_id="listOrders",
        endpoint_path="/orders",
        method="GET",
        allowed_roles=["Owner", "ProductionHead", "FinancePayroll", "MaklonClient"],
        parameters={
            "type": "object",
            "properties": {
                "clientId": {
                    "type": "string",
                    "description": "Client UUID to scope query."
                },
                "status": {
                    "type": "string",
                    "enum": ["DRAFT", "CONFIRMED", "IN_PRODUCTION", "QC", "COMPLETED", "CANCELLED"]
                }
            }
        }
    ),
    ToolDefinition(
        name="get_qc_bonus_pool_status",
        description="Fetch current 3-way QC bonus pool accumulation metrics and distribution preview.",
        operation_id="getBonusPool",
        endpoint_path="/qc/bonus-pool",
        method="GET",
        allowed_roles=["Owner", "ProductionHead", "QCInspector", "FinancePayroll"],
        parameters={
            "type": "object",
            "properties": {
                "periodId": {
                    "type": "string",
                    "description": "Weekly period identifier."
                }
            }
        }
    ),
    ToolDefinition(
        name="get_ledger_entries",
        description="Inspect double-entry journal records, debit/credit balance, and account trail.",
        operation_id="getLedgerEntries",
        endpoint_path="/ledger/entries",
        method="GET",
        allowed_roles=["Owner", "FinancePayroll"],
        parameters={
            "type": "object",
            "properties": {
                "accountCode": {
                    "type": "string",
                    "description": "Chart of accounts code prefix (e.g. 1000, 2000)."
                },
                "limit": {
                    "type": "integer",
                    "default": 20
                }
            }
        }
    ),
    ToolDefinition(
        name="search_operational_documents",
        description="Fenced semantic search across technical specifications, rate cards, and factory SOPs.",
        operation_id="searchOperationalDocuments",
        endpoint_path="/search/operational-documents",
        method="GET",
        allowed_roles=["Owner", "SampleTeam", "Warehouse", "ProductionHead", "Tailor", "QCInspector", "FinancePayroll", "MaklonClient"],
        parameters={
            "type": "object",
            "properties": {
                "q": {
                    "type": "string",
                    "description": "Natural language search query."
                }
            },
            "required": ["q"]
        }
    ),
    ToolDefinition(
        name="get_sample_specs",
        description="Query tech pack specifications, grading sheets, and revision logs.",
        operation_id="getSampleSpecs",
        endpoint_path="/samples/specs",
        method="GET",
        allowed_roles=["Owner", "SampleTeam"],
        parameters={
            "type": "object",
            "properties": {
                "sampleId": {
                    "type": "string",
                    "description": "Sample identifier."
                }
            }
        }
    )
]

def filter_tools_for_roles(roles: List[str]) -> List[dict]:
    """
    Dynamically filters tools based on caller roles in AuthContext.
    Prevents role and tenant privilege escalation before reaching the model.
    Returns list of tool definitions as dictionaries.
    """
    roles_set = set(roles)
    matched = [
        tool for tool in READ_TOOL_CATALOG
        if any(role in roles_set for role in tool.allowed_roles)
    ]
    return [t.model_dump() for t in matched]

def export_tools_to_openai_schema(tools: List[dict]) -> List[Dict[str, Any]]:
    """Format tools for standard OpenAI/Anthropic/Ollama function calling."""
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"]
            }
        }
        for t in tools
    ]
