# feedback_collection.py
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import redis

logger = logging.getLogger(__name__)

class FeedbackPersistenceManager:
    """Manages user feedback collection (thumbs, NPS) and telemetry persistence in Redis."""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, password: Optional[str] = None):
        self.pool = redis.ConnectionPool(
            host=host, 
            port=port, 
            db=db, 
            password=password, 
            max_connections=10
        )
        self.r = redis.Redis(connection_pool=self.pool)
        
    def submit_feedback(self, run_id: str, brand_name: str, score_nps: int, rating_verdict: str, user_comment: str = "") -> bool:
        """
        Submits feedback data to Redis.
        - rating_verdict: 'thumbs_up' or 'thumbs_down'
        - score_nps: Integer from 0 to 10 (Net Promoter Score scale)
        """
        if not (0 <= score_nps <= 10):
            raise ValueError("NPS score must be an integer between 0 and 10.")
            
        payload = {
            "run_id": run_id,
            "brand_name": brand_name,
            "score_nps": score_nps,
            "rating_verdict": rating_verdict,
            "user_comment": user_comment,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Store primary record under a hash map
            self.r.hset(f"geo:feedback:{run_id}", mapping=payload)
            # Add run ID to a tracking index list for analytical queries
            self.r.lpush("geo:feedback:index", run_id)
            return True
        except redis.RedisError as e:
            logger.error(f"Failed to persist feedback in Redis: {e}")
            return False
            
    def get_feedback_metrics(self) -> Dict[str, Any]:
        """
        Calculates aggregations:
        - Net Promoter Score (NPS): (% Promoters (9-10)) - (% Detractors (0-6))
        - Thumbs approval rate: thumbs_up / total count
        """
        try:
            run_ids = self.r.lrange("geo:feedback:index", 0, -1)
            if not run_ids:
                return {"nps": 0.0, "total_feedback": 0, "approval_rate": 0.0}
                
            total = len(run_ids)
            promoters = 0
            detractors = 0
            thumbs_up = 0
            
            for rid in run_ids:
                data = self.r.hgetall(f"geo:feedback:{rid.decode('utf-8')}")
                if not data:
                    continue
                    
                nps_score = int(data.get(b"score_nps", 0))
                verdict = data.get(b"rating_verdict", b"").decode('utf-8')
                
                if nps_score >= 9:
                    promoters += 1
                elif nps_score <= 6:
                    detractors += 1
                    
                if verdict == "thumbs_up":
                    thumbs_up += 1
            
            nps = ((promoters - detractors) / total) * 100
            approval_rate = (thumbs_up / total) * 100
            
            return {
                "nps": round(nps, 2),
                "total_feedback": total,
                "approval_rate": round(approval_rate, 2),
                "promoters_pct": round((promoters / total) * 100, 2),
                "detractors_pct": round((detractors / total) * 100, 2)
            }
        except redis.RedisError as e:
            logger.error(f"Failed to calculate NPS metrics: {e}")
            return {"error": str(e)}
