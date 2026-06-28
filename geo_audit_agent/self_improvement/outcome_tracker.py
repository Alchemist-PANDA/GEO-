"""Attach delayed success signals to traces. The most valuable signal:
did a deployed fix raise citations/visibility within N weeks?"""
from datetime import datetime, timedelta
from geo_audit_agent.db.session import get_session
from geo_audit_agent.db.models import AgentTrace

def record_trace(agent_id, trace_id, context, decision, outcome=None, score=None):
    with get_session() as s:
        s.add(AgentTrace(agent_id=agent_id, trace_id=trace_id, context=context,
                         decision=decision, outcome=outcome or {}, score=score))
        s.commit()

def attach_outcome(trace_id, outcome: dict, score: float):
    with get_session() as s:
        row = s.query(AgentTrace).filter(AgentTrace.trace_id == trace_id).first()
        if row:
            row.outcome = outcome; row.score = score; s.add(row); s.commit()
