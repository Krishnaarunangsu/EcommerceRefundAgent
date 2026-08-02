import os
from typing import Dict, Any, Literal
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END

from src.agent.policy_agent import PolicyAgent
from src.agent.inventory_agent import InventoryAgent
from src.agent.finance_agent import FinanceAgent


class RefundState(BaseModel):
    order_id: str
    customer_id: str
    item_id: str
    amount: float
    days_since_purchase: int

    # Flags with default values
    policy_approved: bool = False
    policy_reason: str = ""
    inventory_updated: bool = False
    refund_processed: bool = False
    error_logs: list[str] = Field(default_factory=list)

    # Simplified method signature
    def check_policy_rules(self, days: int) -> tuple[bool, str]:
        if days <= 30:
            return True, "Within the valid 30-day return window."
        return False, f"Return rejected. Purchase was {self.days_since_purchase} days ago (limit is 30)."

    def call_warehouse_api(self, item_id: str) -> bool:
        print(f"[API] Warehouse DB updated: Item {item_id} marked as 'restocking'.")
        return True

    def call_stripe_api(self, customer_id: str, amount: float) -> bool:
        if amount <= 0:
            raise ValueError("Refund amount must be greater than zero.")
        print(f"[API] Stripe processed refund of ${amount} for Customer {customer_id}.")
        return True


# ==========================================
# 3. LANGGRAPH WORKFLOW SETUP
# ==========================================
policy_agent = PolicyAgent()
inventory_agent = InventoryAgent()
finance_agent = FinanceAgent()

workflow = StateGraph(RefundState)

workflow.add_node("PolicyAgent", policy_agent.evaluate_policy)
workflow.add_node("InventoryAgent", inventory_agent.update_inventory)
workflow.add_node("FinanceAgent", finance_agent.process_payment)


# ==========================================
# 4. CONDITIONAL ORCHESTRATION ROUTER
# ==========================================
def router_node(state: RefundState) -> Literal["approved_path", "reject_path"]:
    """Acts as the orchestrator routing the state payload."""
    # Fixed: Replaced state.get("policy_approved") with state.policy_approved
    if state.policy_approved:
        return "approved_path"
    return "reject_path"


workflow.set_entry_point("PolicyAgent")

workflow.add_conditional_edges(
    "PolicyAgent",
    router_node,
    {
        "approved_path": "InventoryAgent",
        "reject_path": END
    }
)

workflow.add_edge("InventoryAgent", "FinanceAgent")
workflow.add_edge("FinanceAgent", END)

app = workflow.compile()


# ==========================================
# 6. EXECUTION RUNS
# ==========================================
if __name__ == "__main__":
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
    print("\nFinal State Result:")
    print(result_a)