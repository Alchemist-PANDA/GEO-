def record(plan_id, action_id, result):
    try:
        from geo_audit_agent.db.session import get_session
        from geo_audit_agent.db.models import ActionExecution
        with get_session() as s:
            s.add(ActionExecution(plan_id=plan_id, action_id=action_id,
                status=result.get("status", "complete"), result=result,
                error_message=result.get("reason")))
            s.commit()
    except Exception:
        pass
