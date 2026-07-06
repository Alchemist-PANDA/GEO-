"""Cheap, deterministic-first intent routing. Keyword router covers the
common cases for free; LLM fallback only for genuinely ambiguous input."""
import re

from geo_audit_agent.llm import gateway

INTENTS = ["audit", "recommend", "compare", "deploy", "explain_chart",
           "keyword", "visibility", "score", "help", "smalltalk"]

_RULES = [
    ("deploy",        r"\b(deploy|publish|push live|go live|execute)\b"),
    ("compare",       r"\b(vs|versus|compare|competitor|against|rival)\b"),
    ("explain_chart", r"\bexplain (this )?chart\b|what does this (chart|graph)"),
    ("recommend",     r"\b(what should i fix|recommend|action plan|how to fix|remediat)\b"),
    ("keyword",       r"\b(keyword|search term|query monitor)\b"),
    ("visibility",    r"\b(visibility|platform|where am i|where do i show)\b"),
    ("score",         r"\b(score|confidence|how am i doing|geo coverage)\b"),
    ("audit",         r"\b(audit|run an audit|scan my brand)\b"),
    ("help",          r"\b(help|what can you|how does this work)\b"),
]


def classify(message: str) -> str:
    m = (message or "").lower().strip()
    if not m:
        return "smalltalk"
    for intent, pat in _RULES:
        if re.search(pat, m):
            return intent
    res = gateway.claude(
        system="Classify the user's intent into exactly one of: " + ", ".join(INTENTS),
        user=message, model="claude-opus-4-8", max_tokens=20, force_json=True)
    return gateway.parse_json(res.text).get("intent", "help")
