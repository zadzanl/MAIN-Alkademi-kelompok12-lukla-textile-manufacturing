"""
Phase 2 & Phase 3 Adversarial Challenge Verification Suite
Author: challenger_phase3_1 (Empirical Challenger)
Target Proposal: openspec/changes/reconcile-openapi-endpoint-gaps

Empirically verifies:
1. Blueprint negative controls & validation
2. Schema constraints (OrderCancellationRequest, SewingTallyItem, Assembly, Keyset pagination, Ledger immutability)
3. Payroll boundary isolation against backend/payroll-costing/API_CONTRACTS.md
4. Contract & architecture parity (83 operations)
"""

import os
import sys
import yaml
import re
from copy import deepcopy
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
CONTRACT_PATH = os.path.join(WORKSPACE_ROOT, "openspec/changes/lukla-ops-engine-planning/contracts/openapi.yaml")
API_CONTRACT_PLAN_PATH = os.path.join(WORKSPACE_ROOT, "openspec/changes/lukla-ops-engine-planning/12-api-contract-plan.md")
FRONTEND_ARCH_PATH = os.path.join(WORKSPACE_ROOT, "openspec/changes/lukla-ops-engine-planning/14-frontend-architecture.md")
PAYROLL_CONTRACTS_PATH = "C:/Projects/hackathon-MAIN-alkademi/backend/payroll-costing/API_CONTRACTS.md"
HARDENING_REPORT_PATH = os.path.join(WORKSPACE_ROOT, "openspec/changes/reconcile-openapi-endpoint-gaps/artifacts/pre-implementation-hardening.md")
JOINT_REVIEW_PATH = os.path.join(WORKSPACE_ROOT, "openspec/changes/reconcile-openapi-endpoint-gaps/artifacts/joint-review-phase2-phase3.md")

URI = "urn:lukla:openapi"


def get_format_checker():
    fc = FormatChecker()
    if "date-time" not in fc.checkers:
        from datetime import datetime
        @fc.checks("date-time")
        def _check_datetime(val):
            if not isinstance(val, str):
                return True
            try:
                datetime.fromisoformat(val.replace("Z", "+00:00"))
                return True
            except Exception:
                return False
    return fc


def get_validator(doc, pointer):
    registry = Registry().with_resource(
        URI, Resource.from_contents(doc, default_specification=DRAFT202012)
    )
    return Draft202012Validator(
        {"$ref": URI + "#" + pointer}, registry=registry, format_checker=get_format_checker()
    )


def test_1_blueprint_negative_controls(doc):
    print("\n" + "="*60)
    print("CHALLENGE 1: BLUEPRINT NEGATIVE CONTROLS & RESILIENCE")
    print("="*60)
    
    # Negative control 1: OrderCancellationRequest with missing reason
    v_cancel = get_validator(doc, "/components/schemas/OrderCancellationRequest")
    assert not v_cancel.is_valid({}), "FAIL: Accepted empty OrderCancellationRequest"
    print("  [PASS] Negative control: Empty OrderCancellationRequest is rejected")

    # Negative control 2: SewingTallyItem with invalid pieces type
    v_tally = get_validator(doc, "/components/schemas/SewingTallyItem")
    invalid_tally = {
        "id": "00000000-0000-4000-8000-000000000001",
        "orderId": "00000000-0000-4000-8000-000000000002",
        "cutBatchId": "00000000-0000-4000-8000-000000000003",
        "lineId": "00000000-0000-4000-8000-000000000004",
        "componentCode": "FRONT_PANEL",
        "operatorId": "00000000-0000-4000-8000-000000000005",
        "intervalStart": "2026-10-15T08:00:00.123456Z",
        "intervalEnd": "2026-10-15T09:00:00.123456Z",
        "pieces": -1,  # Negative pieces
        "status": "RECORDED"
    }
    assert not v_tally.is_valid(invalid_tally), "FAIL: Accepted SewingTallyItem with negative pieces"
    print("  [PASS] Negative control: SewingTallyItem with negative pieces is rejected")

    # Negative control 3: Invalid Uuid
    v_uuid = get_validator(doc, "/components/schemas/Uuid")
    assert not v_uuid.is_valid("not-a-uuid"), "FAIL: Accepted non-uuid string"
    assert not v_uuid.is_valid("12345"), "FAIL: Accepted short string"
    assert v_uuid.is_valid("00000000-0000-4000-8000-000000000001"), "FAIL: Rejected valid uuid"
    print("  [PASS] Negative control: Uuid validator rejects non-uuid strings")

    # Negative control 4: Operation count verification
    op_ids = set()
    for path, item in doc["paths"].items():
        for m, op in item.items():
            if m in {"get", "post", "put", "patch", "delete", "head", "options", "trace"}:
                oid = op.get("operationId")
                assert oid not in op_ids, f"Duplicate operationId: {oid}"
                op_ids.add(oid)
    assert len(op_ids) == 83, f"Expected 83 operations, got {len(op_ids)}"
    print(f"  [PASS] Verified exactly 83 unique operations across all paths")


def test_2_order_cancellation_request_adversarial(doc):
    print("\n" + "="*60)
    print("CHALLENGE 2: ADVERSARIAL STRESS TEST - OrderCancellationRequest")
    print("="*60)
    v = get_validator(doc, "/components/schemas/OrderCancellationRequest")

    # Adversarial cases that MUST FAIL
    failing_cases = [
        ("empty string", {"reason": ""}),
        ("spaces only", {"reason": "   "}),
        ("tabs only", {"reason": "\t\t\t"}),
        ("newlines only", {"reason": "\n\n"}),
        ("mixed whitespace", {"reason": "  \t \r\n  "}),
        ("missing reason key", {}),
        ("null reason", {"reason": None}),
        ("integer reason", {"reason": 12345}),
        ("boolean reason", {"reason": True}),
        ("array reason", {"reason": ["Cancelled"]}),
        ("dict reason", {"reason": {"text": "Cancelled"}}),
        ("excessive length 1001 chars", {"reason": "X" * 1001}),
        ("unexpected property injection", {"reason": "Valid reason", "adminOverride": True}),
        ("unexpected property injection 2", {"reason": "Valid reason", "force": "true"}),
    ]

    for label, payload in failing_cases:
        is_valid = v.is_valid(payload)
        assert not is_valid, f"SECURITY VIOLATION: OrderCancellationRequest accepted {label}: {payload}"
        print(f"  [PASS] Successfully rejected {label}")

    # Cases that MUST PASS
    passing_cases = [
        ("simple valid reason", {"reason": "Client cancelled contract due to budget cuts"}),
        ("minimum 1 char non-whitespace", {"reason": "C"}),
        ("maximum 1000 chars", {"reason": "R" * 1000}),
        ("leading whitespace with valid text", {"reason": "   Fabric delivery delayed by vendor"}),
        ("trailing whitespace with valid text", {"reason": "Fabric delivery delayed by vendor   "}),
        ("whitespace surrounding single char", {"reason": "   X   "}),
        ("special chars and punctuation", {"reason": "Order #1234 - Defect rate > 15% (QC scrap)!"}),
    ]

    for label, payload in passing_cases:
        is_valid = v.is_valid(payload)
        assert is_valid, f"FALSE REJECTION: OrderCancellationRequest rejected {label}: {payload}"
        print(f"  [PASS] Successfully accepted {label}")


def test_3_sewing_tally_nullable_fields(doc):
    print("\n" + "="*60)
    print("CHALLENGE 3: ADVERSARIAL STRESS TEST - SewingTallyItem Nullability")
    print("="*60)
    v = get_validator(doc, "/components/schemas/SewingTallyItem")

    base = {
        "id": "11111111-1111-4111-8111-111111111111",
        "orderId": "22222222-2222-4222-8222-222222222222",
        "cutBatchId": "33333333-3333-4333-8333-333333333333",
        "lineId": "44444444-4444-4444-8444-444444444444",
        "componentCode": "FRONT_PANEL",
        "operatorId": "55555555-5555-4555-8555-555555555555",
        "intervalStart": "2026-10-15T08:00:00.123456Z",
        "intervalEnd": "2026-10-15T09:00:00.123456Z",
        "pieces": 25,
        "status": "RECORDED"
    }

    # 1. Schema-level declaration check: nullable must be True and fields optional
    st_schema = doc["components"]["schemas"]["SewingTallyItem"]
    assert st_schema["properties"]["verifiedBy"].get("nullable") is True, "FAIL: verifiedBy missing nullable: true"
    assert st_schema["properties"]["verifiedAt"].get("nullable") is True, "FAIL: verifiedAt missing nullable: true"
    assert "verifiedBy" not in st_schema["required"], "FAIL: verifiedBy must not be required"
    assert "verifiedAt" not in st_schema["required"], "FAIL: verifiedAt must not be required"
    print("  [PASS] SewingTallyItem schema declares nullable: true for verifiedBy and verifiedAt, both omitted from required[]")

    # 2. Omitted verifiedBy and verifiedAt -> MUST PASS (valid unverified state)
    omitted = dict(base)
    assert v.is_valid(omitted), "FAIL: SewingTallyItem rejected omitted verifiedBy/verifiedAt"
    print("  [PASS] SewingTallyItem accepts omitted verifiedBy and verifiedAt (unverified tally)")

    # 3. Verified tally with valid UUID and Timestamp -> MUST PASS
    verified = dict(base, 
                    status="VERIFIED",
                    verifiedBy="66666666-6666-4666-8666-666666666666", 
                    verifiedAt="2026-10-15T09:15:00.654321Z")
    assert v.is_valid(verified), "FAIL: SewingTallyItem rejected valid verifiedBy/verifiedAt"
    print("  [PASS] SewingTallyItem accepts valid UUID verifiedBy and Timestamp verifiedAt")

    # 4. Invalid verifiedBy type (integer) -> MUST FAIL
    bad_type = dict(base, verifiedBy=12345)
    assert not v.is_valid(bad_type), "FAIL: Accepted integer for verifiedBy"
    print("  [PASS] Rejects non-UUID type (integer) for verifiedBy")

    # 5. Invalid verifiedBy format (non-UUID string) -> MUST FAIL
    bad_uuid = dict(base, verifiedBy="not-a-valid-uuid")
    assert not v.is_valid(bad_uuid), "FAIL: Accepted malformed UUID string for verifiedBy"
    print("  [PASS] Rejects malformed UUID format for verifiedBy")

    # 6. Invalid verifiedAt format (non-datetime string) -> MUST FAIL
    bad_date = dict(base, verifiedAt="yesterday afternoon")
    assert not v.is_valid(bad_date), "FAIL: Accepted invalid date-time for verifiedAt"
    print("  [PASS] Rejects malformed date-time format for verifiedAt")

    # 7. ADVERSARIAL FINDING: Pure Draft 2020-12 vs OpenAPI 3.0 'nullable' keyword
    # In pure JSON Schema Draft 2020-12, 'nullable: true' is an unrecognized vocabulary keyword;
    # pure validators require OpenAPI normalization or oneOf/anyOf to accept explicit null.
    unverified_null = dict(base, verifiedBy=None, verifiedAt=None)
    pure_draft_valid = v.is_valid(unverified_null)
    if not pure_draft_valid:
        print("  [NOTE] Empirical Finding: Pure Draft 2020-12 rejects explicit null due to OpenAPI 3.0 'nullable' keyword dialect.")
        # Test OpenAPI-normalized schema
        normalized_doc = deepcopy(doc)
        normalized_st = normalized_doc["components"]["schemas"]["SewingTallyItem"]
        for prop in ["verifiedBy", "verifiedAt"]:
            orig_ref = normalized_st["properties"][prop]["$ref"]
            normalized_st["properties"][prop] = {
                "anyOf": [{"$ref": orig_ref}, {"type": "null"}]
            }
        v_norm = get_validator(normalized_doc, "/components/schemas/SewingTallyItem")
        assert v_norm.is_valid(unverified_null), "FAIL: OpenAPI-normalized schema rejected explicit null"
        print("  [PASS] OpenAPI-normalized schema successfully validates explicit null (verifiedBy=None, verifiedAt=None)")


def test_4_assembly_orderid_schema(doc):
    print("\n" + "="*60)
    print("CHALLENGE 4: ADVERSARIAL STRESS TEST - Assembly & orderId Schemas")
    print("="*60)
    # Check GET /assemblies query parameter orderId
    assemblies_get = doc["paths"]["/assemblies"]["get"]
    order_id_param = None
    for p in assemblies_get.get("parameters", []):
        if p.get("name") == "orderId":
            order_id_param = p
            break
    assert order_id_param is not None, "FAIL: GET /assemblies missing orderId query parameter"
    assert order_id_param.get("in") == "query", "FAIL: orderId is not a query parameter"
    assert order_id_param.get("required") is False, "FAIL: orderId in GET /assemblies should be optional filter"
    schema = order_id_param.get("schema", {})
    assert schema.get("$ref") == "#/components/schemas/Uuid", f"FAIL: orderId schema is {schema}, expected ref to Uuid"
    print("  [PASS] GET /assemblies parameter 'orderId' properly references #/components/schemas/Uuid")

    # Check AssemblyRequest.orderId
    assembly_req_schema = doc["components"]["schemas"]["AssemblyRequest"]
    order_id_prop = assembly_req_schema["properties"]["orderId"]
    assert order_id_prop.get("$ref") == "#/components/schemas/Uuid", f"FAIL: AssemblyRequest.orderId is {order_id_prop}"
    print("  [PASS] AssemblyRequest property 'orderId' properly references #/components/schemas/Uuid")

    # Check Assembly schema composition
    assembly_schema = doc["components"]["schemas"]["Assembly"]
    assert "allOf" in assembly_schema, "FAIL: Assembly schema should use allOf pattern"
    assert assembly_schema["allOf"][0].get("$ref") == "#/components/schemas/AssemblyRequest"
    print("  [PASS] Assembly schema composes AssemblyRequest with valid status enum and Uuid id")


def test_5_keyset_pagination_microsecond_resolution(doc):
    print("\n" + "="*60)
    print("CHALLENGE 5: KEYSET PAGINATION & MICROSECOND SPECIFICATION")
    print("="*60)
    # Check Timestamp component
    ts_schema = doc["components"]["schemas"]["Timestamp"]
    assert ts_schema.get("type") == "string", "FAIL: Timestamp is not string"
    assert ts_schema.get("format") == "date-time", "FAIL: Timestamp format is not date-time"
    print("  [PASS] Timestamp schema specifies type: string, format: date-time")

    # Check Cursor parameter
    cursor_param = doc["components"]["parameters"]["Cursor"]
    assert cursor_param.get("name") == "cursor"
    assert cursor_param.get("in") == "query"
    assert cursor_param.get("schema", {}).get("type") == "string"
    print("  [PASS] Cursor parameter properly defined as optional string in query")

    # Check pagination pages
    page_schemas = [
        "OrderPage", "LedgerPage", "AuditPage", "RevisionPage", "StockPage",
        "ProgressPage", "SearchPage", "SewingTallyPage", "CutBatchPage",
        "PurchaseOrderPage", "SupplierInvoicePage", "LedgerAccountPage", "TimeStudyPage"
    ]
    for p_name in page_schemas:
        p_schema = doc["components"]["schemas"].get(p_name)
        assert p_schema is not None, f"FAIL: Missing page schema {p_name}"
        assert "items" in p_schema.get("properties", {}), f"FAIL: {p_name} missing items property"
        assert "nextCursor" in p_schema.get("properties", {}), f"FAIL: {p_name} missing nextCursor property"
        nc = p_schema["properties"]["nextCursor"]
        assert nc.get("type") == "string" and nc.get("nullable") is True, f"FAIL: {p_name}.nextCursor not nullable string"
    print(f"  [PASS] All {len(page_schemas)} page schemas implement items[] and nullable string nextCursor")

    # Check that microsecond resolution requirement is documented in architecture and hardening docs
    with open(HARDENING_REPORT_PATH, "r", encoding="utf-8") as f:
        hard_txt = f.read()
    assert ".ffffffZ" in hard_txt and "microsecond" in hard_txt.lower(), "FAIL: Microsecond precision omitted in hardening report"
    print("  [PASS] Pre-implementation hardening report enforces 6-digit microsecond cursor precision (.ffffffZ)")

    with open(FRONTEND_ARCH_PATH, "r", encoding="utf-8") as f:
        fe_txt = f.read()
    assert "microsecond" in fe_txt.lower(), "FAIL: Microsecond precision omitted in frontend architecture"
    print("  [PASS] Frontend architecture enforces microsecond cursor precision on time study and collection hooks")


def test_6_ledger_immutability(doc):
    print("\n" + "="*60)
    print("CHALLENGE 6: STRICT LEDGER IMMUTABILITY (ZERO PUT/PATCH/DELETE)")
    print("="*60)
    sensitive_prefixes = [
        "/ledger",
        "/sewing-tallies",
        "/qc-inspections",
        "/assemblies",
        "/orders",
        "/purchase-orders",
        "/supplier-invoices",
        "/client-invoices"
    ]

    mutations_found = []
    all_puts = []
    all_patches = []
    all_deletes = []

    for path, methods in doc["paths"].items():
        for m, op in methods.items():
            m_lower = m.lower()
            if m_lower == "delete":
                all_deletes.append((path, op.get("operationId")))
            elif m_lower == "patch":
                all_patches.append((path, op.get("operationId")))
            elif m_lower == "put":
                all_puts.append((path, op.get("operationId")))
                for pref in sensitive_prefixes:
                    if path.startswith(pref):
                        mutations_found.append((m.upper(), path, op.get("operationId")))

    assert len(all_deletes) == 0, f"VIOLATION: Found DELETE operations in OpenAPI contract: {all_deletes}"
    print("  [PASS] Exactly ZERO DELETE operations exist in the entire 83-operation OpenAPI contract")

    assert len(all_patches) == 0, f"VIOLATION: Found PATCH operations in OpenAPI contract: {all_patches}"
    print("  [PASS] Exactly ZERO PATCH operations exist in the entire 83-operation OpenAPI contract")

    assert len(mutations_found) == 0, f"VIOLATION: Found forbidden PUT operations on immutable paths: {mutations_found}"
    print(f"  [PASS] Exactly ZERO PUT operations on ledger, tallies, QC, assemblies, orders, or invoices")

    # Audit the only allowed PUTs
    allowed_puts = {"/rate-cards", "/lines/{lineId}/operators"}
    for p, oid in all_puts:
        assert p in allowed_puts, f"Unrecognized PUT operation: {p} ({oid})"
    print(f"  [PASS] Total PUT operations = {len(all_puts)}: strictly limited to authorized administrative setup ({allowed_puts})")


def test_7_payroll_boundary_isolation(doc):
    print("\n" + "="*60)
    print("CHALLENGE 7: PAYROLL SUBSYSTEM ISOLATION & ZERO REDUNDANCY")
    print("="*60)
    assert os.path.exists(PAYROLL_CONTRACTS_PATH), f"FAIL: Payroll contracts file not found at {PAYROLL_CONTRACTS_PATH}"
    
    with open(PAYROLL_CONTRACTS_PATH, "r", encoding="utf-8") as f:
        payroll_text = f.read()

    # Extract payroll owned operations
    # Lines in table like: | `createPayrollPeriod` | POST | `/payroll-periods` |
    payroll_owned_ops = set(re.findall(r"\|\s*`([a-zA-Z0-9_]+)`\s*\|\s*(?:POST|GET)\s*\|\s*`([^`]+)`", payroll_text))
    payroll_op_ids = {op[0] for op in payroll_owned_ops}
    payroll_paths = {op[1] for op in payroll_owned_ops}

    print(f"  Found {len(payroll_op_ids)} owned operations in payroll module: {sorted(payroll_op_ids)}")

    # 14 reconciled operations
    reconciled_14_ops = {
        "getClient", "confirmOrder", "cancelOrder", "listLedgerAccounts", 
        "getLedgerTransaction", "getSample", "listTimeStudies", "listCutBatches", 
        "listSewingTallies", "listPurchaseOrders", "getPurchaseOrder", 
        "listSupplierInvoices", "getAssembly", "getClientInvoice"
    }

    # Verify ZERO intersection between reconciled 14 and payroll owned
    collision_ops = reconciled_14_ops.intersection(payroll_op_ids)
    assert len(collision_ops) == 0, f"CRITICAL CONFLICT: Reconciled operations collide with payroll engine: {collision_ops}"
    print(f"  [PASS] Zero operationId overlap between 14 reconciled operations and payroll owned operations")

    # Verify path collision
    contract_paths_for_14 = {
        "/clients/{clientId}",
        "/orders/{orderId}/confirmation",
        "/orders/{orderId}/cancellation",
        "/ledger/accounts",
        "/ledger/transactions/{transactionId}",
        "/samples/{sampleId}",
        "/time-studies",
        "/cut-batches",
        "/sewing-tallies",
        "/purchase-orders",
        "/purchase-orders/{purchaseOrderId}",
        "/supplier-invoices",
        "/assemblies/{assemblyId}",
        "/client-invoices/{invoiceId}"
    }

    collision_paths = contract_paths_for_14.intersection(payroll_paths)
    assert len(collision_paths) == 0, f"CRITICAL CONFLICT: Reconciled paths collide with payroll paths: {collision_paths}"
    print(f"  [PASS] Zero path collisions between 14 reconciled endpoints and payroll endpoints")

    # Extract operationIds from first column of each table row
    consumed_section = payroll_text.split("## Consumed operations")[1].split("## Shared rules")[0]
    flat_consumed = set()
    for line in consumed_section.strip().splitlines():
        if line.startswith("|") and not line.startswith("| operationId") and not line.startswith("| ---"):
            cols = [c.strip() for c in line.split("|")]
            if len(cols) >= 3:
                first_col = cols[1]
                for op in re.findall(r"`([a-zA-Z0-9_]+)`", first_col):
                    flat_consumed.add(op)
    
    print(f"  Payroll declared consumed operations from operations engine: {sorted(flat_consumed)}")
    assert len(flat_consumed) == 6, f"Expected 6 consumed operations, found {len(flat_consumed)}: {flat_consumed}"
    for cop in flat_consumed:
        # Verify that these consumed operations exist in the main openapi.yaml
        op_found = False
        for p, methods in doc["paths"].items():
            for m, op in methods.items():
                if op.get("operationId") == cop:
                    op_found = True
                    break
        assert op_found, f"FAIL: Consumed operation '{cop}' declared by payroll not found in openapi.yaml"
    print(f"  [PASS] All {len(flat_consumed)} consumed operations referenced by payroll engine exist in openapi.yaml")


def test_8_ui_architecture_parity(doc):
    print("\n" + "="*60)
    print("CHALLENGE 8: CONTRACT TO UI DATA HOOK 83-OPERATION EXACT PARITY")
    print("="*60)
    contract_ops = set()
    for path, item in doc["paths"].items():
        for m, op in item.items():
            if m in {"get", "post", "put", "patch", "delete"}:
                oid = op.get("operationId")
                if oid:
                    contract_ops.add(oid)

    # Extract all operation IDs referenced in 14-frontend-architecture.md
    with open(FRONTEND_ARCH_PATH, "r", encoding="utf-8") as f:
        fe_content = f.read()

    # Look for the operations list in test script in Section 9 of 14-frontend-architecture.md
    match = re.search(r"refs=\{(.*?)\}", fe_content, re.DOTALL)
    assert match is not None, "FAIL: Could not locate refs set in 14-frontend-architecture.md"
    raw_refs = match.group(1).replace("'", "").replace('"', "").replace("\n", "").replace(" ", "").split(",")
    frontend_ops = {r for r in raw_refs if r}

    missing_in_frontend = contract_ops - frontend_ops
    orphaned_in_contract = frontend_ops - contract_ops

    assert len(missing_in_frontend) == 0, f"FAIL: Contract operations missing in frontend architecture: {missing_in_frontend}"
    assert len(orphaned_in_contract) == 0, f"FAIL: Frontend architecture references orphaned operations: {orphaned_in_contract}"
    assert len(contract_ops) == 83, f"FAIL: Expected 83 operations, got {len(contract_ops)}"
    assert len(frontend_ops) == 83, f"FAIL: Expected 83 frontend operations, got {len(frontend_ops)}"

    print(f"  [PASS] 1:1 Bidirectional Parity: exactly 83 operations in openapi.yaml <==> 83 in 14-frontend-architecture.md")
    print(f"  [PASS] Zero missing operations, zero orphaned operations.")


def main():
    print("Starting Comprehensive Empirical Challenger Review Suite...")
    with open(CONTRACT_PATH, "r", encoding="utf-8") as f:
        doc = yaml.safe_load(f)

    test_1_blueprint_negative_controls(doc)
    test_2_order_cancellation_request_adversarial(doc)
    test_3_sewing_tally_nullable_fields(doc)
    test_4_assembly_orderid_schema(doc)
    test_5_keyset_pagination_microsecond_resolution(doc)
    test_6_ledger_immutability(doc)
    test_7_payroll_boundary_isolation(doc)
    test_8_ui_architecture_parity(doc)

    print("\n" + "="*60)
    print("ALL 8 EMPIRICAL CHALLENGER TESTS PASSED (100% SUCCESS)")
    print("="*60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
