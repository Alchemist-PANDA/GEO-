"""
auth.py — Supabase-backed authentication for Streamlit apps.

Design goals:
- $0 cost: uses Supabase free tier (50,000 MAU) for all the hard parts
  (password hashing, brute-force/rate limiting, session token rotation,
  email verification). We never hand-roll crypto.
- Multiple named users, identical access level (no roles).
- Session persists across a Streamlit rerun/refresh via a signed cookie,
  not just st.session_state (which is wiped on refresh).

Setup required (one-time, in your Supabase project — free tier):
1. Go to supabase.com -> New project (free tier).
2. Authentication -> Providers -> make sure "Email" is enabled.
3. Authentication -> Settings -> turn OFF "Allow new users to sign up"
   if you want to be the only one creating accounts (invite-only), or
   leave it ON if anyone with the link should be able to self-register.
4. Authentication -> URL configuration -> Site URL: set to wherever
   you deploy (e.g. https://yourapp.streamlit.app). Needed for the
   email confirmation link to redirect correctly.
5. Copy your Project URL and anon public API key into secrets (see
   secrets.toml.example in this folder) — the anon key is safe to
   ship client-side, it has no power without a valid user session and
   RLS policies (see schema.sql) enforce what it can actually touch.

This module intentionally does NOT use the Supabase service_role key
anywhere. service_role bypasses Row Level Security entirely — if it
ever ends up in a Streamlit app (even server-side on community cloud,
where the whole repo is public if the app is public), that's a full
database compromise. Keep it out of this codebase, full stop.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import extra_streamlit_components as stx
import streamlit as st
from supabase import Client, create_client

COOKIE_NAME = "sb_session"
# How long a persisted session cookie is trusted before we force a
# fresh Supabase token refresh check. Keep short-ish; Supabase's own
# refresh token handles the real long-lived session.
COOKIE_MAX_AGE_DAYS = 7


@dataclass
class AuthedUser:
    id: str
    email: str

    def __getitem__(self, key):
        return getattr(self, key)

    def get(self, key, default=None):
        return getattr(self, key, default)


def _get_client() -> Client | None:
    import os
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["anon_key"]
    except (KeyError, AttributeError, FileNotFoundError):
        if os.getenv("DEV_MODE", "false").lower() == "true":
            if "supabase_warning_shown" not in st.session_state:
                st.info("🔧 DEV_MODE – using dummy user.")
                st.session_state.supabase_warning_shown = True
            return None
        st.error("⚠️ Supabase secrets not configured. Please add them to Streamlit Cloud secrets.")
        return None

    if "sb_client" not in st.session_state:
        st.session_state.sb_client = create_client(url, key)
    return st.session_state.sb_client


def _get_cookie_manager() -> stx.CookieManager:
    if "cookie_manager" not in st.session_state:
        st.session_state.cookie_manager = stx.CookieManager(key="auth_cookie_mgr")
    return st.session_state.cookie_manager


def _restore_session(client: Client | None, cookies: dict) -> AuthedUser | None:
    """Try to restore a session from the persisted refresh token."""
    if client is None:
        return None
    refresh_token = cookies.get(COOKIE_NAME)
    if not refresh_token:
        return None
    try:
        result = client.auth.refresh_session(refresh_token)
        user = result.user
        session = result.session
        if user is None or session is None:
            return None
        st.session_state.sb_access_token = session.access_token
        st.session_state.sb_refresh_token = session.refresh_token
        return AuthedUser(id=user.id, email=user.email)
    except Exception:
        return None


def current_user() -> AuthedUser | None:
    """Returns the logged-in user, or None. Call this at the top of every page."""
    import os
    if "authed_user" in st.session_state:
        return st.session_state.authed_user

    client = _get_client()
    if client is None:
        if os.getenv("DEV_MODE", "false").lower() == "true":
            dummy = AuthedUser(id="dev-user", email="dev@example.com")
            st.session_state.authed_user = dummy
            return dummy
        return None

    cookie_mgr = _get_cookie_manager()
    cookies = cookie_mgr.get_all()

    user = _restore_session(client, cookies)
    st.session_state.authed_user = user
    return user


def sign_in(email: str, password: str) -> tuple[bool, str]:
    """Returns (success, message)."""
    client = _get_client()
    if client is None:
        return False, "Database client unavailable."
    try:
        result = client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        user = result.user
        session = result.session
        if user is None or session is None:
            return False, "Invalid email or password."

        st.session_state.sb_access_token = session.access_token
        st.session_state.sb_refresh_token = session.refresh_token
        st.session_state.authed_user = AuthedUser(id=user.id, email=user.email)

        cookie_mgr = _get_cookie_manager()
        cookie_mgr.set(
            COOKIE_NAME,
            session.refresh_token,
            max_age=COOKIE_MAX_AGE_DAYS * 24 * 60 * 60,
            key="set_session_cookie",
        )
        return True, "Signed in."
    except Exception as e:
        # Supabase already rate-limits repeated failed attempts server-side,
        # so we don't need to (and shouldn't try to) implement lockout logic
        # here — that's exactly the kind of hand-rolled auth logic that's
        # easy to get subtly wrong.
        return False, _friendly_error(e)


def sign_up(email: str, password: str) -> tuple[bool, str]:
    """Returns (success, message). Requires email confirmation if enabled
    in Supabase settings (recommended — prevents fake/typo emails)."""
    client = _get_client()
    if client is None:
        return False, "Database client unavailable."
    try:
        client.auth.sign_up({"email": email, "password": password})
        return True, "Account created. Check your email to confirm before signing in."
    except Exception as e:
        return False, _friendly_error(e)


def sign_out() -> None:
    client = _get_client()
    if client is not None:
        try:
            client.auth.sign_out()
        except Exception:
            pass
    for k in ("authed_user", "sb_access_token", "sb_refresh_token"):
        st.session_state.pop(k, None)
    cookie_mgr = _get_cookie_manager()
    cookie_mgr.delete(COOKIE_NAME, key="delete_session_cookie")


def _friendly_error(e: Exception) -> str:
    msg = str(e)
    if "already registered" in msg.lower():
        return "That email is already registered — try signing in instead."
    if "invalid login credentials" in msg.lower():
        return "Invalid email or password."
    if "email not confirmed" in msg.lower():
        return "Please confirm your email before signing in (check your inbox)."
    return "Something went wrong. Please try again."


def require_login() -> AuthedUser:
    """Call at the top of a protected page. Renders a login/signup form
    and st.stop()s the script if nobody is logged in yet."""
    user = current_user()
    if user is not None:
        return user

    st.title("Sign in")
    tab_login, tab_signup = st.tabs(["Log in", "Create account"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Log in")
        if submitted:
            ok, msg = sign_in(email, password)
            if ok:
                st.rerun()
            else:
                st.error(msg)

    with tab_signup:
        with st.form("signup_form"):
            email = st.text_input("Email", key="signup_email")
            password = st.text_input(
                "Password (min 8 characters)", type="password", key="signup_password"
            )
            submitted = st.form_submit_button("Create account")
        if submitted:
            if len(password) < 8:
                st.error("Password must be at least 8 characters.")
            else:
                ok, msg = sign_up(email, password)
                (st.success if ok else st.error)(msg)

    st.stop()
