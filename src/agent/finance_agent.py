from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.agent.refund_state import RefundState


class FinanceAgent:
    def process_payment(self, state: "RefundState") -> Dict[str, Any]:
        """Handles financial ledger clearing and ledger updates."""
        print("[Agent] Finance Agent processing payment transaction...")
        try:
            success = state.call_stripe_api(state.customer_id, state.amount)
            return {"refund_processed": success}
        except Exception as e:
            error_msg = f"FinanceAgent Error: Payment gateway rejected transaction. {str(e)}"
            print(f"[Error] {error_msg}")
            return {
                "refund_processed": False,
                # Fixed: Dot notation
                "error_logs": state.error_logs + [error_msg]
            }