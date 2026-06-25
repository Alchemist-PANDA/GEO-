# tasks.py
import logging
import asyncio
from datetime import datetime
from sqlmodel import Session, select
from geo_audit_agent.workers.celery_app import celery_app
from geo_audit_agent.db.session import engine
from geo_audit_agent.db.models import Audit, Brand, AuditStatus, Competitor, CompetitorScan, CompetitorScore, CompetitorExplanation, Alert
from geo_audit_agent.agent.graph import audit_graph
from geo_audit_agent.agent.state import AuditState
from geo_audit_agent.agents.unified_competitor_agent import UnifiedCompetitorIntelligenceAgent

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

@celery_app.task(name="geo_audit_agent.workers.tasks.run_competitor_analysis")
def run_competitor_analysis(brand_name: str, category: str, city: str, limit: int = 5):
    """Executes the Unified Competitor Intelligence Agent and persists to DB."""
    logger.info(f"Asynchronous worker picked up competitor analysis task for {brand_name}")
    
    agent = UnifiedCompetitorIntelligenceAgent()
    try:
        # Run async agent in synchronous celery worker
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(agent.run(brand_name, category, city, limit))
        
        if result.get("status") != "success":
            return result
            
        with Session(engine) as session:
            brand = session.exec(select(Brand).where(Brand.name == brand_name)).first()
            if not brand:
                logger.warning(f"Brand {brand_name} not found in DB. Skipping persistence.")
                return result

            competitors = result.get("competitors", [])
            for comp_data in competitors:
                # 1. Upsert Competitor
                comp_name = comp_data.get("name")
                competitor = session.exec(select(Competitor).where(Competitor.name == comp_name, Competitor.brand_id == brand.id)).first()
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
                scores = comp_data.get("scores", {})
                overall_score = 0
                for dim, score_val in scores.items():
                    if dim != "overall":
                        overall_score += score_val
                        session.add(CompetitorScore(
                            competitor_id=competitor.id,
                            scan_id=scan.id,
                            dimension=dim,
                            score=score_val
                        ))
                
                # We could add an overall dimension too if we want
                if scores:
                    overall = overall_score / len(scores)
                    session.add(CompetitorScore(
                        competitor_id=competitor.id,
                        scan_id=scan.id,
                        dimension="overall",
                        score=overall
                    ))

                # 4. Add CompetitorExplanations
                intel = comp_data.get("intelligence", {})
                if intel.get("explanation"):
                    session.add(CompetitorExplanation(
                        competitor_id=competitor.id,
                        scan_id=scan.id,
                        explanation_type="winning_factors",
                        content=intel.get("explanation")
                    ))
                if intel.get("strategy"):
                    session.add(CompetitorExplanation(
                        competitor_id=competitor.id,
                        scan_id=scan.id,
                        explanation_type="strategy",
                        content=intel.get("strategy")
                    ))
                    
            # 5. Add Global Summary as Alert (optional) or store globally. 
            summary = result.get("summary")
            if summary:
                alert = Alert(
                    user_id=brand.user_id,
                    alert_type="scan_summary",
                    severity="info",
                    message=summary[:200] + "..." if len(summary) > 200 else summary
                )
                session.add(alert)
                
            session.commit()

        logger.info(f"Competitor analysis for {brand_name} completed and persisted successfully.")
        return {"status": "success", "message": "Analysis and persistence complete"}
    except Exception as e:
        logger.error(f"Competitor analysis pipeline crashed for {brand_name}: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}
