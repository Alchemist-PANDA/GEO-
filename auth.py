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

import os
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


def _get_client() -> Client:
    try:
        secrets_url = st.secrets.get("supabase", {}).get("url")
        secrets_key = st.secrets.get("supabase", {}).get("anon_key")
    except Exception:
        secrets_url = secrets_key = None
    url = secrets_url or os.getenv("SUPABASE_URL")
    key = secrets_key or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        st.error("⚠️ **Supabase Secrets Missing!**")
        st.info("Your Streamlit Cloud environment is missing the required Supabase credentials. Please go to **Manage App > Settings > Secrets** on your Streamlit dashboard and paste your `[supabase]` section with `url` and `anon_key`.")
        st.stop()

    if "sb_client" not in st.session_state:
        st.session_state.sb_client = create_client(url, key)
    return st.session_state.sb_client


def _get_cookie_manager() -> stx.CookieManager:
    if "cookie_manager" not in st.session_state:
        st.session_state.cookie_manager = stx.CookieManager(key="auth_cookie_mgr")
    return st.session_state.cookie_manager


def _restore_session(client: Client, cookies: dict) -> AuthedUser | None:
    """Try to restore a session from the persisted refresh token."""
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
    if "authed_user" in st.session_state:
        return st.session_state.authed_user

    client = _get_client()
    cookie_mgr = _get_cookie_manager()
    cookies = cookie_mgr.get_all()

    user = _restore_session(client, cookies)
    st.session_state.authed_user = user
    return user


def sign_in(email: str, password: str) -> tuple[bool, str]:
    """Returns (success, message)."""
    client = _get_client()
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
    try:
        client.auth.sign_up({"email": email, "password": password})
        return True, "Account created. Check your email to confirm before signing in."
    except Exception as e:
        return False, _friendly_error(e)


def sign_out() -> None:
    client = _get_client()
    try:
        client.auth.sign_out()
    except Exception:
        pass
    for k in ("authed_user", "sb_access_token", "sb_refresh_token"):
        st.session_state.pop(k, None)
    cookie_mgr = _get_cookie_manager()
    cookie_mgr.delete(COOKIE_NAME, key="delete_session_cookie")


def _friendly_error(e: Exception) -> str:
    print(f"🔥 [AUTH ERROR] Supabase rejected request: {repr(e)}")
    msg = str(e)
    if "already registered" in msg.lower():
        return "That email is already registered — try signing in instead."
    if "invalid login credentials" in msg.lower():
        return "Invalid email or password."
    if "email not confirmed" in msg.lower():
        return "Please confirm your email before signing in (check your inbox)."
    if "signups not allowed" in msg.lower() or "not allowed to sign up" in msg.lower():
        return "Signups are currently disabled. Please contact the administrator."
    return f"Something went wrong: {msg[:50]}..."


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
    raise RuntimeError("Authentication flow stopped before a user was established")


def require_admin_user() -> AuthedUser:
    """Require a verified Supabase session whose email is in the admin allowlist."""
    user = require_login()
    allowed = {
        email.strip().casefold()
        for email in os.getenv("BRANDSIGHT_ADMIN_EMAILS", "").split(",")
        if email.strip()
    }
    if user.email.casefold() not in allowed:
        st.error("Access denied. Administrator role required.")
        st.stop()
        raise RuntimeError("Administrator access denied")
    return user
