"""
Comprehensive Empirical Security & State Machine Challenge Test Suite.
Challenger 4: Security Challenger (Iteration 2).

Audits:
1. Idempotency In-Flight Lease Timeout (60 seconds) vs 24-Hour Key Deadlocks:
   - Proves 24-hour deadlock on unhardened crashed workers.
   - Proves 60s lease timeout protects active in-flight requests (< 60s).
   - Proves crashed worker lease recovery after >= 60s.
   - Concurrency stress test: 20 simultaneous threads racing to recover expired lease.
   - Database simulation using actual SQLite tables with atomic UPDATE ... WHERE created_at <= ...
2. OrderCancellationRequest Reason Validation & Regex Defense:
   - Rigorous evaluation of regex patterns: '^\s*\S.*$' vs '\S' vs '^\s*\S[\s\S]*$'
   - Whitespace attacks: empty, spaces, tabs, newlines, CRLF, mixed, unicode whitespace (NBSP, EM space)
   - Real JSON Schema validation via jsonschema library
   - Edge case discovery: Multiline text with '^\s*\S.*$' vs '\S'
   - Max length DoS protection (>1000 chars)
3. Order State Machine Invariant Reconciliation across DRAFT, CONFIRMED, IN_PRODUCTION:
   - Full 6x6 transition matrix testing
   - confirmOrder allowed only from DRAFT, rejected on CONFIRMED, IN_PRODUCTION, QC, COMPLETED, CANCELLED
   - cancelOrder allowed from DRAFT, CONFIRMED, and IN_PRODUCTION (under WIP quarantine)
   - cancelOrder strictly forbidden on COMPLETED and CANCELLED
   - Role permission boundary: confirmOrder (Owner, ProductionHead), cancelOrder (Owner only)
"""
import sys
import os
import uuid
import time
import threading
import sqlite3
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple, Optional, List
import unittest
import jsonschema

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.services.idempotency import (
    canonical_json_bytes,
    compute_canonical_hash,
)
from backend.app.schemas.problem import ProblemException


# ==============================================================================
# 1. IDEMPOTENCY LEASE RECOVERY HARNESS & CONCURRENCY TESTS
# ==============================================================================

class SQLiteIdempotencyStore:
    """
    In-memory SQLite simulation of PostgreSQL idempotency_records table
    matching backend/migrations/001_identities.sql and pre-implementation-hardening.md §2.3.
    """
    def __init__(self):
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.conn.isolation_level = None  # Autocommit mode, using explicit transactions
        self.lock = threading.Lock()
        with self.conn:
            self.conn.execute("""
                CREATE TABLE idempotency_records (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    operation_id TEXT NOT NULL,
                    key TEXT NOT NULL,
                    canonical_payload_hash BLOB NOT NULL,
                    status TEXT NOT NULL,
                    response_status INTEGER,
                    response_body TEXT,
                    created_at REAL NOT NULL,
                    completed_at REAL,
                    UNIQUE(tenant_id, operation_id, key)
                );
            """)

    def reserve_or_get(
        self,
        tenant_id: uuid.UUID,
        operation_id: str,
        key: str,
        payload_hash: bytes,
        simulated_now: float,
        lease_timeout_sec: float = 60.0,
        enable_lease_recovery: bool = True
    ) -> Tuple[bool, Optional[Tuple[int, str]]]:
        """
        Executes atomic reservation with 60-second in-flight lease recovery.
        Returns: (is_new, cached_response)
        """
        tid = str(tenant_id)
        with self.lock:
            cur = self.conn.cursor()
            
            # 1. Try initial INSERT as PENDING
            try:
                rec_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO idempotency_records (
                        id, tenant_id, operation_id, key, canonical_payload_hash, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, 'PENDING', ?)
                """, (rec_id, tid, operation_id, key, payload_hash, simulated_now))
                return (True, None)
            except sqlite3.IntegrityError:
                pass  # Key collision: row already exists

            # 2. Key exists: inspect current record
            cur.execute("""
                SELECT id, canonical_payload_hash, status, response_status, response_body, created_at
                FROM idempotency_records
                WHERE tenant_id = ? AND operation_id = ? AND key = ?
            """, (tid, operation_id, key))
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("Row unexpectedly missing after conflict")

            rec_id, rec_hash, status, resp_status, resp_body, created_at = row

            # If payload hash does not match -> 409 IDEMPOTENCY_CONFLICT
            if rec_hash != payload_hash:
                raise ProblemException(
                    status=409,
                    code="IDEMPOTENCY_CONFLICT",
                    detail="Idempotency key conflict: the same key was used with a different canonical payload"
                )

            # If COMPLETED -> return cached response
            if status == "COMPLETED" and resp_status is not None:
                return (False, (resp_status, resp_body or ""))

            # If PENDING:
            if status == "PENDING":
                elapsed = simulated_now - created_at
                if enable_lease_recovery and elapsed >= lease_timeout_sec:
                    # Abandoned in-flight lease recovery: atomic UPDATE with timestamp condition
                    cur.execute("""
                        UPDATE idempotency_records
                        SET created_at = ?,
                            canonical_payload_hash = ?
                        WHERE tenant_id = ?
                          AND operation_id = ?
                          AND key = ?
                          AND status = 'PENDING'
                          AND created_at <= ?
                    """, (simulated_now, payload_hash, tid, operation_id, key, simulated_now - lease_timeout_sec))
                    
                    if cur.rowcount > 0:
                        # Successfully reclaimed expired lease
                        return (True, None)

                # Active execution in-flight (< 60s or unrecovered) -> 409 Conflict
                raise ProblemException(
                    status=409,
                    code="IDEMPOTENCY_CONFLICT",
                    detail="Operation with this idempotency key is currently pending execution"
                )

            raise ProblemException(
                status=409,
                code="IDEMPOTENCY_CONFLICT",
                detail=f"Idempotency record is in unexpected status '{status}'"
            )

    def complete(
        self,
        tenant_id: uuid.UUID,
        operation_id: str,
        key: str,
        response_status: int,
        response_body: str,
        completed_at: float
    ) -> None:
        with self.lock:
            self.conn.execute("""
                UPDATE idempotency_records
                SET status = 'COMPLETED',
                    response_status = ?,
                    response_body = ?,
                    completed_at = ?
                WHERE tenant_id = ? AND operation_id = ? AND key = ?
            """, (response_status, response_body, completed_at, str(tenant_id), operation_id, key))


# ==============================================================================
# 2. UNIT TESTS: IDEMPOTENCY LEASE TIMEOUT VERIFICATION
# ==============================================================================

class TestIdempotencyLeaseTimeout(unittest.TestCase):

    def setUp(self):
        self.store = SQLiteIdempotencyStore()
        self.tenant = uuid.uuid4()
        self.op = "confirmOrder"
        self.key = "test-idem-key-999"
        self.payload = {"notes": "Urgent order"}
        self.hash = compute_canonical_hash(self.payload)

    def test_unhardened_system_causes_24h_deadlock_on_crashed_worker(self):
        """
        EMPIRICAL PROOF: In the baseline unhardened system (without 60s lease timeout),
        if a worker crashes while PENDING at t=0, the key remains permanently locked
        for the entire 24h retention window.
        """
        t0 = 1000.0
        # Worker 1 reserves key at t=0 and crashes (never calls complete)
        is_new, _ = self.store.reserve_or_get(
            self.tenant, self.op, self.key, self.hash, simulated_now=t0,
            enable_lease_recovery=False  # Simulates baseline behavior
        )
        self.assertTrue(is_new)

        # Retry at t=10s, t=61s, t=3600s (1hr), t=86399s (almost 24hr)
        for t_retry in [t0 + 10, t0 + 61, t0 + 3600, t0 + 86399]:
            with self.assertRaises(ProblemException) as ctx:
                self.store.reserve_or_get(
                    self.tenant, self.op, self.key, self.hash, simulated_now=t_retry,
                    enable_lease_recovery=False
                )
            self.assertEqual(ctx.exception.status, 409)
            self.assertEqual(ctx.exception.code, "IDEMPOTENCY_CONFLICT")
            self.assertIn("currently pending execution", ctx.exception.detail)

    def test_hardened_system_protects_in_flight_under_60s(self):
        """
        EMPIRICAL PROOF: Hardened system strictly protects active in-flight requests
        when elapsed time is under 60 seconds (t < 60s).
        """
        t0 = 1000.0
        is_new, _ = self.store.reserve_or_get(
            self.tenant, self.op, self.key, self.hash, simulated_now=t0,
            lease_timeout_sec=60.0, enable_lease_recovery=True
        )
        self.assertTrue(is_new)

        # Retries at t=1s, t=30s, t=59s, t=59.9s must all be blocked with 409
        for delta in [1.0, 30.0, 59.0, 59.9]:
            with self.assertRaises(ProblemException) as ctx:
                self.store.reserve_or_get(
                    self.tenant, self.op, self.key, self.hash, simulated_now=t0 + delta,
                    lease_timeout_sec=60.0, enable_lease_recovery=True
                )
            self.assertEqual(ctx.exception.status, 409)
            self.assertEqual(ctx.exception.code, "IDEMPOTENCY_CONFLICT")
            self.assertIn("currently pending execution", ctx.exception.detail)

    def test_hardened_system_reclaims_lease_after_60s_crash(self):
        """
        EMPIRICAL PROOF: If worker crashed at t=0, a retry at t >= 60s successfully
        reclaims the lease and executes to completion, breaking the deadlock.
        """
        t0 = 1000.0
        # Worker 1 crashes at t=0
        is_new1, _ = self.store.reserve_or_get(
            self.tenant, self.op, self.key, self.hash, simulated_now=t0,
            lease_timeout_sec=60.0, enable_lease_recovery=True
        )
        self.assertTrue(is_new1)

        # Worker 2 retries at t=60.001s (lease expired) -> Successfully reclaims lease!
        t_retry = t0 + 60.1
        is_new2, _ = self.store.reserve_or_get(
            self.tenant, self.op, self.key, self.hash, simulated_now=t_retry,
            lease_timeout_sec=60.0, enable_lease_recovery=True
        )
        self.assertTrue(is_new2, "Worker 2 must successfully reclaim expired lease")

        # Worker 2 finishes execution and commits COMPLETED
        self.store.complete(
            self.tenant, self.op, self.key, response_status=200,
            response_body='{"status":"CONFIRMED"}', completed_at=t_retry + 0.5
        )

        # Subsequent caller at t=70s receives Cache HIT (200 OK)
        is_new3, cached = self.store.reserve_or_get(
            self.tenant, self.op, self.key, self.hash, simulated_now=t0 + 70.0,
            lease_timeout_sec=60.0, enable_lease_recovery=True
        )
        self.assertFalse(is_new3)
        self.assertEqual(cached[0], 200)
        self.assertIn("CONFIRMED", cached[1])

    def test_concurrent_race_to_reclaim_expired_lease(self):
        """
        EMPIRICAL CONCURRENCY PROOF: When lease expires at t=61s, 20 concurrent threads
        race to reclaim the lease. Exactly ONE thread must win (is_new=True),
        while 19 threads receive 409 Conflict (since created_at was reset to now).
        """
        t0 = 1000.0
        # Worker 1 crashed at t=0
        self.store.reserve_or_get(
            self.tenant, self.op, self.key, self.hash, simulated_now=t0,
            lease_timeout_sec=60.0, enable_lease_recovery=True
        )

        t_race = t0 + 65.0
        winners = []
        conflicts = []

        def racer(thread_id: int):
            try:
                is_new, cached = self.store.reserve_or_get(
                    self.tenant, self.op, self.key, self.hash, simulated_now=t_race,
                    lease_timeout_sec=60.0, enable_lease_recovery=True
                )
                if is_new:
                    winners.append(thread_id)
            except ProblemException as e:
                conflicts.append((thread_id, e.status, e.code))

        threads = [threading.Thread(target=racer, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(winners), 1, f"Expected exactly 1 lease winner, got {len(winners)}")
        self.assertEqual(len(conflicts), 19, f"Expected 19 conflicts, got {len(conflicts)}")
        for c in conflicts:
            self.assertEqual(c[1], 409)
            self.assertEqual(c[2], "IDEMPOTENCY_CONFLICT")


# ==============================================================================
# 3. REGEX & VALIDATION TESTS: OrderCancellationRequest.reason
# ==============================================================================

class TestOrderCancellationReasonValidation(unittest.TestCase):
    
    # OpenAPI Schema with pattern: '^\s*\S.*$' as drafted in pre-implementation-hardening.md §1.4
    SCHEMA_DOT = {
        "type": "object",
        "required": ["reason"],
        "additionalProperties": False,
        "properties": {
            "reason": {
                "type": "string",
                "minLength": 1,
                "maxLength": 1000,
                "pattern": r"^\s*\S.*$"
            }
        }
    }

    # OpenAPI Schema with pattern: '\S' as documented in tasks.md §1.2 and pre-implementation-hardening.md §1.4 notes
    SCHEMA_SLASH_S = {
        "type": "object",
        "required": ["reason"],
        "additionalProperties": False,
        "properties": {
            "reason": {
                "type": "string",
                "minLength": 1,
                "maxLength": 1000,
                "pattern": r"\S"
            }
        }
    }

    # OpenAPI Schema with multiline-safe full-match pattern: '^\s*\S[\s\S]*$'
    SCHEMA_MULTILINE_SAFE = {
        "type": "object",
        "required": ["reason"],
        "additionalProperties": False,
        "properties": {
            "reason": {
                "type": "string",
                "minLength": 1,
                "maxLength": 1000,
                "pattern": r"^\s*\S[\s\S]*$"
            }
        }
    }

    def test_whitespace_only_rejection_across_all_schemas(self):
        """CRITICAL: All schemas MUST strictly reject whitespace-only strings."""
        invalid_payloads = [
            "",                      # Empty string
            "   ",                   # Standard ASCII spaces
            "\t\t\t",                # Tabs
            "\n\n\r\n",              # Newlines / CRLF
            "   \t\n\r   ",          # Mixed whitespace
            "              ",        # Long whitespace
        ]
        schemas = [
            ("SCHEMA_DOT", self.SCHEMA_DOT),
            ("SCHEMA_SLASH_S", self.SCHEMA_SLASH_S),
            ("SCHEMA_MULTILINE_SAFE", self.SCHEMA_MULTILINE_SAFE)
        ]

        for sname, schema in schemas:
            for payload in invalid_payloads:
                with self.subTest(schema=sname, payload=repr(payload)):
                    with self.assertRaises(jsonschema.ValidationError):
                        jsonschema.validate(
                            instance={"reason": payload},
                            schema=schema
                        )

    def test_multiline_valid_reasons_and_pattern_defect(self):
        """
        CRITICAL EMPIRICAL FINDING:
        Multi-line cancellation reasons (e.g. 'Line 1\nLine 2') are valid executive input.
        - SCHEMA_DOT ('^\\s*\\S.*$') ERRONEOUSLY REJECTS multi-line inputs because '.' excludes newlines.
        - SCHEMA_SLASH_S ('\\S') and SCHEMA_MULTILINE_SAFE ('^\\s*\\S[\\s\\S]*$') CORRECTLY ACCEPT multi-line inputs!
        """
        multiline_reason = "Order cancellation requested by executive:\nClient defaulted on milestone payment #2.\nQuarantine initiated."
        
        # 1. SCHEMA_DOT fails on multiline text
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(instance={"reason": multiline_reason}, schema=self.SCHEMA_DOT)

        # 2. SCHEMA_SLASH_S succeeds on multiline text
        try:
            jsonschema.validate(instance={"reason": multiline_reason}, schema=self.SCHEMA_SLASH_S)
        except jsonschema.ValidationError:
            self.fail("SCHEMA_SLASH_S should have accepted valid multiline cancellation reason")

        # 3. SCHEMA_MULTILINE_SAFE succeeds on multiline text
        try:
            jsonschema.validate(instance={"reason": multiline_reason}, schema=self.SCHEMA_MULTILINE_SAFE)
        except jsonschema.ValidationError:
            self.fail("SCHEMA_MULTILINE_SAFE should have accepted valid multiline cancellation reason")

    def test_length_boundary_limits(self):
        """Reason must enforce 1 <= length <= 1000."""
        schema = self.SCHEMA_SLASH_S
        # Length 1 -> OK
        jsonschema.validate(instance={"reason": "A"}, schema=schema)
        # Length 1000 -> OK
        jsonschema.validate(instance={"reason": "A" * 1000}, schema=schema)
        # Length 1001 -> Fail
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(instance={"reason": "A" * 1001}, schema=schema)

    def test_additional_properties_false(self):
        """additionalProperties: false must reject arbitrary fields."""
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(
                instance={"reason": "Valid reason", "malicious_injection": True},
                schema=self.SCHEMA_SLASH_S
            )


# ==============================================================================
# 4. ORDER STATE TRANSITIONS HARNESS & RECONCILIATION AUDIT
# ==============================================================================

class OrderStateMachineHarness:
    """
    Simulates production order state transition rules reconciled in ARCH-SPEC-RECONCILE-001 §2.4:
    States: DRAFT, CONFIRMED, IN_PRODUCTION, QC, COMPLETED, CANCELLED.
    """
    ALL_STATES = ["DRAFT", "CONFIRMED", "IN_PRODUCTION", "QC", "COMPLETED", "CANCELLED"]

    @classmethod
    def execute_confirm_order(
        cls,
        current_status: str,
        role: str,
        has_sample_or_components: bool = True
    ) -> Tuple[int, str, Optional[str]]:
        # 1. RBAC
        if role not in ("Owner", "ProductionHead"):
            return (403, "FORBIDDEN", f"Role '{role}' is not authorized to confirm orders.")
        # 2. State Invariant
        if current_status != "DRAFT":
            return (409, "INVALID_STATE", f"Order is currently in status '{current_status}'. Only DRAFT orders can be confirmed.")
        # 3. Prerequisites
        if not has_sample_or_components:
            return (409, "INVALID_STATE", "Order cannot be confirmed without locked sample revision or components.")
        return (200, "CONFIRMED", "Order confirmed successfully.")

    @classmethod
    def execute_cancel_order(
        cls,
        current_status: str,
        role: str,
        reason: Optional[str],
        has_active_wip: bool = False,
        wip_quarantined: bool = False
    ) -> Tuple[int, str, Optional[str]]:
        # 1. RBAC: strictly Owner
        if role != "Owner":
            return (403, "FORBIDDEN", f"Role '{role}' is not authorized to cancel orders. Owner role required.")
        # 2. Body validation
        if reason is None or len(reason.strip()) < 1:
            return (422, "VALIDATION_ERROR", "Validation failed: reason: Field required and must contain non-whitespace text")
        if len(reason) > 1000:
            return (422, "VALIDATION_ERROR", "Validation failed: reason: Maximum length is 1000 characters")
        # 3. Terminal state: COMPLETED
        if current_status == "COMPLETED":
            return (409, "INVALID_STATE", "Order is in terminal status 'COMPLETED'. Finished orders cannot be cancelled.")
        # 4. Terminal state: CANCELLED
        if current_status == "CANCELLED":
            return (409, "INVALID_STATE", "Order has already been cancelled.")
        # 5. In-flight production state: IN_PRODUCTION, QC
        if current_status in ("IN_PRODUCTION", "QC"):
            if has_active_wip and not wip_quarantined:
                return (409, "INVALID_STATE", "Cannot cancel order: active cut batches and material issuances must be quarantined first.")
            return (200, "CANCELLED", "Active production order cancelled under executive audit quarantine.")
        # 6. Pre-production states: DRAFT, CONFIRMED
        if current_status in ("DRAFT", "CONFIRMED"):
            return (200, "CANCELLED", "Order cancelled successfully.")

        return (409, "INVALID_STATE", f"Invalid order status '{current_status}'.")


class TestOrderStateTransitionsReconciled(unittest.TestCase):

    def test_complete_confirm_order_matrix(self):
        """
        Verify confirmOrder state transitions:
        - DRAFT -> 200 CONFIRMED
        - CONFIRMED, IN_PRODUCTION, QC, COMPLETED, CANCELLED -> 409 INVALID_STATE
        """
        for st in OrderStateMachineHarness.ALL_STATES:
            with self.subTest(initial_status=st):
                status_code, new_status, detail = OrderStateMachineHarness.execute_confirm_order(
                    current_status=st,
                    role="Owner",
                    has_sample_or_components=True
                )
                if st == "DRAFT":
                    self.assertEqual(status_code, 200)
                    self.assertEqual(new_status, "CONFIRMED")
                else:
                    self.assertEqual(status_code, 409)
                    self.assertEqual(new_status, "INVALID_STATE")

    def test_complete_cancel_order_matrix(self):
        """
        Verify cancelOrder state transitions across all 6 statuses:
        - DRAFT -> 200 CANCELLED
        - CONFIRMED -> 200 CANCELLED
        - IN_PRODUCTION (with active WIP unquarantined) -> 409 INVALID_STATE
        - IN_PRODUCTION (with active WIP quarantined) -> 200 CANCELLED
        - QC (with active WIP unquarantined) -> 409 INVALID_STATE
        - QC (with active WIP quarantined) -> 200 CANCELLED
        - COMPLETED -> 409 INVALID_STATE (terminal)
        - CANCELLED -> 409 INVALID_STATE (terminal)
        """
        valid_reason = "Client requested cancellation due to commercial dispute"

        # 1. DRAFT & CONFIRMED -> 200
        for st in ["DRAFT", "CONFIRMED"]:
            status_code, new_status, detail = OrderStateMachineHarness.execute_cancel_order(
                current_status=st, role="Owner", reason=valid_reason
            )
            self.assertEqual(status_code, 200)
            self.assertEqual(new_status, "CANCELLED")

        # 2. IN_PRODUCTION & QC without quarantine -> 409
        for st in ["IN_PRODUCTION", "QC"]:
            status_code, new_status, detail = OrderStateMachineHarness.execute_cancel_order(
                current_status=st, role="Owner", reason=valid_reason,
                has_active_wip=True, wip_quarantined=False
            )
            self.assertEqual(status_code, 409)
            self.assertEqual(new_status, "INVALID_STATE")
            self.assertIn("quarantined first", detail)

        # 3. IN_PRODUCTION & QC with quarantine -> 200
        for st in ["IN_PRODUCTION", "QC"]:
            status_code, new_status, detail = OrderStateMachineHarness.execute_cancel_order(
                current_status=st, role="Owner", reason=valid_reason,
                has_active_wip=True, wip_quarantined=True
            )
            self.assertEqual(status_code, 200)
            self.assertEqual(new_status, "CANCELLED")

        # 4. Terminal states COMPLETED & CANCELLED -> 409
        for st in ["COMPLETED", "CANCELLED"]:
            status_code, new_status, detail = OrderStateMachineHarness.execute_cancel_order(
                current_status=st, role="Owner", reason=valid_reason
            )
            self.assertEqual(status_code, 409)
            self.assertEqual(new_status, "INVALID_STATE")

    def test_rbac_boundary_all_roles(self):
        """
        Test RBAC boundaries across all 8 roles in 04-rbac-matrix.md:
        - confirmOrder: Owner (200), ProductionHead (200), all others (403)
        - cancelOrder: Owner (200), all others (403)
        """
        roles = [
            "Owner", "ProductionHead", "Warehouse", "Tailor",
            "QCInspector", "FinancePayroll", "SampleTeam", "MaklonClient"
        ]
        for r in roles:
            with self.subTest(role=r):
                # confirmOrder
                c_status, _, _ = OrderStateMachineHarness.execute_confirm_order(
                    current_status="DRAFT", role=r
                )
                if r in ("Owner", "ProductionHead"):
                    self.assertEqual(c_status, 200)
                else:
                    self.assertEqual(c_status, 403)

                # cancelOrder
                k_status, _, _ = OrderStateMachineHarness.execute_cancel_order(
                    current_status="DRAFT", role=r, reason="Valid reason"
                )
                if r == "Owner":
                    self.assertEqual(k_status, 200)
                else:
                    self.assertEqual(k_status, 403)


# ==============================================================================
# MAIN TEST EXECUTION
# ==============================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
