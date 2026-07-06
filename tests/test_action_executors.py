"""Tests for all 16 action executors — mock mode, no credentials.

Every executor must return a dict with a 'status' key and produce a fallback
artifact when no platform credentials are configured.
"""
import importlib
import os

import pytest

os.environ.setdefault("FORCE_MOCK", "true")

CTX = {"brand": "Burger Hub", "category": "fast food", "city": "Islamabad",
       "gaps": [{"gap": "missing_json_ld"}], "score": 60.0}


def _executor_ids():
    from geo_audit_agent.actions.registry import REGISTRY
    return sorted(REGISTRY.keys())


@pytest.mark.parametrize("action_id", _executor_ids())
def test_executor_runs_without_credentials(action_id):
    from geo_audit_agent.actions.registry import REGISTRY
    action = REGISTRY[action_id]
    mod = importlib.import_module(f"geo_audit_agent.actions.executors.{action.executor}")
    result = mod.execute(dict(CTX))
    assert isinstance(result, dict)
    assert "status" in result
    # without credentials, nothing should claim a real deployment
    assert result["status"] != "deployed"


def test_registry_has_16_actions():
    from geo_audit_agent.actions.registry import REGISTRY
    assert len(REGISTRY) == 16


def test_registry_approval_flags():
    from geo_audit_agent.actions.registry import REGISTRY
    # every outward-facing platform action must require human approval
    for aid, action in REGISTRY.items():
        if action.platform in ("WordPress", "Google Business", "Email", "LinkedIn"):
            assert action.requires_approval, f"{aid} posts externally but skips approval"
