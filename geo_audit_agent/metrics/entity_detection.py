from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class EntityVerdict(str, Enum):
    MATCH = "match"
    NO_MATCH = "no_match"
    UNCERTAIN = "uncertain"


@dataclass(frozen=True)
class EntityMatch:
    verdict: EntityVerdict
    matched_alias: str | None = None
    confidence: float = 0.0


def _contains_phrase(text: str, phrase: str) -> bool:
    tokens = re.findall(r"[\w]+", phrase.casefold())
    if not tokens:
        return False
    pattern = r"(?<!\w)" + r"[\s\-_'.]*".join(map(re.escape, tokens)) + r"(?!\w)"
    return re.search(pattern, text.casefold(), flags=re.UNICODE) is not None


def detect_entity(text: str, brand: str, aliases: list[str] | None = None, domain: str | None = None) -> EntityMatch:
    """Find a brand using token boundaries; never treat substrings as citations."""
    if not text or not brand.strip():
        return EntityMatch(EntityVerdict.NO_MATCH)
    candidates = [brand, *(aliases or [])]
    if domain:
        candidates.append(domain.split("/")[0].removeprefix("www.").split(".")[0])
    for candidate in candidates:
        if candidate.strip() and _contains_phrase(text, candidate):
            return EntityMatch(EntityVerdict.MATCH, candidate, 1.0)

    meaningful = [token for token in re.findall(r"[\w]+", brand.casefold()) if len(token) > 2]
    partial = [token for token in meaningful if _contains_phrase(text, token)]
    if len(meaningful) > 1 and partial:
        return EntityMatch(EntityVerdict.UNCERTAIN, " ".join(partial), len(partial) / len(meaningful))
    return EntityMatch(EntityVerdict.NO_MATCH)
