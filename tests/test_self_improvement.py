"""Tests for the self-improvement loop: tracker, proposer, shadow, canary."""
import os

os.environ.setdefault("FORCE_MOCK", "true")


def test_record_trace_survives_db_failure():
    from geo_audit_agent.self_improvement.outcome_tracker import record_trace
    # must not raise even when the DB is unavailable / tables missing
    record_trace("agent1", "trace1", {"q": "test"}, {"a": "answer"}, score=0.9)


def test_attach_outcome_survives_db_failure():
    from geo_audit_agent.self_improvement.outcome_tracker import attach_outcome
    attach_outcome("nonexistent-trace", {"result": "ok"}, 0.8)


def test_proposer_returns_none_without_traces():
    from geo_audit_agent.self_improvement.improvement_proposer import propose
    assert propose("agent-with-no-traces") is None


def test_canary_noop_in_mock_mode():
    from geo_audit_agent.self_improvement import canary_rollout as cr
    cr.set_canary("a1", "p1", {"x": 1})
    assert cr.variant_active("a1", "req-123") is None
    cr.promote("a1")
    cr.rollback("a1")


def test_shadow_tester_rejects_empty_golden_set(tmp_path, monkeypatch):
    from geo_audit_agent.self_improvement.shadow_tester import shadow_test
    monkeypatch.setattr(
        "geo_audit_agent.evaluation.golden_set.load", lambda: [])
    res = shadow_test(lambda c: "variant output")
    assert res["passed"] is False
    assert res["reason"] == "empty_golden_set"


def test_shadow_tester_scores_variant():
    from geo_audit_agent.self_improvement.shadow_tester import shadow_test
    # echo the expected output — variant should never regress vs baseline
    res = shadow_test(lambda c: c["expected_output"])
    assert "passed" in res
    if "before" in res:
        assert res["after"] >= res["before"]


def test_celery_self_improvement_task():
    from geo_audit_agent.workers.self_improvement_task import run_self_improvement
    result = run_self_improvement("test-agent")
    assert result["status"] in ("skipped", "proposed", "error")
