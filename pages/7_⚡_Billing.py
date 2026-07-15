from __future__ import annotations

import uuid

import streamlit as st
from sqlmodel import select

from auth import require_login
from geo_audit_agent.auth.user import TIER_CONFIG, get_user_tier
from geo_audit_agent.db.models import InvoiceRequest
from geo_audit_agent.db.session import get_session
from geo_audit_agent.ui.theme import apply_theme, render_page_header

st.set_page_config(page_title="Billing & Plans", page_icon="💳", layout="wide")
apply_theme()

user = require_login()
user_email = user.email
try:
    user_id = uuid.UUID(str(user.id))
except (TypeError, ValueError):
    st.error("Your account identifier is invalid. Please sign out and sign in again.")
    st.stop()

render_page_header("💳", "Billing & plans", "Simple usage-based plans for teams measuring and improving AI visibility.")

current_tier = get_user_tier(str(user_id))
st.success(f"Current plan: **{current_tier.upper()}** · Signed in as {user_email}")

st.markdown("### Choose the right workspace")
tiers = [tier for tier in TIER_CONFIG if tier != "free"]
cols = st.columns(len(tiers))

for col, tier_name in zip(cols, tiers, strict=False):
    config = TIER_CONFIG[tier_name]
    with col:
        with st.container(border=True):
            st.markdown(f"### {tier_name.capitalize()}")
            st.markdown(f"## ${config['price']}<span style='font-size:.9rem;color:#64748b'>/month</span>", unsafe_allow_html=True)
            st.caption("Built for growing GEO operations")
            st.markdown(f"✅ **{config['audits_per_month']:,}** audits / month")
            st.markdown(f"✅ **{config['competitors']:,}** competitors tracked")
            st.markdown("✅ " + ", ".join(config["models"]))
            if config.get("action_agent"):
                st.markdown("✅ Approval-gated Action Agent")

            if tier_name == current_tier:
                st.button("Current plan", disabled=True, key=f"btn_{tier_name}", use_container_width=True)
            else:
                with st.expander("Request this plan"):
                    with st.form(key=f"form_{tier_name}"):
                        notes = st.text_area("Billing notes", placeholder="Company name, tax details, purchase-order requirements…")
                        submitted = st.form_submit_button("Submit invoice request", type="primary", use_container_width=True)
                    if submitted:
                        try:
                            with get_session() as session:
                                request = InvoiceRequest(
                                    user_id=user_id,
                                    tier=tier_name,
                                    amount=config["price"],
                                    status="pending",
                                    notes=notes.strip(),
                                )
                                session.add(request)
                                session.commit()
                            st.success("Invoice request submitted. Our team will contact you with the next step.")
                            st.rerun()
                        except Exception:
                            st.error("We could not submit the invoice request. Please try again or contact support.")

st.divider()
render_page_header("🧾", "Invoice history", "A private record of your plan requests and their current status.")

try:
    with get_session() as session:
        requests = session.exec(
            select(InvoiceRequest)
            .where(InvoiceRequest.user_id == user_id)
            .order_by(InvoiceRequest.created_at.desc())
        ).all()
except Exception:
    requests = []
    st.warning("Invoice history is temporarily unavailable. No private database details were exposed.")

if not requests:
    st.info("You have no invoice requests yet.")
else:
    for request in requests:
        with st.container(border=True):
            left, middle, right = st.columns([2, 2, 1])
            left.markdown(f"**{request.tier.capitalize()} plan**")
            left.caption(request.created_at.strftime("%d %b %Y, %H:%M"))
            middle.markdown(f"**${request.amount}**")
            middle.caption("Requested amount")
            right.markdown(f"**{request.status.upper()}**")
