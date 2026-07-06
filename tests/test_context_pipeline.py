import os

os.environ["FORCE_MOCK"] = "true"

from geo_audit_agent.context import build_context
from geo_audit_agent.context.compression_layer import compress
from geo_audit_agent.context.fusion_layer import fuse
from geo_audit_agent.context.validation_layer import validate


def test_build_context_returns_valid_bundle():
    result = build_context("audit my brand", brand="TestBrand", industry="tech")
    assert "intent" in result
    assert "prompt" in result
    assert "bundle" in result
    assert "validation" in result


def test_build_context_classifies_intent():
    result = build_context("run an audit on my brand")
    assert result["intent"] == "audit"


def test_validation_insufficient_evidence():
    bundle = {"evidence": [], "query": "test", "evidence_meta": []}
    v = validate(bundle, min_evidence=1)
    assert "insufficient_evidence" in v["issues"]


def test_validation_passes_with_evidence():
    bundle = {"evidence": ["some evidence"], "query": "test", "evidence_meta": []}
    v = validate(bundle, min_evidence=1)
    assert v["valid"] is True


def test_fusion_merges_sources():
    result = fuse(query="test", retrieved=[{"text": "doc1", "meta": {}}],
                  memory=["mem1"], business_rules=["rule1"],
                  live_metrics={"score": 70}, history=[{"q": "prev"}],
                  agent_state={"gaps": []})
    assert result["query"] == "test"
    assert result["evidence"] == ["doc1"]
    assert result["memory"] == ["mem1"]


def test_compression_deduplicates():
    bundle = {"evidence": ["same text here", "same text here", "different text"]}
    result = compress(bundle)
    assert len(result["evidence"]) == 2
