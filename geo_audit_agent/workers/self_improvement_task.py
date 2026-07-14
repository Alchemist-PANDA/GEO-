"""Celery task that runs the self-improvement loop periodically."""
import logging

from geo_audit_agent.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="geo_audit_agent.workers.self_improvement_task.run_self_improvement")
def run_self_improvement(agent_id: str = "default"):
    logger.info("Self-improvement task started for agent: %s", agent_id)
    try:
        from geo_audit_agent.self_improvement.improvement_proposer import propose
        proposal = propose(agent_id=agent_id)
        if not proposal:
            logger.info("No improvement proposal generated (insufficient data or no pattern found).")
            return {"status": "skipped", "reason": "no_proposal"}

        logger.info("Improvement proposal generated: %s", proposal.get("description", ""))
        logger.info("Proposal ready for shadow testing (manual review required): %s", proposal.get("id"))
        return {"status": "proposed", "proposal_id": proposal.get("id"), "proposal": proposal}
    except ImportError as e:
        logger.warning("Self-improvement dependencies not available: %s", e)
        return {"status": "skipped", "reason": str(e)}
    except Exception as e:
        logger.error("Self-improvement task failed: %s", e, exc_info=True)
        return {"status": "error", "reason": str(e)}
