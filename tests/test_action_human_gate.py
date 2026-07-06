import os

os.environ["FORCE_MOCK"] = "true"

from geo_audit_agent.agents.action_agent import ActionAgent
from geo_audit_agent.orchestration.state import AgenticState


def test_unapproved_action_is_held():
    s = AgenticState(brand_name="Burger Hub")
    s.action_plan = [{"action_id": "deploy_json_ld", "approved": False, "requires_approval": True}]
    s = ActionAgent().execute(s)
    assert s.action_results[0]["status"] == "awaiting_approval"


def test_approved_action_executes():
    s = AgenticState(brand_name="Burger Hub", category="restaurant", city="Austin")
    s.action_plan = [{"action_id": "generate_weekly_report", "approved": True, "requires_approval": False}]
    s = ActionAgent().execute(s)
    assert s.action_results[0]["status"] == "complete"
    assert s.action_results[0].get("artifact")


def test_non_approval_action_runs():
    s = AgenticState(brand_name="Burger Hub", category="restaurant", city="Austin")
    s.action_plan = [{"action_id": "generate_weekly_report", "approved": False, "requires_approval": False}]
    s = ActionAgent().execute(s)
    assert s.action_results[0]["status"] == "complete"
