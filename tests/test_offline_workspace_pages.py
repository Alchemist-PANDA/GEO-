from streamlit.testing.v1 import AppTest


def test_copilot_is_available_without_auth_in_explicit_demo_mode():
    app = AppTest.from_file("pages/3_🤖_Copilot.py").run(timeout=20)
    assert not app.exception
    assert any("Demo workspace" in item.value for item in app.warning)
    assert any("Start an evidence-grounded conversation" in item.value for item in app.markdown)


def test_action_agent_empty_state_is_available_without_auth():
    app = AppTest.from_file("pages/4_⚡_Action_Agent.py").run(timeout=20)
    assert not app.exception
    assert any("Demo workspace" in item.value for item in app.warning)
    assert any("Run a visibility audit first" in item.value for item in app.markdown)


def test_action_agent_consumes_the_canonical_audit_context():
    app = AppTest.from_file("pages/4_⚡_Action_Agent.py")
    app.session_state["audit_results"] = {
        "gaps": [{
            "id": "missing-mention-openai",
            "gap_type": "content authority",
            "severity": "High",
            "description": "Brand was not mentioned.",
        }],
    }
    app.session_state["active_audit"] = {
        "brand_name": "Acme Coffee",
        "city": "Islamabad",
        "data_source": "simulated",
    }
    app.run(timeout=20)
    assert not app.exception
    assert any("Selected audit: Acme Coffee" in item.value for item in app.caption)
    assert any("Demo data" in item.value for item in app.warning)
    assert any(button.label == "Execute approved actions" for button in app.button)


def test_copilot_discloses_fixture_context_in_an_end_to_end_answer():
    app = AppTest.from_file("pages/3_🤖_Copilot.py")
    app.session_state["verified_audit_input"] = {
        "brand": "Acme Coffee",
        "category": "coffee shop",
        "city": "Islamabad",
    }
    app.session_state["verified_audit"] = {
        "summary": {"data_source": "simulated", "visibility_score": 0.5},
        "results": [{
            "model": "ChatGPT",
            "provider": "openai",
            "mode": "fixture",
            "mentioned": True,
            "confidence": 0.8,
        }],
    }
    app.run(timeout=20)
    next(button for button in app.button if button.label == "Visibility").click().run(timeout=20)
    assert not app.exception
    assert any("DEMO FIXTURE" in item.value for item in app.markdown)


def test_agentic_workflow_is_available_without_auth():
    app = AppTest.from_file("pages/6_🧠_Agentic_Workflow.py").run(timeout=20)
    assert not app.exception
    assert any("Demo workspace" in item.value for item in app.warning)
    assert app.text_area[0].label == "Instruction"
    assert any(button.label == "Run governed workflow" for button in app.button)
