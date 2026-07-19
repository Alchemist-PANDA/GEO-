# cost_tracker.py
import logging
import threading

logger = logging.getLogger(__name__)

# Fallback budget memory
BUDGET_MEMORY: dict[str, float] = {}
_BUDGET_LOCK = threading.Lock()

class TokenCostTracker:
    """Tracks token consumption costs and checks execution budget caps per user."""

    def __init__(self, monthly_limit_usd: float = 50.0):
        self.monthly_limit_usd = monthly_limit_usd

    def is_budget_exceeded(self, user_id: str) -> bool:
        """Checks if user has exceeded their monthly budget limit."""
        with _BUDGET_LOCK:
            current_spend = BUDGET_MEMORY.get(user_id, 0.0)
            return current_spend >= self.monthly_limit_usd

    def track_run(self, user_id: str, cost: float) -> float:
        """Adds cost metrics to the user's monthly spending summary."""
        if cost < 0:
            raise ValueError("Cost cannot be negative")
        with _BUDGET_LOCK:
            BUDGET_MEMORY[user_id] = BUDGET_MEMORY.get(user_id, 0.0) + cost
            total = BUDGET_MEMORY[user_id]
        logger.info("Tracked $%.6f for user %s. Monthly total: $%.4f", cost, user_id, total)
        return total
