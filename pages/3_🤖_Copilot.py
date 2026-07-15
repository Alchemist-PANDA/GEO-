import uuid

import plotly.io as pio
import streamlit as st

from geo_audit_agent.copilot import engine
from geo_audit_agent.copilot.context import build_context
from geo_audit_agent.ui.access import require_user_or_demo
from geo_audit_agent.ui.theme import apply_theme, render_empty, render_page_header

st.set_page_config(page_title="GEO Copilot", page_icon="◉", layout="wide")
apply_theme()
user = require_user_or_demo()

if "copilot_conversations" not in st.session_state:
    st.session_state.copilot_conversations = []
if "copilot_active_conversation_id" not in st.session_state:
    st.session_state.copilot_active_conversation_id = None
if "copilot_confirm_clear" not in st.session_state:
    st.session_state.copilot_confirm_clear = False


def _new_conversation(title="New conversation", pinned_chart=None):
    conv = {
        "id": str(uuid.uuid4()),
        "title": title,
        "pinned_chart": pinned_chart,
        "messages": [],
    }
    st.session_state.copilot_conversations.insert(0, conv)
    st.session_state.copilot_active_conversation_id = conv["id"]
    return conv


def _get_active_conversation():
    active_id = st.session_state.copilot_active_conversation_id
    for conv in st.session_state.copilot_conversations:
        if conv["id"] == active_id:
            return conv
    return None


def _ask(conv, user_message: str):
    conv["messages"].append({"role": "user", "content": user_message})
    context = build_context()
    if conv.get("pinned_chart"):
        context["chart_title"] = conv["pinned_chart"].get("title")
        context["fig_json"] = conv["pinned_chart"].get("fig_json")
    history = [{"role": m["role"], "content": m["content"]} for m in conv["messages"][:-1]]
    answer = engine.get_response(user_message, context, history=history)
    conv["messages"].append({"role": "assistant", "content": answer})
    if conv["title"] == "New conversation" and len(conv["messages"]) <= 2:
        conv["title"] = user_message[:40] + ("…" if len(user_message) > 40 else "")


pending_context = st.session_state.pop("copilot_context", None)
pending_ask = st.session_state.pop("copilot_auto_ask", None)
if pending_context is not None or pending_ask:
    pinned_chart = None
    if pending_context and pending_context.get("fig_json"):
        pinned_chart = {
            "title": pending_context.get("chart_title", "Chart"),
            "fig_json": pending_context["fig_json"],
        }
    conv = _new_conversation(
        title=pending_context.get("chart_title", "New conversation") if pending_context else "New conversation",
        pinned_chart=pinned_chart,
    )
    _ask(conv, pending_ask or f"Explain this chart: {pending_context.get('chart_title', '')}")

active_conv = _get_active_conversation()
if active_conv is None and st.session_state.copilot_conversations:
    active_conv = st.session_state.copilot_conversations[0]
    st.session_state.copilot_active_conversation_id = active_conv["id"]

st.markdown(
    """
    <style>
    [data-testid="stChatMessage"] { border-radius:16px; border:1px solid rgba(17,24,39,.07); padding:.4rem .7rem; }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) { background:#f4f3ff; }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) { background:rgba(255,255,255,.92); }
    </style>
    """,
    unsafe_allow_html=True,
)

render_page_header(
    "COPILOT",
    "GEO Copilot",
    "Ask questions about the selected audit. Answers are grounded in the evidence available in the active workspace.",
)

history_col, chat_col = st.columns([3, 7], gap="large")

with history_col:
    st.markdown("### Conversations")
    if st.button("New conversation", use_container_width=True, type="primary"):
        _new_conversation()
        st.rerun()

    if not st.session_state.copilot_confirm_clear:
        if st.button("Clear conversation history", use_container_width=True):
            st.session_state.copilot_confirm_clear = True
            st.rerun()
    else:
        st.warning("Delete all conversations from this session?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Delete all", use_container_width=True, type="primary"):
                st.session_state.copilot_conversations = []
                st.session_state.copilot_active_conversation_id = None
                st.session_state.copilot_confirm_clear = False
                st.rerun()
        with c2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.copilot_confirm_clear = False
                st.rerun()

    st.divider()
    if not st.session_state.copilot_conversations:
        st.caption("No saved conversations in this session.")
    for conv in st.session_state.copilot_conversations:
        is_active = active_conv and conv["id"] == active_conv["id"]
        label = ("Pinned · " if conv.get("pinned_chart") else "") + conv["title"]
        if st.button(
            label,
            key=f"hist_{conv['id']}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state.copilot_active_conversation_id = conv["id"]
            st.rerun()

with chat_col:
    if active_conv is None:
        render_empty(
            "＋",
            "Start an evidence-grounded conversation",
            "Create a conversation or choose a quick question. Run an audit first for brand-specific answers.",
        )
        st.markdown("#### Suggested questions")
        qa_cols = st.columns(4)
        quick_actions = [
            ("Current score", "What is my current GEO score and how am I doing?"),
            ("Priority fixes", "What should I fix first to improve my score?"),
            ("Competitors", "Show me the competitive landscape"),
            ("Visibility", "Where am I visible across AI platforms?"),
        ]
        for col, (label, prompt) in zip(qa_cols, quick_actions, strict=False):
            with col:
                if st.button(label, use_container_width=True, key=f"qa_{label}"):
                    conv = _new_conversation()
                    _ask(conv, prompt)
                    st.rerun()
    else:
        pinned = active_conv.get("pinned_chart")
        if pinned and pinned.get("fig_json"):
            st.markdown(f"**Pinned evidence: {pinned['title']}**")
            try:
                fig = pio.from_json(pinned["fig_json"])
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True, key=f"pinned_{active_conv['id']}")
            except Exception:
                st.caption(f"Chart: {pinned['title']}")
            st.divider()

        for msg in active_conv["messages"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        st.markdown("##### Follow-up questions")
        fq_cols = st.columns(4)
        followups = [
            ("Score", "What is my GEO score?"),
            ("Fixes", "What should I fix first?"),
            ("Compare", "Compare me against competitors"),
            ("Trends", "Explain my visibility trend"),
        ]
        for col, (label, prompt) in zip(fq_cols, followups, strict=False):
            with col:
                if st.button(label, use_container_width=True, key=f"fq_{active_conv['id']}_{label}"):
                    _ask(active_conv, prompt)
                    st.rerun()

        user_input = st.chat_input("Ask about the selected audit evidence…")
        if user_input:
            _ask(active_conv, user_input)
            st.rerun()

st.divider()
if st.button("Return to dashboard"):
    st.switch_page("dashboard.py")
