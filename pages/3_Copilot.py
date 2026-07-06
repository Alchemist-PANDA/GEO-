import streamlit as st
import uuid
import os
import asyncio
import plotly.io
from sqlmodel import Session, select, desc, SQLModel
from geo_audit_agent.db.session import engine
from geo_audit_agent.db.models import UserProfile, CopilotConversation
from geo_audit_agent.copilot.context import build_copilot_context
from geo_audit_agent.copilot.engine import stream_chat

SQLModel.metadata.create_all(engine)

def get_db_session():
    return Session(engine)

# Load CSS
def load_css(file_name="style.css"):
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Page Setup
st.set_page_config(
    page_title="GEO Copilot • BrandSight",
    page_icon="🤖",
    layout="wide"
)

load_css("style.css")

# Ensure default user profile exists in database
def ensure_default_user() -> uuid.UUID:
    with get_db_session() as session:
        statement = select(UserProfile)
        user = session.exec(statement).first()
        if not user:
            # Create a mock user profile
            mock_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
            user = UserProfile(
                id=mock_id,
                email="demo@brandsightgeo.com",
                display_name="Demo User",
                plan_tier="enterprise",
                monthly_audit_quota=100
            )
            session.add(user)
            session.commit()
            session.refresh(user)
        return user.id

USER_ID = ensure_default_user()

# Session State
if "active_conv_id" not in st.session_state:
    st.session_state.active_conv_id = None

# Sidebar History Panel
def render_history_sidebar():
    st.sidebar.markdown("<h2 style='text-align: center; background: linear-gradient(135deg, #7C3AED 0%, #3B82F6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>🤖 GEO Copilot</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    if st.sidebar.button("➕ New Chat", use_container_width=True):
        st.session_state.active_conv_id = None
        st.rerun()

    st.sidebar.markdown("### Conversation History")
    
    with get_db_session() as session:
        statement = select(CopilotConversation).where(
            CopilotConversation.user_id == USER_ID
        ).order_by(desc(CopilotConversation.updated_at))
        conversations = session.exec(statement).all()

        if not conversations:
            st.sidebar.caption("No conversations yet.")
        
        for conv in conversations:
            conv_id_str = str(conv.id)
            # Accentuate active item
            is_active = (st.session_state.active_conv_id == conv_id_str)
            title_prefix = "💬 " if not is_active else "👉 "
            
            col1, col2 = st.sidebar.columns([4, 1])
            with col1:
                if st.button(f"{title_prefix}{conv.title}", key=f"select_{conv_id_str}", use_container_width=True):
                    st.session_state.active_conv_id = conv_id_str
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{conv_id_str}"):
                    session.delete(conv)
                    session.commit()
                    if st.session_state.active_conv_id == conv_id_str:
                        st.session_state.active_conv_id = None
                    st.rerun()

        if conversations:
            st.sidebar.markdown("---")
            if st.sidebar.button("🧹 Clear All Chats", use_container_width=True):
                for conv in conversations:
                    session.delete(conv)
                session.commit()
                st.session_state.active_conv_id = None
                st.rerun()

render_history_sidebar()

# Main Chat Window
st.title("AI Copilot")
st.markdown("Your interactive command center for Generative Engine Optimization. Ask questions about your brand visibility, competitor strategies, or action plans.")

# Get or create active conversation
def get_or_create_conversation() -> str:
    if st.session_state.active_conv_id:
        return st.session_state.active_conv_id
        
    with get_db_session() as session:
        conv = CopilotConversation(
            user_id=USER_ID,
            title="New conversation",
            context_snapshot={}
        )
        session.add(conv)
        session.commit()
        session.refresh(conv)
        st.session_state.active_conv_id = str(conv.id)
        return st.session_state.active_conv_id

active_id = get_or_create_conversation()

# Load current conversation messages
with get_db_session() as session:
    conversation = session.get(CopilotConversation, uuid.UUID(active_id))
    messages = conversation.messages if conversation else []

    # Display past messages
    for msg in messages:
        with st.chat_message(msg.role):
            st.write(msg.content)
            
            # Render charts if present in artifacts
            if msg.artifacts and "chart" in msg.artifacts:
                try:
                    fig = plotly.io.from_json(msg.artifacts["chart"])
                    st.plotly_chart(fig, use_container_width=True)
                except Exception:
                    print("Error loading chart from message artifacts")
            
            # Render navigation if present in artifacts
            if msg.artifacts and "navigation" in msg.artifacts:
                nav = msg.artifacts["navigation"]
                st.info(f"💡 Suggestion: Navigate to the **{nav.get('tab')}** tab. Reason: {nav.get('reason')}")

# Chat Input
pending_prompt = st.session_state.pop("copilot_pending_message", None)
user_query = st.chat_input("Ask about your brand visibility...")

prompt_to_send = pending_prompt or user_query

if prompt_to_send:
    # 1. Display user query immediately
    with st.chat_message("user"):
        st.write(prompt_to_send)

    # 2. Build context
    ctx = build_copilot_context(st.session_state)

    # 3. Stream assistant response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        chart_placeholder = st.empty()
        nav_placeholder = st.empty()
        
        state = {
            "full_text": "",
            "plotly_json": None,
            "nav_info": None
        }

        # Execute stream async-to-sync
        async def run_stream():
            with get_db_session() as session:
                async for event in stream_chat(active_id, prompt_to_send, ctx, session):
                    if event["type"] == "text":
                        state["full_text"] += event["content"]
                        response_placeholder.write(state["full_text"])
                    elif event["type"] == "chart":
                        state["plotly_json"] = event["content"]
                    elif event["type"] == "navigation":
                        state["nav_info"] = event["content"]

        asyncio.run(run_stream())

        # Render any generated chart or navigation tips
        if state["plotly_json"]:
            try:
                fig = plotly.io.from_json(state["plotly_json"])
                chart_placeholder.plotly_chart(fig, use_container_width=True)
            except Exception:
                print("Plotly load error")
        if state["nav_info"]:
            nav_placeholder.info(f"💡 Suggestion: Navigate to the **{state['nav_info'].get('tab')}** tab. Reason: {state['nav_info'].get('reason')}")

    # Rerun to refresh conversation list titles and order
    st.rerun()
