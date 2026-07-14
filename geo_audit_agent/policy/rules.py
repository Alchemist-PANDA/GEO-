"""Declarative business rules. condition is a pure predicate over a flat
context dict — no eval(), no string DSL (those are injection risks)."""
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyRule:
    id: str
    name: str
    action: str            # "BLOCK" | "WARN"
    message: str
    condition: Callable[[dict], bool]   # returns True when VIOLATED


RULES: list[PolicyRule] = [
    PolicyRule("POL-001", "Deployment requires successful audit", "BLOCK",
        "Deployment blocked: complete a successful audit first.",
        lambda c: c.get("intent") == "deploy" and c.get("audit_status") != "complete"),
    PolicyRule("POL-002", "Recommendations require evidence", "BLOCK",
        "Recommendation blocked: no supporting evidence provided.",
        lambda c: c.get("intent") == "recommend" and not c.get("evidence")),
    PolicyRule("POL-003", "Competitor comparisons need data", "BLOCK",
        "Comparison blocked: competitor claim lacks supporting data.",
        lambda c: c.get("intent") == "compare" and not c.get("competitor_data")),
    PolicyRule("POL-004", "Confidence score required", "WARN",
        "Recommendation should include a confidence score.",
        lambda c: c.get("intent") == "recommend" and c.get("confidence") is None),
    PolicyRule("POL-005", "No invented visibility scores", "BLOCK",
        "Blocked: visibility score must trace to audit data.",
        lambda c: bool(c.get("score_present")) and not c.get("score_source")),
    PolicyRule("POL-006", "Brand must exist", "BLOCK",
        "Blocked: unknown brand.",
        lambda c: c.get("intent") in {"audit", "deploy"} and not c.get("brand_known")),
    PolicyRule("POL-007", "Deployment requires human approval", "BLOCK",
        "Blocked: production change needs human approval.",
        lambda c: c.get("intent") == "deploy" and not c.get("human_approved")),
    PolicyRule("POL-008", "Evaluation before deployment", "BLOCK",
        "Blocked: response failed inspector/eval gate.",
        lambda c: c.get("intent") == "deploy" and c.get("inspector_passed") is False),
]
