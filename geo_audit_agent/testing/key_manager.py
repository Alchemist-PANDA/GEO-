import logging
import os

logger = logging.getLogger(__name__)



class GeminiKeyManager:
    def __init__(self):
        self.keys = self._load_keys()
        self.current_index = 0
        self.key_usage = {key: 0 for key in self.keys}
        self.failed_keys = set()

    def _load_keys(self) -> list[str]:
        keys = []
        for i in range(1, 8):
            key = os.getenv(f"GOOGLE_API_KEY_{i}")
            if key:
                keys.append(key)

        if not keys:
            raise ValueError(
                "No Gemini API keys found. Please configure environment variables "
                "GOOGLE_API_KEY_1 to GOOGLE_API_KEY_7 in your .env file."
            )

        logger.info(f"Loaded {len(keys)} Gemini keys from environment variables.")
        return keys

    def get_next_key(self) -> str:
        """Return the next available key (round‑robin)."""
        available = [k for k in self.keys if k not in self.failed_keys]
        if not available:
            # If all are marked failed, reset them to avoid blocking entirely
            logger.warning("All keys marked as failed. Resetting failed keys pool.")
            self.failed_keys.clear()
            available = list(self.keys)

        key = available[self.current_index % len(available)]
        self.current_index += 1
        self.key_usage[key] += 1
        return key

    def mark_failed(self, key: str):
        self.failed_keys.add(key)
        logger.warning(f"Key {key[:10]}... marked as failed/rate-limited.")

    def get_key_name(self, key: str) -> str:
        """Helper to return an identifier for logs without printing the full secret."""
        try:
            idx = self.keys.index(key)
            return f"KEY_{idx + 1}"
        except ValueError:
            return "UNKNOWN_KEY"

    def reset_usage(self):
        """Reset usage counters."""
        self.key_usage = {key: 0 for key in self.keys}
        self.failed_keys = set()
