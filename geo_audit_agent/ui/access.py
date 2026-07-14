"""Streamlit access policy: authenticated production, explicit fixture-only demo."""
from __future__ import annotations

import os
from dataclasses import dataclass

import streamlit as st


@dataclass(frozen=True)
class WorkspaceUser:
    id: str
    email: str
    is_demo: bool = False


def auth_configured() -> bool:
    if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"):
        return True
    try:
        return "supabase" in st.secrets and bool(st.secrets["supabase"].get("url"))
    except Exception:
        return False


def require_user_or_demo() -> WorkspaceUser:
    if auth_configured():
        from auth import require_login

        user = require_login()
        return WorkspaceUser(id=user.id, email=user.email)
    st.warning("Demo workspace — authentication and live execution are disabled; all audit data is session-local.")
    return WorkspaceUser(id="demo-session", email="demo@local.invalid", is_demo=True)
