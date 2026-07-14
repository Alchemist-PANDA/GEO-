# cost_tracker.py
import logging

logger = logging.getLogger(__name__)

# Fallback budget memory
BUDGET_MEMORY: dict[str, float] = {}

class TokenCostTracker:
    """Tracks token consumption costs and checks execution budget caps per user."""

    def __init__(self, monthly_limit_usd: float = 50.0):
        self.monthly_limit_usd = monthly_limit_usd

    def is_budget_exceeded(self, user_id: str) -> bool:
        """Checks if user has exceeded their monthly budget limit."""
        current_spend = BUDGET_MEMORY.get(user_id, 0.0)
        return current_spend >= self.monthly_limit_usd

    def track_run(self, user_id: str, cost: float) -> float:
        """Adds cost metrics to the user's monthly spending summary."""
        BUDGET_MEMORY[user_id] = BUDGET_MEMORY.get(user_id, 0.0) + cost
        logger.info(f"Tracked ${cost:.6f} for user {user_id}. Monthly total: ${BUDGET_MEMORY[user_id]:.4f}")
        return BUDGET_MEMORY[user_id]
