import streamlit as st

from auth import require_login
from geo_audit_agent.auth.user import TIER_CONFIG, get_user_tier
from geo_audit_agent.db.models import InvoiceRequest
from geo_audit_agent.db.session import get_session

st.set_page_config(page_title="Billing & Plans", page_icon="⚡", layout="wide")

user = require_login()
user_email = user.email
user_id = user.id

st.title("⚡ Billing & Plans")
st.write("Manage your BrandSight GEO subscription.")

current_tier = get_user_tier(user_id)
st.success(f"**Current Plan:** {current_tier.upper()}")

st.markdown("---")
st.subheader("Upgrade Your Plan")

# Display plans in columns
cols = st.columns(4)

tiers = [t for t in TIER_CONFIG.keys() if t != "free"]

for i, tier_name in enumerate(tiers):
    col = cols[i % 4]
    config = TIER_CONFIG[tier_name]

    with col:
        st.markdown(f"### {tier_name.capitalize()}")
        st.markdown(f"**${config['price']}/month**")
        st.markdown(f"✅ {config['audits_per_month']} audits/month")
        st.markdown(f"✅ {config['competitors']} competitors tracked")

        models_str = ", ".join(config['models'])
        st.markdown(f"🤖 Models: {models_str}")

        if config['action_agent']:
            st.markdown("✅ Action Agent included")

        if tier_name == current_tier:
            st.button("Current Plan", disabled=True, key=f"btn_{tier_name}")
        else:
            with st.expander(f"Request Invoice for {tier_name.capitalize()}"):
                with st.form(key=f"form_{tier_name}"):
                    st.write(f"Send a request to upgrade to **{tier_name.capitalize()}**.")
                    notes = st.text_area("Any special notes or billing details?", key=f"notes_{tier_name}")
                    if st.form_submit_button("Submit Request"):
                        with get_session() as s:
                            # Create an invoice request
                            req = InvoiceRequest(
                                user_id=user_id,
                                tier=tier_name,
                                amount=config['price'],
                                status="pending",
                                notes=notes
                            )
                            s.add(req)
                            s.commit()
                            st.success("✅ Invoice request submitted! Our team will process it shortly and upgrade your account upon payment.")

st.markdown("---")
st.subheader("Invoice History")

with get_session() as s:
    from sqlmodel import select
    requests = s.exec(select(InvoiceRequest).where(InvoiceRequest.user_id == user_id).order_by(InvoiceRequest.created_at.desc())).all()

    if not requests:
        st.info("You have no past invoice requests.")
    else:
        for r in requests:
            st.write(f"**{r.created_at.strftime('%Y-%m-%d')}** | Tier: {r.tier.capitalize()} | Amount: ${r.amount} | Status: **{r.status.upper()}**")
