import streamlit as st
import json
import logging
from typing import List, Dict, Optional
from geo_audit_agent.agent import build_geo_audit_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Page Configuration ---
st.set_page_config(
    page_title="GEO Audit Agent Dashboard",
    page_icon="🌍",
    layout="wide"
)

# --- Session State Initialization ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "audit_results" not in st.session_state:
    st.session_state.audit_results = None
if "remediations" not in st.session_state:
    st.session_state.remediations = []

# --- Authentication ---
def login_screen():
    st.title("🔒 GEO SaaS Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if username == "admin" and password == "geo123":
                st.session_state.authenticated = True
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password")

if not st.session_state.authenticated:
    login_screen()
    st.stop()

# --- Main Dashboard ---
st.title("🌍 GEO Audit & Remediation Dashboard")
st.markdown("Monitor and improve your brand's presence in Generative Engine Optimization (GEO).")

# --- Sidebar Inputs ---
st.sidebar.header("Audit Configuration")
with st.sidebar.form("audit_form"):
    brand_name = st.text_input("Brand Name", value="Burger Hub")
    category = st.text_input("Category", value="fast food")
    city = st.text_input("City", value="Islamabad")
    run_audit = st.form_submit_button("🚀 Run GEO Audit")

if run_audit:
    with st.spinner(f"Running GEO Audit for {brand_name}..."):
        try:
            agent = build_geo_audit_agent()
            inputs = {
                "brand_name": brand_name,
                "category": category,
                "city": city,
                "gaps": [],
                "planned_actions": [],
                "remediation_results": []
            }
            results = agent.invoke(inputs)
            st.session_state.audit_results = results

            # Initialize remediations state
            st.session_state.remediations = []
            for res in results.get("remediation_results", []):
                st.session_state.remediations.append({
                    "tool": res["tool"],
                    "content": res.get("output_preview", "No preview available"),
                    "status": "Pending"
                })
            st.success("Audit Completed!")
        except Exception as e:
            st.error(f"Audit failed: {e}")
            logger.error(f"Audit error: {e}")

# --- Display Results ---
if st.session_state.audit_results:
    res = st.session_state.audit_results

    col1, col2, col3 = st.columns(3)

    with col1:
        is_cited = res.get("is_cited", False)
        st.metric("Citation Status", "Cited" if is_cited else "Not Cited",
                  delta="Positive" if is_cited else "Negative", delta_color="normal")

    with col2:
        confidence = res.get("confidence_score", 0.0)
        st.metric("Confidence Score", f"{confidence:.2f}")
        st.progress(confidence)

    with col3:
        gaps_count = len(res.get("gaps", []))
        st.metric("Gaps Identified", gaps_count)

    # Details Expanders
    with st.expander("📝 LLM Analysis Response"):
        st.write(res.get("llm_response", "No response content."))

    with st.expander("🚩 Identified Gaps"):
        gaps = res.get("gaps", [])
        if gaps:
            for gap in gaps:
                st.warning(f"**{gap['gap_type']}** ({gap['severity']}): {gap['description']}")
        else:
            st.success("No critical gaps identified!")

    # --- Remediation Panel (Human-in-the-Loop) ---
    st.divider()
    st.subheader("🛠️ Remediation & Content Review")
    st.info("Review, edit, and approve the AI-generated remediation content below.")

    if st.session_state.remediations:
        for idx, item in enumerate(st.session_state.remediations):
            with st.container(border=True):
                st.write(f"### Tool: `{item['tool']}`")

                # Dynamic text area for editing
                edited_content = st.text_area(
                    f"Edit content for {item['tool']}",
                    value=item['content'],
                    height=200,
                    key=f"edit_{idx}"
                )
                st.session_state.remediations[idx]['content'] = edited_content

                c1, c2, c3 = st.columns([1, 1, 2])
                with c1:
                    if st.button("✅ Approve", key=f"app_{idx}"):
                        st.session_state.remediations[idx]['status'] = "Approved"
                        st.toast(f"Approved {item['tool']}")
                with c2:
                    if st.button("❌ Reject", key=f"rej_{idx}"):
                        st.session_state.remediations[idx]['status'] = "Rejected"
                        st.toast(f"Rejected {item['tool']}")
                with c3:
                    status = st.session_state.remediations[idx]['status']
                    color = "green" if status == "Approved" else "red" if status == "Rejected" else "orange"
                    st.markdown(f"Status: **:{color}[{status}]**")

        # --- Export Section ---
        st.divider()
        approved_items = [i for i in st.session_state.remediations if i['status'] == "Approved"]

        if approved_items:
            export_data = {
                "brand": res["brand_name"],
                "approved_remediations": approved_items
            }
            json_export = json.dumps(export_data, indent=4)
            st.download_button(
                label="📥 Export Approved Remediation JSON",
                data=json_export,
                file_name=f"geo_remediation_{res['brand_name'].lower().replace(' ', '_')}.json",
                mime="application/json"
            )
        else:
            st.button("📥 Export Approved Remediation JSON", disabled=True, help="Approve at least one item to export.")
    else:
        st.write("No remediation results to display.")

# Footer
st.sidebar.divider()
st.sidebar.caption("GEO Audit Agent v1.0 (MVP)")
