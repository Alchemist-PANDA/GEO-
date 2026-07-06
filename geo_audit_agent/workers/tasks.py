# tasks.py
import logging

from sqlmodel import Session

from geo_audit_agent.agent.graph import audit_graph
from geo_audit_agent.agent.state import AuditState
from geo_audit_agent.db.models import Audit, AuditStatus, Brand
from geo_audit_agent.db.session import engine
from geo_audit_agent.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(name="geo_audit_agent.workers.tasks.run_audit_task")
def run_audit_task(audit_id: str, user_id: str):
    """Executes the LangGraph audit graph asynchronously for a queued audit_id."""
    logger.info("Asynchronous worker picked up audit task: %s", audit_id)

    with Session(engine) as session:
        # Retrieve target audit
        audit = session.get(Audit, audit_id)
        if not audit:
            logger.error("Audit record %s not found in database.", audit_id)
            return False

        brand = session.get(Brand, audit.brand_id)
        if not brand:
            logger.error("Brand record %s not found for audit %s.", audit.brand_id, audit_id)
            audit.status = AuditStatus.FAILED
            session.add(audit)
            session.commit()
            return False

        # Update status to running
        audit.status = AuditStatus.RUNNING
        session.add(audit)
        session.commit()

        # Prepare initial state for the state graph
        initial_state = AuditState(
            brand_name=brand.name,
            category=brand.category,
            city=brand.city,
            tier=audit.tier,
            audit_id=str(audit.id),
            user_id=user_id,
            correlation_id=f"corr_{audit_id}"
        )

        try:
            logger.info("Invoking LangGraph execution pipeline for %s (%s tier)", brand.name, audit.tier)
            final_state = audit_graph.invoke(initial_state)

            # Retrieve final data from graph state
            audit.confidence_score = final_state.get("confidence_score", 0.0)
            audit.is_cited = final_state.get("is_cited", False)
            audit.gaps = final_state.get("gaps", [])
            audit.remediations = final_state.get("remediation", {})
            audit.status = AuditStatus.COMPLETE

            session.add(audit)
            session.commit()
            logger.info("Audit %s completed successfully.", audit_id)
            return True

        except Exception as e:
            logger.error("LangGraph execution pipeline crashed for audit %s: %s", audit_id, e, exc_info=True)
            audit.status = AuditStatus.FAILED
            session.add(audit)
            session.commit()
            return False
