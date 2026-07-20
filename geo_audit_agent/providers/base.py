from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol


class ExecutionMode(str, Enum):
    LIVE = "live"
    FIXTURE = "fixture"
    CACHED = "cached"
    FAILED = "failed"


class ProviderError(RuntimeError):
    """Base class for provider failures that callers must handle explicitly."""


class ProviderUnavailableError(ProviderError):
    """The provider cannot be used because configuration or its SDK is absent."""


class ProviderAuthError(ProviderError):
    """The provider rejected its credential."""


@dataclass(frozen=True)
class ProviderResult:
    provider: str
    model: str
    prompt_id: str
    prompt_version: str
    text: str
    mode: ExecutionMode
    latency_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    cache_hit: bool = False
    metadata: dict[str, str] = field(default_factory=dict)
    recommendation: bool | None = None
    sentiment: str | None = None
    position: int | None = None
    citation_urls: list[str] = field(default_factory=list)
    error_code: str | None = None


class ProviderAdapter(Protocol):
    name: str

    def query(
        self,
        prompt: str,
        *,
        prompt_id: str,
        prompt_version: str,
    ) -> ProviderResult: ...
