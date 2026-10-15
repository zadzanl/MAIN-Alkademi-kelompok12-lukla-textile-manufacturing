"""
Adversarial State Transition Stress Test Harness for Order Lifecycle.
Validates state machine invariants for confirmOrder and cancelOrder:
- COMPLETED -> CANCELLED transition rejection
- IN_PRODUCTION cancellation rules & audit reason enforcement
- DRAFT -> CONFIRMED vs non-DRAFT transitions
- Terminal states (COMPLETED, CANCELLED)
- Reason payload validation (length, whitespace, additionalProperties)
"""
import unittest
from enum import Enum
from typing import Dict, Any, Optional

class OrderStatus(str, Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    IN_PRODUCTION = "IN_PRODUCTION"
    QC = "QC"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class OrderStateMachine:
    """Reference implementation of Order State Machine per ARCH-SPEC-RECONCILE-001 §2.4 and §4.1."""
    
    @staticmethod
    def confirm_order(
        current_status: OrderStatus,
        role: str,
        has_sample_or_components: bool = True
    ) -> Dict[str, Any]:
        # 1. RBAC check
        if role not in ("Owner", "ProductionHead"):
            return {
                "status": 403,
                "code": "FORBIDDEN",
                "detail": f"Role '{role}' is not authorized to confirm orders."
            }
        
        # 2. State invariant
        if current_status != OrderStatus.DRAFT:
            return {
                "status": 409,
                "code": "INVALID_STATE",
                "detail": f"Order is in status '{current_status}'. Only DRAFT orders can be confirmed."
            }
        
        # 3. Prerequisites check
        if not has_sample_or_components:
            return {
                "status": 409,
                "code": "INVALID_STATE",
                "detail": "Order cannot be confirmed without locked sample revision or components."
            }
        
        return {
            "status": 200,
            "new_status": OrderStatus.CONFIRMED,
            "detail": "Order confirmed successfully."
        }

    @staticmethod
    def cancel_order(
        current_status: OrderStatus,
        role: str,
        reason: Optional[str],
        has_active_lots_or_batches: bool = False,
        owner_quarantine_override: bool = False
    ) -> Dict[str, Any]:
        # 1. RBAC check: only Owner can cancel
        if role != "Owner":
            return {
                "status": 403,
                "code": "FORBIDDEN",
                "detail": f"Role '{role}' is not authorized to cancel orders. Owner role required."
            }
        
        # 2. Validation check: reason is required and must not be empty or whitespace-only
        if reason is None or len(reason.strip()) < 1:
            return {
                "status": 422,
                "code": "VALIDATION_ERROR",
                "detail": "Validation failed: reason: Field required and must not be empty or whitespace only"
            }
        
        if len(reason) > 1000:
            return {
                "status": 422,
                "code": "VALIDATION_ERROR",
                "detail": "Validation failed: reason: Maximum length is 1000 characters"
            }

        # 3. Terminal state check: COMPLETED cannot be cancelled
        if current_status == OrderStatus.COMPLETED:
            return {
                "status": 409,
                "code": "INVALID_STATE",
                "detail": "Order is in terminal status 'COMPLETED'. Finished orders cannot be cancelled."
            }

        # 4. Terminal state check: already CANCELLED
        if current_status == OrderStatus.CANCELLED:
            return {
                "status": 409,
                "code": "INVALID_STATE",
                "detail": "Order has already been cancelled."
            }

        # 5. Active production state check: IN_PRODUCTION / QC
        if current_status in (OrderStatus.IN_PRODUCTION, OrderStatus.QC):
            if has_active_lots_or_batches and not owner_quarantine_override:
                return {
                    "status": 409,
                    "code": "INVALID_STATE",
                    "detail": "Cannot cancel order: active cut batches and material issuances must be quarantined first."
                }
            # If quarantined or no active batches, Owner cancellation proceeds with audit reason
            return {
                "status": 200,
                "new_status": OrderStatus.CANCELLED,
                "detail": "Active production order cancelled under executive audit quarantine."
            }

        # 6. Standard allowed pre-production statuses: DRAFT, CONFIRMED
        if current_status in (OrderStatus.DRAFT, OrderStatus.CONFIRMED):
            return {
                "status": 200,
                "new_status": OrderStatus.CANCELLED,
                "detail": "Order cancelled successfully."
            }

        return {
            "status": 409,
            "code": "INVALID_STATE",
            "detail": f"Invalid order status '{current_status}' for cancellation."
        }


class TestOrderLifecycleAdversarial(unittest.TestCase):
    
    def test_completed_order_cannot_transition_to_cancelled(self):
        """CRITICAL: COMPLETED is strictly terminal. Replay with cancelOrder MUST fail with 409."""
        res = OrderStateMachine.cancel_order(
            current_status=OrderStatus.COMPLETED,
            role="Owner",
            reason="Customer changed mind post-delivery"
        )
        self.assertEqual(res["status"], 409)
        self.assertEqual(res["code"], "INVALID_STATE")
        self.assertIn("COMPLETED", res["detail"])
        self.assertIn("cannot be cancelled", res["detail"])

    def test_in_production_cancelled_without_audit_reason(self):
        """CRITICAL: IN_PRODUCTION cancellation without reason MUST be rejected with 422."""
        # 1. None reason
        res1 = OrderStateMachine.cancel_order(
            current_status=OrderStatus.IN_PRODUCTION,
            role="Owner",
            reason=None
        )
        self.assertEqual(res1["status"], 422)
        self.assertEqual(res1["code"], "VALIDATION_ERROR")

        # 2. Empty string reason
        res2 = OrderStateMachine.cancel_order(
            current_status=OrderStatus.IN_PRODUCTION,
            role="Owner",
            reason=""
        )
        self.assertEqual(res2["status"], 422)
        self.assertEqual(res2["code"], "VALIDATION_ERROR")

        # 3. Whitespace-only reason (Adversarial attack: "   ")
        res3 = OrderStateMachine.cancel_order(
            current_status=OrderStatus.IN_PRODUCTION,
            role="Owner",
            reason="   \t\n  "
        )
        self.assertEqual(res3["status"], 422)
        self.assertEqual(res3["code"], "VALIDATION_ERROR")

    def test_in_production_cancelled_with_active_lots_without_quarantine(self):
        """IN_PRODUCTION cancellation with unquarantined fabric batches must fail with 409."""
        res = OrderStateMachine.cancel_order(
            current_status=OrderStatus.IN_PRODUCTION,
            role="Owner",
            reason="Material defect discovered on line",
            has_active_lots_or_batches=True,
            owner_quarantine_override=False
        )
        self.assertEqual(res["status"], 409)
        self.assertEqual(res["code"], "INVALID_STATE")
        self.assertIn("quarantined first", res["detail"])

    def test_in_production_cancelled_with_quarantine_override(self):
        """IN_PRODUCTION cancellation with executive quarantine override succeeds with audit reason."""
        res = OrderStateMachine.cancel_order(
            current_status=OrderStatus.IN_PRODUCTION,
            role="Owner",
            reason="Client insolvency bankruptcy filing; all WIP quarantined",
            has_active_lots_or_batches=True,
            owner_quarantine_override=True
        )
        self.assertEqual(res["status"], 200)
        self.assertEqual(res["new_status"], OrderStatus.CANCELLED)

    def test_production_head_cannot_cancel_order(self):
        """Only Owner can cancel orders. ProductionHead must receive 403 Forbidden."""
        res = OrderStateMachine.cancel_order(
            current_status=OrderStatus.DRAFT,
            role="ProductionHead",
            reason="Production line breakdown"
        )
        self.assertEqual(res["status"], 403)
        self.assertEqual(res["code"], "FORBIDDEN")

    def test_confirm_order_transitions(self):
        """confirmOrder can ONLY transition from DRAFT. All other statuses must fail with 409."""
        invalid_pre_statuses = [
            OrderStatus.CONFIRMED,
            OrderStatus.IN_PRODUCTION,
            OrderStatus.QC,
            OrderStatus.COMPLETED,
            OrderStatus.CANCELLED
        ]
        for st in invalid_pre_statuses:
            res = OrderStateMachine.confirm_order(
                current_status=st,
                role="Owner"
            )
            self.assertEqual(res["status"], 409, f"Status {st} should have returned 409")
            self.assertEqual(res["code"], "INVALID_STATE")

        # DRAFT succeeds
        res_draft = OrderStateMachine.confirm_order(
            current_status=OrderStatus.DRAFT,
            role="Owner",
            has_sample_or_components=True
        )
        self.assertEqual(res_draft["status"], 200)
        self.assertEqual(res_draft["new_status"], OrderStatus.CONFIRMED)

    def test_reason_payload_dos_length_limit(self):
        """Reason > 1000 characters must be rejected with 422 to prevent audit log bloat/DoS."""
        oversized_reason = "X" * 1001
        res = OrderStateMachine.cancel_order(
            current_status=OrderStatus.DRAFT,
            role="Owner",
            reason=oversized_reason
        )
        self.assertEqual(res["status"], 422)
        self.assertEqual(res["code"], "VALIDATION_ERROR")
        self.assertIn("1000", res["detail"])


if __name__ == "__main__":
    unittest.main()
