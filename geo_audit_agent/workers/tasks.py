# tasks.py
import logging
from sqlmodel import Session, select
from geo_audit_agent.workers.celery_app import celery_app
from geo_audit_agent.db.session import engine
from geo_audit_agent.db.models import Audit, Brand, AuditStatus
from geo_audit_agent.agent.graph import audit_graph
from geo_audit_agent.agent.state import AuditState

logger = logging.getLogger(__name__)

@celery_app.task(name="geo_audit_agent.workers.tasks.run_audit_task")
def run_audit_task(audit_id: str, user_id: str):
    """Executes the LangGraph audit graph asynchronously for a queued audit_id."""
    logger.info(f"Asynchronous worker picked up audit task: {audit_id}")
    
    with Session(engine) as session:
        # Retrieve target audit
        audit = session.get(Audit, audit_id)
        if not audit:
            logger.error(f"Audit record {audit_id} not found in database.")
            return False
            
        brand = session.get(Brand, audit.brand_id)
        if not brand:
            logger.error(f"Brand record {audit.brand_id} not found for audit {audit_id}.")
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
            logger.info(f"Invoking LangGraph execution pipeline for {brand.name} ({audit.tier} tier)")
            final_state = audit_graph.invoke(initial_state)
            
            # Retrieve final data from graph state
            audit.confidence_score = final_state.get("confidence_score", 0.0)
            audit.is_cited = final_state.get("is_cited", False)
            audit.gaps = final_state.get("gaps", [])
            audit.remediations = final_state.get("remediation", {})
            audit.status = AuditStatus.COMPLETE
            
            session.add(audit)
            session.commit()
            logger.info(f"Audit {audit_id} completed successfully.")
            return True
            
        except Exception as e:
            logger.error(f"LangGraph execution pipeline crashed for audit {audit_id}: {e}", exc_info=True)
            audit.status = AuditStatus.FAILED
            session.add(audit)
            session.commit()
            return False
