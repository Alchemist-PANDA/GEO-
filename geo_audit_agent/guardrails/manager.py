"""Routes a phase to its handlers, aggregates violations, persists, decides."""
from __future__ import annotations
import logging
from geo_audit_agent.guardrails.types import GuardrailDecision, Violation, Severity
from geo_audit_agent.guardrails import handlers as H

logger = logging.getLogger(__name__)

_PHASES = {
    "input":          [H.input_guardrail],
    "context":        [H.context_guardrail],
    "retrieval":      [H.retrieval_guardrail],
    "memory":         [H.memory_guardrail],
    "tool":           [H.tool_guardrail],
    "agent":          [H.agent_guardrail],
    "business":       [H.business_guardrail],
    "output":         [H.output_guardrail],
    "security":       [H.security_guardrail],
    "cost":           [H.cost_guardrail],
    "workflow":       [H.workflow_guardrail],
    "human_approval": [H.human_approval_guardrail],
}

_BLOCKING = {Severity.HIGH, Severity.CRITICAL}


def check_phase(phase: str, payload: dict, *, agent_id: str = "system",
                trace_id: str | None = None) -> GuardrailDecision:
    violations: list[Violation] = []
    for handler in _PHASES.get(phase, []):
        try:
            violations.extend(handler(payload))
        except Exception as e:
            logger.error("guardrail %s crashed: %s", handler.__name__, e)
            if phase in ("security", "human_approval", "business"):
                violations.append(Violation(phase, "handler_error",
                    Severity.CRITICAL, f"guardrail crashed: {e}"))
    _persist(violations, phase, agent_id, trace_id)
    allowed = not any(v.severity in _BLOCKING for v in violations)
    try:
        from geo_audit_agent.observability.metrics import GUARDRAIL_EVENTS, GUARDRAIL_BLOCKS
        GUARDRAIL_EVENTS.labels(classification="safe" if allowed else "blocked").inc()
        for v in violations:
            GUARDRAIL_BLOCKS.labels(type=v.guardrail_type, severity=v.severity.value,
                                    blocked=str(v.severity in _BLOCKING)).inc()
    except Exception:
        pass
    return GuardrailDecision(allowed=allowed, violations=violations)


def _persist(violations, phase, agent_id, trace_id):
    if not violations:
        return
    try:
        from geo_audit_agent.db.session import get_session
        from geo_audit_agent.db.models import GuardrailViolation
        with get_session() as s:
            for v in violations:
                blocked = v.severity in _BLOCKING
                s.add(GuardrailViolation(
                    guardrail_type=v.guardrail_type, agent_id=agent_id,
                    trace_id=trace_id, severity=v.severity.value,
                    blocked=blocked, violation_details={"rule": v.rule, "message": v.message, **v.details}))
            s.commit()
    except Exception as e:
        logger.warning("guardrail persist failed (non-fatal): %s", e)
