def record(plan_id, action_id, result):
    try:
        from geo_audit_agent.observability.metrics import ACTION_EXECUTIONS
        ACTION_EXECUTIONS.labels(action_id=action_id, status=result.get("status", "complete")).inc()
    except Exception:
        pass
    try:
        from geo_audit_agent.db.models import ActionExecution
        from geo_audit_agent.db.session import get_session
        with get_session() as s:
            s.add(ActionExecution(plan_id=plan_id, action_id=action_id,
                status=result.get("status", "complete"), result=result,
                error_message=result.get("reason")))
            s.commit()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Action tracking persist failed: %s", e)
