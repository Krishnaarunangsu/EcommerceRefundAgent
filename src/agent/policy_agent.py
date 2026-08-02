from typing import Dict, Any, TYPE_CHECKING

# Avoid runtime circular import; only import for type checkers/IDEs
if TYPE_CHECKING:
    from src.agent.refund_state import RefundState


class PolicyAgent:
    def evaluate_policy(self, state: "RefundState") -> Dict[str, Any]:
        """

        Args:
            state:

        Returns:

        """
        print("\n[Agent] Policy Agent checking item eligibility...")
        try:
            approved, reason = state.check_policy_rules(state.days_since_purchase)

            return {
                "policy_approved": approved,
                "policy_reason": reason
            }
        except Exception as e:
            # Fixed: Use dot notation state.error_logs instead of state.get()
            return {"error_logs": state.error_logs + [f"PolicyAgent Error: {str(e)}"]}