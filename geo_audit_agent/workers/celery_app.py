# celery_app.py
import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "geo_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["geo_audit_agent.workers.tasks"]
)

# Standard configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

# Celery Beat schedule for recurring scans
celery_app.conf.beat_schedule = {
    "weekly-competitor-scan": {
        "task": "geo_audit_agent.workers.tasks.run_competitor_analysis",
        "schedule": 604800.0,  # 7 days in seconds
        # Provide placeholder args to avoid crash if no kwargs provided
        "args": ["Burger Hub", "fast food", "Islamabad"],
        "kwargs": {"limit": 5},
    },
}
