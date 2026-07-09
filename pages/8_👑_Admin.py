from datetime import datetime

import pandas as pd
import streamlit as st
from sqlmodel import func, select

from geo_audit_agent.auth.user import TIER_CONFIG
from geo_audit_agent.db.models import AuditUsage, InvoiceRequest, UserProfile
from geo_audit_agent.db.session import get_session

st.set_page_config(page_title="Admin Panel", page_icon="👑", layout="wide")

# ── Restrict access ──
ADMIN_EMAIL = "admin@brandsightgeo.com"
if st.session_state.get("user_email") != ADMIN_EMAIL:
    st.error("❌ Access denied. Admin only.")
    st.stop()

st.title("👑 Admin Dashboard")

# ── Stats ──
with get_session() as s:
    total_users = s.exec(select(func.count(UserProfile.id))).one()
    paid_users = s.exec(select(func.count(UserProfile.id)).where(UserProfile.tier != "free")).one()
    total_revenue = 0  # You can calculate from invoice_requests

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Users", total_users)
col2.metric("Paid Users", paid_users)
col3.metric("Revenue (MTD)", f"${total_revenue:,.2f}")
col4.metric("MRR", f"${paid_users * 49:,.2f}")

# ── Tabs ──
tab1, tab2, tab3, tab4 = st.tabs(["👥 Users", "📄 Invoices", "📊 Analytics", "⚙️ Settings"])

# ── TAB 1: Users ──
with tab1:
    st.subheader("👥 User Management")

    # ── Filters ──
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search = st.text_input("🔍 Search", placeholder="Search by email...")
    with col2:
        tier_filter = st.selectbox("Filter by Tier", ["All"] + list(TIER_CONFIG.keys()))
    with col3:
        sort_by = st.selectbox("Sort by", ["Created (newest)", "Created (oldest)", "Tier"])

    # ── Fetch users ──
    with get_session() as s:
        query = select(UserProfile)
        if search:
            query = query.where(UserProfile.email.contains(search))
        if tier_filter != "All":
            query = query.where(UserProfile.tier == tier_filter)

        if sort_by == "Created (newest)":
            query = query.order_by(UserProfile.created_at.desc())
        elif sort_by == "Created (oldest)":
            query = query.order_by(UserProfile.created_at.asc())
        elif sort_by == "Tier":
            query = query.order_by(UserProfile.tier)

        users = s.exec(query).all()

    # ── Display users ──
    if users:
        data = []
        for user in users:
            # Get audit usage
            with get_session() as s2:
                usage = s2.exec(select(AuditUsage).where(AuditUsage.user_id == user.id)).all()
                total_audits = sum(u.count for u in usage)

            tier_limit = TIER_CONFIG.get(user.tier, {}).get("audits_per_month", 0)

            data.append({
                "ID": str(user.id)[:8],
                "Email": user.email,
                "Tier": user.tier.capitalize(),
                "Audits": f"{total_audits}/{tier_limit if tier_limit != 999999 else '∞'}",
                "Joined": user.created_at.strftime("%Y-%m-%d") if user.created_at else "N/A",
                "Actions": "Edit|Upgrade|Delete",
            })

        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)

        # ── Quick Actions ──
        st.subheader("⚡ Quick Actions")
        col1, col2, col3 = st.columns(3)

        with col1:
            with st.form("upgrade_form"):
                user_emails = [u.email for u in users]
                selected_email = st.selectbox("Select User", user_emails)
                new_tier = st.selectbox("New Tier", list(TIER_CONFIG.keys()))
                if st.form_submit_button("⬆️ Upgrade User"):
                    with get_session() as s:
                        user = s.exec(select(UserProfile).where(UserProfile.email == selected_email)).first()
                        if user:
                            user.tier = new_tier
                            s.add(user)
                            s.commit()
                            st.success(f"✅ {selected_email} upgraded to {new_tier}")
                            st.rerun()

        with col2:
            with st.form("delete_form"):
                delete_email = st.selectbox("Select User to Delete", user_emails)
                confirm = st.checkbox("I understand this action is permanent")
                if st.form_submit_button("🗑️ Delete User"):
                    if confirm:
                        with get_session() as s:
                            user = s.exec(select(UserProfile).where(UserProfile.email == delete_email)).first()
                            if user:
                                s.delete(user)
                                s.commit()
                                st.success(f"✅ {delete_email} deleted")
                                st.rerun()
                    else:
                        st.warning("Please confirm deletion")

        with col3:
            st.info("📤 Export users as CSV")
            if st.button("📥 Export CSV"):
                df.to_csv("users_export.csv", index=False)
                st.success("✅ users_export.csv downloaded")

# ── TAB 2: Invoices ──
with tab2:
    st.subheader("📄 Invoice Management")

    # ── Invoice requests ──
    with get_session() as s:
        requests = s.exec(select(InvoiceRequest).order_by(InvoiceRequest.created_at.desc())).all()

    if not requests:
        st.info("No invoice requests yet.")
    else:
        data = []
        for req in requests:
            with get_session() as s2:
                user = s2.get(UserProfile, req.user_id)

            data.append({
                "ID": str(req.id)[:8],
                "User": user.email if user else "Unknown",
                "Tier": req.tier.capitalize(),
                "Amount": f"${req.amount}",
                "Status": req.status,
                "Requested": req.created_at.strftime("%Y-%m-%d"),
                "Notes": req.notes or ""
            })
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)

        st.subheader("Update Invoice Status")
        with st.form("update_invoice_form"):
            request_ids = [str(r.id) for r in requests]
            selected_req_id = st.selectbox("Select Request ID", request_ids)
            new_status = st.selectbox("New Status", ["pending", "sent", "paid", "cancelled"])

            if st.form_submit_button("Update Status"):
                with get_session() as s:
                    # find the actual request
                    for req in requests:
                        if str(req.id) == selected_req_id:
                            req_to_update = s.get(InvoiceRequest, req.id)
                            if req_to_update:
                                req_to_update.status = new_status
                                if new_status == "paid":
                                    req_to_update.paid_at = datetime.utcnow()
                                    # auto upgrade user
                                    user = s.get(UserProfile, req_to_update.user_id)
                                    if user:
                                        user.tier = req_to_update.tier
                                        s.add(user)
                                elif new_status == "sent":
                                    req_to_update.invoice_sent_at = datetime.utcnow()
                                s.add(req_to_update)
                                s.commit()
                                st.success(f"✅ Invoice request {selected_req_id[:8]} marked as {new_status}")
                                st.rerun()

    # ── Create invoice request ──
    with st.expander("➕ Create Invoice Request"):
        with get_session() as s:
            users = s.exec(select(UserProfile)).all()
            user_emails = [u.email for u in users]

        with st.form("invoice_request_form"):
            email = st.selectbox("User", user_emails)
            tier = st.selectbox("Tier", list(TIER_CONFIG.keys()))
            amount = st.number_input("Amount", min_value=0.0, step=5.0)
            notes = st.text_area("Notes (optional)")

            if st.form_submit_button("📩 Create Invoice Request"):
                with get_session() as s:
                    user = s.exec(select(UserProfile).where(UserProfile.email == email)).first()
                    if user:
                        request = InvoiceRequest(
                            user_id=user.id,
                            tier=tier,
                            amount=amount,
                            status="pending",
                            notes=notes,
                        )
                        s.add(request)
                        s.commit()
                        st.success(f"✅ Invoice request created for {email}")
                        st.rerun()

# ── TAB 3: Analytics ──
with tab3:
    st.subheader("📊 Analytics")

    # ── User growth ──
    with get_session() as s:
        from sqlmodel import func
        users = s.exec(select(UserProfile)).all()

    # ── Tier distribution ──
    tier_counts = {}
    for user in users:
        tier_counts[user.tier] = tier_counts.get(user.tier, 0) + 1

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📈 Tier Distribution")
        st.bar_chart(tier_counts)

    with col2:
        st.markdown("#### 💰 Revenue Summary")
        st.metric("Total Users", len(users))
        paid = sum(1 for u in users if u.tier != "free")
        st.metric("Paid Users", paid)
        st.metric("Conversion Rate", f"{paid/len(users)*100:.1f}%" if users else "0%")

    # ── Monthly revenue (manual entry) ──
    st.subheader("💰 Revenue Tracking")
    st.caption("Enter revenue manually to track your business growth.")

    with get_session() as s:
        requests = s.exec(select(InvoiceRequest).where(InvoiceRequest.status == "paid")).all()
        total_paid = sum(r.amount for r in requests)

    st.metric("Total Revenue (All Time)", f"${total_paid:,.2f}")

# ── TAB 4: Settings ──
with tab4:
    st.subheader("⚙️ Admin Settings")

    st.info("📧 Admin Email: admin@brandsightgeo.com")

    st.divider()

    st.markdown("### 🏷️ Tier Settings")
    st.json(TIER_CONFIG)

    st.divider()

    st.markdown("### 🗄️ Database")
    if st.button("🔄 Run Database Migration"):
        st.warning("⚠️ This would run alembic upgrade head in a production environment.")

    st.divider()

    st.markdown("### ⚠️ Danger Zone")
    if st.button("🗑️ Delete All Test Data", type="primary"):
        st.error("⚠️ This will delete all test users. Are you sure?")
        if st.button("✅ Confirm Delete"):
            # Mock behavior
            st.success("Test data deleted (simulated)")
