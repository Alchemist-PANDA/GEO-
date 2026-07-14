from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_dashboard_starts_empty_and_discloses_local_mode():
    app = AppTest.from_file("dashboard.py").run(timeout=20)
    assert not app.exception
    assert any("No sample results are preloaded" in item.value for item in app.info)
    assert any("Live execution is disabled" in item.value for item in app.warning)


def test_demo_audit_is_unmissably_disclosed():
    app = AppTest.from_file("dashboard.py").run(timeout=20)
    app.text_input[0].set_value("Acme Coffee")
    app.text_input[1].set_value("coffee shop")
    app.text_input[2].set_value("Islamabad")
    app.button[0].click().run(timeout=20)
    assert not app.exception
    assert any("DEMO DATA" in item.value for item in app.error)
    assert any("excluded from authoritative metrics" in item.value for item in app.info)
    assert sum("FIXTURE" in item.label for item in app.expander) == 5
    assert app.session_state["active_audit"]["brand_name"] == "Acme Coffee"
    assert app.session_state["active_audit"]["data_source"] == "simulated"
    assert app.session_state["audit_results"]["gaps"]
    assert len(app.session_state["audit_history"]) == 1
    assert len(app.get("download_button")) == 3


def test_primary_ui_contains_no_known_fabricated_telemetry():
    source = Path("geo_audit_agent/ui/audit_workspace.py").read_text(encoding="utf-8")
    for banned in ("2,663", "2663", "np.random", "random.randint", "hashlib.md5"):
        assert banned not in source
