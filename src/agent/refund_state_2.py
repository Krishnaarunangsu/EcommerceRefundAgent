import os
from typing import Dict, Any, Literal
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, END


# ==========================================
# 1. STATE MANAGEMENT DEFINITION
# ==========================================
class RefundState(TypedDict):
    order_id: str
    customer_id: str
    amount: float
    days_since_purchase: int
    policy_approved: bool
    policy_reason: str
    inventory_updated: bool
    refund_processed: bool
    error_logs: list[str]


# ==========================================
# 2. MOCK TOOLS & BUSINESS LOGIC
# ==========================================
def check_policy_rules(days: int) -> tuple[bool, str]:
    if days <= 30:
        return True, "Within the valid 30-day return window."
    return False, f"Return rejected. Purchase was {days} days ago (limit is 30)."


def call_warehouse_api(item_id: str) -> bool:
    # Simulate a successful external inventory system database update
    print(f"[API] Warehouse DB updated: Item {item_id} marked as 'restocking'.")
    return True

def call_stripe_api(customer_id: str, amount: float) -> bool:
    # Simulate an external gateway call. Throws error if invalid amount.
    if amount <= 0:
        raise ValueError("Refund amount must be greater than zero.")
    print(f"[API] Stripe processed refund of ${amount} for Customer {customer_id}.")
    return True


# ==========================================
# 3. MULTI-AGENT NODE DEFINITIONS
# ==========================================
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


class InventoryAgent:
    def update_inventory(self, state: "RefundState") -> Dict[str, Any]:
        """

        Args:
            state:

        Returns:

        """
        """Handles physical warehouse restock logs."""
        print("[Agent] Inventory Agent logging item return...")
        try:
            success = state.call_warehouse_api(state.item_id)
            return {"inventory_updated": success}
        except Exception as e:
            error_msg = f"InventoryAgent Error: Failed to restock. {str(e)}"
            print(f"[Error] {error_msg}")
            return {
                "inventory_updated": False,
                # Fixed: Dot notation
                "error_logs": state.error_logs + [error_msg]
            }


class FinanceAgent:
    def process_payment(self, state: "RefundState") -> Dict[str, Any]:
        """

        Args:
            state:

        Returns:

        """
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


# ==========================================
# 4. CONDITIONAL ORCHESTRATION ROUTER
# ==========================================
def router_node(state: RefundState) -> Literal["approved_path", "reject_path"]:
    """Acts as the orchestrator routing the state payload."""
    if state.get("policy_approved"):
        return "approved_path"
    return "reject_path"

# ==========================================
# 5. GRAPH COMPOSITION & BUILD
# ==========================================
workflow = StateGraph(RefundState)

policy_agent=PolicyAgent()
inventory_agent=InventoryAgent()
finance_agent=FinanceAgent()

# Add processing units
workflow.add_node("PolicyAgent", policy_agent.evaluate_policy)
workflow.add_node("InventoryAgent", inventory_agent.update_inventory)
workflow.add_node("FinanceAgent", finance_agent.process_payment)

# Configure directed pathways
workflow.set_entry_point("PolicyAgent")

# Conditional orchestration routing based on policy validation results
workflow.add_conditional_edges(
    "PolicyAgent",
    router_node,
    {
        "approved_path": "InventoryAgent",
        "reject_path": END
    }
)

# Connect linear execution dependencies
workflow.add_edge("InventoryAgent", "FinanceAgent")
workflow.add_edge("FinanceAgent", END)

# Compile into an executable application
app = workflow.compile()

# ==========================================
# 6. EXECUTION RUNS
# ==========================================
if __name__ == "__main__":
    # Case A: Eligible Order (Within 30 Days)
    valid_order = {
        "order_id": "ORD-9921",
        "customer_id": "CUST-551",
        "item_id": "SKU-4412",
        "amount": 89.99,
        "days_since_purchase": 14,
        "error_logs": []
    }

    print("--- RUNNING VALID TRANSACTION ---")
    result_a = app.invoke(valid_order)
    print(f"\nFinal State Result: Approved={result_a.get('policy_approved')}, "
          f"Refunded={result_a.get('refund_processed')}, Errors={result_a.get('error_logs')}")

    # Case B: Ineligible Order (Over 30 Days)
    invalid_order = {
        "order_id": "ORD-1102",
        "customer_id": "CUST-302",
        "item_id": "SKU-8874",
        "amount": 150.00,
        "days_since_purchase": 45,
        "error_logs": []
    }

    print("\n--- RUNNING OUT-OF-WINDOW TRANSACTION ---")
    result_b = app.invoke(invalid_order)
    print(f"\nFinal State Result: Approved={result_b.get('policy_approved')}, "
          f"Reason='{result_b.get('policy_reason')}'")