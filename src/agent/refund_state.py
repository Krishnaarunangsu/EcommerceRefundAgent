from typing import TypedDict


class RefundState(TypedDict):
    """Tracks Global State across all interacting agents."""
    order_id: str
    customer_id: str
    item_id: str
    amount: float
    days_since_purchase: int

    # Agent outputs and  tracking flags
    policy_approved: bool
    policy_reason: str
    inventory_updated: bool

    # Error Logging
    error_logs: list[str]

    # ==========================================
    # 2. MOCK TOOLS & BUSINESS LOGIC
    # ==========================================
    def check_policy(days: int) -> tuple[bool, str]:
        if days <= 30:
            return True, "Within the30-day return window"
        return False, f"Return rejeced. Purchase was {days} days ago(limit is 30)"