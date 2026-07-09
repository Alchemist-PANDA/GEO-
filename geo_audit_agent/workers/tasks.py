# tasks.py
import logging
from datetime import datetime

from sqlmodel import Session, select

from geo_audit_agent.agent.graph import audit_graph
from geo_audit_agent.agent.state import AuditState
from geo_audit_agent.agents.unified_competitor_agent import run_competitor_scan
from geo_audit_agent.db.models import (
    Alert,
    Audit,
    AuditStatus,
    Brand,
    Competitor,
    CompetitorExplanation,
    CompetitorScan,
    CompetitorScore,
)
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

@celery_app.task(name="geo_audit_agent.workers.tasks.run_competitor_analysis")
def run_competitor_analysis(brand_name: str, category: str, city: str, limit: int = 5):
    """Executes the Unified Competitor Intelligence Agent and persists to DB."""
    logger.info(f"Asynchronous worker picked up competitor analysis task for {brand_name}")

    try:
        # Get list of existing competitors from DB if available, or scan new ones
        with Session(engine) as session:
            brand = session.exec(select(Brand).where(Brand.name == brand_name)).first()
            existing_names = []
            if brand:
                existing_comps = session.exec(select(Competitor).where(Competitor.brand_id == brand.id)).all()
                existing_names = [c.name for c in existing_comps]

        # Call the synchronous competitor scan
        # We pass existing competitor names to keep them consistent if they exist
        result = run_competitor_scan(
            brand_name=brand_name,
            category=category,
            city=city,
            competitors=existing_names if existing_names else None
        )

        with Session(engine) as session:
            brand = session.exec(select(Brand).where(Brand.name == brand_name)).first()
            if not brand:
                logger.warning(f"Brand {brand_name} not found in DB. Skipping persistence.")
                return result

            competitors = result.get("competitors", [])
            for comp_data in competitors:
                # 1. Upsert Competitor
                scores = comp_data.get("scores", {})
                comp_name = scores.get("competitor")
                if not comp_name:
                    continue

                competitor = session.exec(
                    select(Competitor).where(Competitor.name == comp_name, Competitor.brand_id == brand.id)
                ).first()
                if not competitor:
                    competitor = Competitor(
                        brand_id=brand.id,
                        name=comp_name,
                        website=comp_data.get("website", ""),
                        category=category,
                        city=city
                    )
                    session.add(competitor)
                    session.commit()
                    session.refresh(competitor)

                    # Generate an Alert for new competitor
                    alert = Alert(
                        user_id=brand.user_id,
                        competitor_id=competitor.id,
                        alert_type="new_competitor",
                        severity="info",
                        message=f"New competitor discovered: {comp_name}"
                    )
                    session.add(alert)

                # 2. Create CompetitorScan
                scan = CompetitorScan(
                    competitor_id=competitor.id,
                    scan_type="automated",
                    status="completed",
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow()
                )
                session.add(scan)
                session.commit()
                session.refresh(scan)

                # 3. Add CompetitorScores
                overall_score = 0
                valid_scores_count = 0
                for dim, score_val in scores.items():
                    if dim != "overall" and isinstance(score_val, (int, float)):
                        overall_score += score_val
                        valid_scores_count += 1
                        session.add(CompetitorScore(
                            competitor_id=competitor.id,
                            scan_id=scan.id,
                            dimension=dim,
                            score=score_val
                        ))

                # We could add an overall dimension too if we want
                if valid_scores_count > 0:
                    overall = overall_score / valid_scores_count
                    session.add(CompetitorScore(
                        competitor_id=competitor.id,
                        scan_id=scan.id,
                        dimension="overall",
                        score=overall
                    ))

                # 4. Add CompetitorExplanations
                exps = comp_data.get("explanations", [])
                for exp in exps:
                    area = exp.get("area", "General")
                    insight = exp.get("insight", "")
                    rec = exp.get("recommendation", "")
                    session.add(CompetitorExplanation(
                        competitor_id=competitor.id,
                        scan_id=scan.id,
                        explanation_type=area.lower().replace(" ", "_"),
                        content=f"{insight} Recommendation: {rec}"
                    ))

            # 5. Add Global Summary as Alert (optional) or store globally.
            summary_dict = result.get("summary", {})
            if summary_dict:
                rank = summary_dict.get("brand_rank", 1)
                total = summary_dict.get("total_competitors", 0)
                opp = summary_dict.get("top_opportunity", "Content Depth")
                message = f"Competitor scan complete. Brand rank: {rank}/{total + 1}. Top opportunity: {opp}."
                alert = Alert(
                    user_id=brand.user_id,
                    alert_type="scan_summary",
                    severity="info",
                    message=message
                )
                session.add(alert)

            session.commit()

        logger.info(f"Competitor analysis for {brand_name} completed and persisted successfully.")
        return {"status": "success", "message": "Analysis and persistence complete"}
    except Exception as e:
        logger.error(f"Competitor analysis pipeline crashed for {brand_name}: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}
