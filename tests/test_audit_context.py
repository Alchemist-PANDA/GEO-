import csv
import io
import json

from geo_audit_agent.ui.audit_context import (
    activate_audit_context,
    audit_csv,
    audit_json,
    audit_markdown,
    build_audit_context,
)


def _fixture_audit():
    return {
        "summary": {"data_source": "simulated", "visibility_score": 0.5, "models_tested": 2},
        "results": [
            {"model": "Alpha", "provider": "alpha", "mode": "fixture", "mentioned": True,
             "position": 1, "evidence": "Acme mentioned"},
            {"model": "Beta", "provider": "beta", "mode": "fixture", "mentioned": False,
             "position": None, "evidence": "Acme not mentioned"},
        ],
    }


def test_context_is_canonical_and_derives_evidence_backed_gap():
    context = build_audit_context(
        _fixture_audit(),
        {"brand": "Acme", "category": "Coffee", "city": "Islamabad", "run_at": "2026-01-01T00:00:00Z"},
        audit_id="audit-1",
    )
    assert context["id"] == "audit-1"
    assert context["report"]["geo_score"] == 50
    assert context["data_source"] == "simulated"
    assert context["gaps"] == [{
        "id": "missing-mention-beta",
        "gap_type": "content authority",
        "severity": "High",
        "description": "Brand was not mentioned in the beta recommendation observation.",
        "provider": "beta",
        "evidence": "Acme not mentioned",
        "execution_mode": "fixture",
    }]


def test_activation_connects_legacy_workspaces_and_keeps_bounded_history():
    state = {"audit_history": []}
    first = build_audit_context(_fixture_audit(), {"brand": "A", "category": "C", "city": "I"}, audit_id="1")
    second = build_audit_context(_fixture_audit(), {"brand": "B", "category": "C", "city": "L"}, audit_id="2")
    activate_audit_context(state, first, max_history=2)
    activate_audit_context(state, second, max_history=2)
    assert state["active_audit_id"] == "2"
    assert state["audit_results"] is second
    assert state["brand_name"] == "B"
    assert [item["id"] for item in state["audit_history"]] == ["2", "1"]


def test_exports_are_machine_and_human_readable():
    context = build_audit_context(
        _fixture_audit(), {"brand": "Acme", "category": "Coffee", "city": "Islamabad"}, audit_id="1",
    )
    assert json.loads(audit_json(context))["brand_name"] == "Acme"
    assert list(csv.DictReader(io.StringIO(audit_csv(context))))[1]["provider"] == "beta"
    report = audit_markdown(context)
    assert "# BrandSight GEO audit — Acme" in report
    assert "Data source: SIMULATED" in report
