import uuid

from geo_audit_agent.metrics.visibility_metrics import calculate_visibility_metrics
from geo_audit_agent.providers import ExecutionMode, ProviderResult
from geo_audit_agent.services.evidence import (
    evidence_as_metric_row,
    provider_result_to_evidence,
    report_to_evidence,
)


def test_provider_result_maps_to_complete_evidence():
    audit_id = uuid.uuid4()
    result = ProviderResult(
        provider="openai", model="test-model", prompt_id="recommendation", prompt_version="2",
        text="Acme Coffee is recommended. Source: https://example.com/acme", mode=ExecutionMode.LIVE,
        latency_ms=123, input_tokens=10, output_tokens=20, cost_usd=0.01,
    )
    evidence = provider_result_to_evidence(result, audit_id=audit_id, brand="Acme Coffee")
    assert evidence.audit_id == audit_id
    assert evidence.mentioned is True
    assert evidence.citation_urls == ["https://example.com/acme"]
    assert evidence.latency_ms == 123
    assert evidence.execution_mode == "live"


def test_evidence_row_is_authoritative_metric_input():
    evidence = report_to_evidence({"observation": {
        "provider": "google", "model": "gemini", "prompt_id": "p", "prompt_version": "1",
        "execution_mode": "live", "raw_response": "Acme", "mentioned": True,
        "recommendation": True, "position": 2, "citation_urls": [],
    }}, audit_id=uuid.uuid4())
    metrics = calculate_visibility_metrics([evidence_as_metric_row(evidence)])
    assert metrics.mention_rate.value == 1.0
    assert metrics.top_three_rate.value == 1.0


def test_missing_observation_fields_map_to_failed_not_fake_values():
    evidence = report_to_evidence({}, audit_id=uuid.uuid4())
    assert evidence.execution_mode == "failed"
    assert evidence.mentioned is False
    assert evidence.raw_response == ""
