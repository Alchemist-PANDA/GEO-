import uuid
import json
from typing import Any, Dict
from fastapi import APIRouter, Depends, status
from sqlmodel import Session, select
from geo_audit_agent.db.session import get_session
from geo_audit_agent.db.models import Competitor, CompetitorScore, Brand, CompetitorExplanation, Alert, CompetitorFeedback
from geo_audit_agent.api.schemas import CompetitorAnalysisRequest, RemediationRequest, CompetitorFeedbackRequest
from geo_audit_agent.workers.tasks import run_competitor_analysis
from geo_audit_agent.workers.celery_app import celery_app
from geo_audit_agent.services.llm_router import query_provider

router = APIRouter()

@router.post("/analyze", status_code=status.HTTP_202_ACCEPTED)
async def analyze_competitors(request: CompetitorAnalysisRequest) -> Dict[str, Any]:
    """Start an asynchronous competitor analysis pipeline."""
    task = run_competitor_analysis.delay(
        brand_name=request.brand_name,
        category=request.category,
        city=request.city,
        limit=request.limit
    )
    return {"message": "Competitor analysis started", "task_id": task.id}

@router.get("/status/{task_id}")
async def get_competitor_status(task_id: str) -> Dict[str, Any]:
    """Check the status of a competitor analysis task."""
    task_result = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None
    }

@router.get("/leaderboard/{brand_name}")
async def get_competitor_leaderboard(
    brand_name: str,
    db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Get the current leaderboard for a given brand."""
    # Find the brand
    brand = db.exec(select(Brand).where(Brand.name == brand_name)).first()
    if not brand:
        return {"brand": brand_name, "leaderboard": [], "message": "Brand not found."}
        
    # Get competitors for this brand
    competitors = db.exec(select(Competitor).where(Competitor.brand_id == brand.id)).all()
    if not competitors:
        return {"brand": brand_name, "leaderboard": [], "message": "No competitors analyzed yet."}
        
    leaderboard = []
    for comp in competitors:
        # Get scores
        scores = db.exec(select(CompetitorScore).where(CompetitorScore.competitor_id == comp.id)).all()
        overall = sum(s.score for s in scores if s.dimension != "overall") / (len(scores)-1 if len(scores) > 1 else 1) if scores else 0
        score_dict = {s.dimension: s.score for s in scores}
        
        # Get Explanations
        explanations = db.exec(select(CompetitorExplanation).where(CompetitorExplanation.competitor_id == comp.id)).all()
        expl_dict = {e.explanation_type: e.content for e in explanations}

        leaderboard.append({
            "id": str(comp.id),
            "name": comp.name,
            "overall": round(overall, 1),
            "scores": score_dict,
            "explanations": expl_dict
        })
        
    # Sort by overall score descending
    leaderboard.sort(key=lambda x: x["overall"], reverse=True)
    
    # Assign ranks
    for i, entry in enumerate(leaderboard):
        entry["rank"] = i + 1
        
    return {
        "brand": brand_name,
        "leaderboard": leaderboard
    }

@router.get("/alerts/{user_id}")
async def get_alerts(
    user_id: str,
    db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Fetch unread alerts for a user."""
    # Using raw str for user_id in this MVP
    alerts = db.exec(select(Alert).where(Alert.user_id == user_id, not Alert.is_read).order_by(Alert.created_at.desc())).all()
    return {"alerts": [{"id": str(a.id), "type": a.alert_type, "severity": a.severity, "message": a.message, "created_at": a.created_at} for a in alerts]}

@router.post("/remediate")
async def generate_remediation(req: RemediationRequest) -> Dict[str, Any]:
    """Generate JSON-LD Schema based on competitor strategy."""
    prompt = f"""You are a Technical SEO Engineer. 
A brand named '{req.brand_name}' is trying to outrank its competitor '{req.competitor_name}'.
The competitor's winning strategy is: {req.strategy_text}

Task: Generate a production-ready JSON-LD LocalBusiness or Organization schema block and 3 FAQ items that '{req.brand_name}' can use to counter this strategy.
Output strictly as a JSON object with two keys:
{{
  "json_ld": "<script type='application/ld+json'>...</script>",
  "faqs": [
    {{"q": "...", "a": "..."}}
  ]
}}
Do NOT wrap the output in markdown backticks. Just pure JSON."""
    
    try:
        response = query_provider(prompt, provider="gemini")
        # Try to parse the response, in case it returns markdown we can strip it
        clean_resp = response.strip()
        if clean_resp.startswith("```json"):
            clean_resp = clean_resp[7:-3]
        if clean_resp.startswith("```"):
            clean_resp = clean_resp[3:-3]
            
        data = json.loads(clean_resp.strip())
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "failed", "error": str(e), "raw_response": response}

@router.post("/feedback")
async def submit_competitor_feedback(
    req: CompetitorFeedbackRequest,
    db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Submit user feedback on competitor intelligence."""
    # For MVP, assume a default user UUID if auth is bypassed
    # Let's see if we have a default user profile, else just generate one
    user_id_str = "00000000-0000-0000-0000-000000000000"
    
    try:
        feedback = CompetitorFeedback(
            user_id=uuid.UUID(user_id_str),
            competitor_id=uuid.UUID(req.competitor_id),
            is_helpful=req.is_helpful,
            comment=req.comment
        )
        db.add(feedback)
        db.commit()
        return {"status": "success", "message": "Feedback recorded."}
    except Exception as e:
        db.rollback()
        return {"status": "failed", "error": str(e)}
