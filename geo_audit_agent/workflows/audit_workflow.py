"""
Temporal workflow wrapping the LangGraph audit pipeline.
Addresses: PE-OS Law 10 (Durable Execution Persistence)
Replaces: wait_and_rerun.py time.sleep() pattern

NOTE: this is an optional durable-execution path. ``temporalio`` is not a
core dependency, so the imports are guarded — importing this module without
temporalio installed degrades to no-op decorators instead of crashing an
import sweep. Install ``temporalio`` to actually run the workflow.
"""
from datetime import timedelta

try:
    from temporalio import activity, workflow
    from temporalio.common import RetryPolicy
    HAS_TEMPORAL = True
except ImportError:  # pragma: no cover - optional dependency
    HAS_TEMPORAL = False

    class _NoOpDecorator:
        """Stand-in so @activity.defn / @workflow.defn don't crash on import."""

        def defn(self, *args, **kwargs):
            def wrap(fn):
                return fn
            return wrap(args[0]) if args and callable(args[0]) else wrap

        def run(self, fn):
            return fn

    activity = workflow = _NoOpDecorator()  # type: ignore[assignment]
    RetryPolicy = None  # type: ignore[assignment,misc]


@activity.defn
async def execute_audit_pipeline(audit_id: str, user_id: str) -> dict:
    from geo_audit_agent.agent.graph import audit_graph
    from geo_audit_agent.agent.state import AuditState
    from geo_audit_agent.db.models import Audit, Brand
    from geo_audit_agent.db.session import get_session

    with get_session() as session:
        audit = session.get(Audit, audit_id)
        brand = session.get(Brand, audit.brand_id)

        state = AuditState(
            brand_name=brand.name,
            category=brand.category,
            city=brand.city,
            tier=audit.tier,
            audit_id=str(audit.id),
            user_id=user_id,
            correlation_id=str(audit.id),
        )

        result = await audit_graph.ainvoke(state)
        return result.report


@activity.defn
async def persist_audit_results(audit_id: str, report: dict) -> None:
    from datetime import datetime

    from geo_audit_agent.db.models import Audit, AuditStatus
    from geo_audit_agent.db.session import get_session
    from geo_audit_agent.services.evidence import report_to_evidence

    with get_session() as session:
        audit = session.get(Audit, audit_id)
        audit.status = AuditStatus.COMPLETE
        audit.report = report
        audit.is_cited = report.get("is_cited", False)
        audit.confidence_score = report.get("confidence_score", 0.0)
        audit.gaps = {"gaps": report.get("gaps", [])}
        audit.remediations = report.get("remediation", {})
        audit.completed_at = datetime.utcnow()
        session.add(audit)
        session.add(report_to_evidence(report, audit_id=audit.id))
        session.commit()


@workflow.defn
class AuditWorkflow:
    @workflow.run
    async def run(self, audit_id: str, user_id: str, tier: str = "balanced") -> dict:
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=30),
            maximum_attempts=3,
        )

        report = await workflow.execute_activity(
            execute_audit_pipeline,
            args=[audit_id, user_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy,
        )

        await workflow.execute_activity(
            persist_audit_results,
            args=[audit_id, report],
            start_to_close_timeout=timedelta(seconds=30),
        )

        if tier == "deep":
            await workflow.sleep(timedelta(hours=48))

            recheck_report = await workflow.execute_activity(
                execute_audit_pipeline,
                args=[audit_id, user_id],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy,
            )

            await workflow.execute_activity(
                persist_audit_results,
                args=[audit_id, recheck_report],
                start_to_close_timeout=timedelta(seconds=30),
            )

            return recheck_report

        return report
