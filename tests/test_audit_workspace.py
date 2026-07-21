from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_dashboard_discloses_evidence_statuses_and_sample_sizes():
    app = AppTest.from_file("dashboard.py").run(timeout=20)
    assert not app.exception
    markdown = "\n".join(item.value for item in app.markdown)
    assert "AI Visibility Dashboard" in markdown
    assert "Insufficient evidence" in markdown
    assert "0 / 0 observations" in markdown
    assert "Live" in markdown
    assert "Cached" in markdown


def test_new_audit_demo_mode_is_unmissably_disclosed():
    app = AppTest.from_file("dashboard.py").run(timeout=20)
    app.radio[0].set_value("New Audit").run(timeout=20)
    app.toggle(key="new_audit_demo_mode").set_value(True).run(timeout=20)
    assert not app.exception
    assert any("Demo mode is not real AI visibility evidence" in item.value for item in app.warning)
    assert any("excluded from authoritative metrics" in item.value for item in app.warning)


def test_repeated_filters_have_stable_unique_keys():
    app = AppTest.from_file("dashboard.py").run(timeout=20)
    assert not app.exception
    assert app.selectbox(key="dashboard_provider_filter").value == "All"

    app.radio[0].set_value("Competitors").run(timeout=20)
    assert not app.exception
    assert app.selectbox(key="competitor_provider_filter").value == "All"
    assert app.selectbox(key="competitor_brand_filter").value == "Dental Art"
    assert app.selectbox(key="competitor_date_range_filter").value == "Last 30 days"

    app.radio[0].set_value("Brands").run(timeout=20)
    assert not app.exception
    assert app.selectbox(key="brand_detail_selected_brand").value == "Dental Art"


def test_primary_ui_contains_no_known_fabricated_telemetry():
    source = Path("geo_audit_agent/ui/audit_workspace.py").read_text(encoding="utf-8")
    for banned in ("2,663", "2663", "np.random", "random.randint", "hashlib.md5"):
        assert banned not in source
