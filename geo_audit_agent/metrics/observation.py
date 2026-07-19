"""Deterministic interpretation helpers for provider observations.

These helpers deliberately make conservative claims.  A brand mention is not
automatically a recommendation, and a URL is not automatically a citation for
the target brand.  The live provider response remains the source evidence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .entity_detection import EntityVerdict, detect_entity

URL_PATTERN = re.compile(r"https?://[^\s)>{}\]]+")
NEGATIVE_TERMS = ("not recommend", "avoid", "poor", "complaint", "worst", "unreliable")
POSITIVE_TERMS = (
    "recommend", "recommended", "best", "top", "excellent", "great", "trusted",
    "popular", "highly rated", "well reviewed", "well-reviewed", "leading",
)


@dataclass(frozen=True)
class ObservationInterpretation:
    mentioned: bool
    recommended: bool
    sentiment: str
    position: int | None
    citation_urls: list[str]
    confidence: float


def extract_urls(text: str) -> list[str]:
    """Return normalized URLs while preserving first-seen order."""
    seen: set[str] = set()
    urls: list[str] = []
    for raw in URL_PATTERN.findall(text or ""):
        url = raw.rstrip(".,;:")
        if url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def _listed_position(text: str, brand: str) -> int | None:
    """Find the position of a brand in common numbered/bulleted answer lists."""
    if not text:
        return None
    escaped = re.escape(brand)
    match = re.search(rf"(?im)^\s*(\d+)[.)]\s+.*?{escaped}", text)
    if match:
        return int(match.group(1))
    return None


def interpret_observation(text: str, brand: str, aliases: list[str] | None = None) -> ObservationInterpretation:
    match = detect_entity(text, brand, aliases)
    mentioned = match.verdict is EntityVerdict.MATCH
    if not mentioned:
        return ObservationInterpretation(False, False, "none", None, extract_urls(text), 0.0)

    alias = match.matched_alias or brand
    position = _listed_position(text, alias) or _listed_position(text, brand)
    location = (text.casefold().find(alias.casefold()) if alias else -1)
    context = text[max(0, location - 140): location + len(alias) + 180].casefold()
    negative = any(term in context for term in NEGATIVE_TERMS)
    positive = any(term in context for term in POSITIVE_TERMS)
    sentiment = "negative" if negative else "positive" if positive else "neutral"
    recommended = not negative and (positive or position is not None)
    confidence = 1.0 if position is not None else 0.85 if positive or negative else 0.65
    return ObservationInterpretation(
        mentioned=True,
        recommended=recommended,
        sentiment=sentiment,
        position=position,
        citation_urls=extract_urls(text),
        confidence=confidence,
    )
