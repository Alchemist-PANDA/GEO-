"""Attach delayed success signals to traces."""
import logging

logger = logging.getLogger(__name__)


def record_trace(agent_id, trace_id, context, decision, outcome=None, score=None):
    try:
        from geo_audit_agent.db.models import AgentTrace
        from geo_audit_agent.db.session import get_session
        with get_session() as s:
            s.add(AgentTrace(agent_id=agent_id, trace_id=trace_id, context=context,
                             decision=decision, outcome=outcome or {}, score=score))
            s.commit()
    except Exception as e:
        logger.warning("record_trace failed: %s", e)


def attach_outcome(trace_id, outcome: dict, score: float):
    try:
        from sqlmodel import select

        from geo_audit_agent.db.models import AgentTrace
        from geo_audit_agent.db.session import get_session
        with get_session() as s:
            row = s.exec(select(AgentTrace).where(AgentTrace.trace_id == trace_id)).first()
            if row:
                row.outcome = outcome
                row.score = score
                s.add(row)
                s.commit()
    except Exception as e:
        logger.warning("attach_outcome failed: %s", e)
