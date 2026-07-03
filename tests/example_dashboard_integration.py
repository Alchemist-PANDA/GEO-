"""
Drop-in example of how to protect your existing dashboard.py.
Add these two lines at the very top, before any other Streamlit calls.
"""

import streamlit as st

from auth import current_user, require_login, sign_out

st.set_page_config(page_title="BrandSight GEO", layout="wide")

# This blocks the rest of the script from running (st.stop()) until the
# person is logged in. Every rerun re-checks the persisted cookie/session,
# so this is cheap and safe to put on every page of a multi-page app.
user = require_login()

with st.sidebar:
    st.write(f"Logged in as **{user.email}**")
    if st.button("Log out"):
        sign_out()
        st.rerun()

# --- everything below here only runs for authenticated users ---
st.title("BrandSight GEO Dashboard")
st.write("Your existing dashboard code goes here, unchanged.")
