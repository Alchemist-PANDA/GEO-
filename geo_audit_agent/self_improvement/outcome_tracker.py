"""Attach delayed success signals to traces."""


def record_trace(agent_id, trace_id, context, decision, outcome=None, score=None):
    try:
        from geo_audit_agent.db.session import get_session
        from geo_audit_agent.db.models import AgentTrace
        with get_session() as s:
            s.add(AgentTrace(agent_id=agent_id, trace_id=trace_id, context=context,
                             decision=decision, outcome=outcome or {}, score=score))
            s.commit()
    except Exception:
        pass


def attach_outcome(trace_id, outcome: dict, score: float):
    try:
        from geo_audit_agent.db.session import get_session
        from geo_audit_agent.db.models import AgentTrace
        with get_session() as s:
            row = s.query(AgentTrace).filter(AgentTrace.trace_id == trace_id).first()
            if row:
                row.outcome = outcome
                row.score = score
                s.add(row)
                s.commit()
    except Exception:
        pass
