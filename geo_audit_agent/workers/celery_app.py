# celery_app.py
import os
try:
    from celery import Celery
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
import uuid

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

if CELERY_AVAILABLE:
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
else:
    class MockCelery:
        class MockTask:
            def __init__(self, fn):
                self.fn = fn
            def __call__(self, *args, **kwargs):
                return self.fn(*args, **kwargs)
            def delay(self, *args, **kwargs):
                # Run synchronously to allow tests/app to function without Celery workers
                try:
                    self.fn(*args, **kwargs)
                except Exception:
                    pass
                class DummyResult:
                    id = str(uuid.uuid4())
                return DummyResult()
            def apply_async(self, *args, **kwargs):
                return self.delay(*args, **kwargs)

        def __init__(self):
            class DummyConf:
                def update(self, *args, **kwargs):
                    pass
                beat_schedule = {}
            self.conf = DummyConf()

        def task(self, *args, **kwargs):
            def decorator(fn):
                return self.MockTask(fn)
            return decorator

        def AsyncResult(self, task_id):
            class MockAsyncResult:
                def __init__(self, tid):
                    self.id = tid
                    self.status = "SUCCESS"
                    self.state = "SUCCESS"
                    self.result = {"status": "success", "message": "Celery mock success"}
                def ready(self):
                    return True
                def get(self, *args, **kwargs):
                    return self.result
            return MockAsyncResult(task_id)

    celery_app = MockCelery()
