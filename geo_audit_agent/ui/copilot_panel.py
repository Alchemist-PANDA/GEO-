import streamlit as st
import uuid
import asyncio
import plotly.io
import os
from datetime import datetime
from sqlmodel import Session, create_engine, select

from geo_audit_agent.db.models import UserProfile, CopilotConversation, CopilotMessage
from geo_audit_agent.copilot.context import build_copilot_context
from geo_audit_agent.copilot.engine import stream_chat

# Database Setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///geo_saas.db")
db_engine = create_engine(DATABASE_URL)

# Ensure tables exist (critical for Streamlit Cloud with local sqlite)
from sqlmodel import SQLModel
SQLModel.metadata.create_all(db_engine)

def get_db_session():
    return Session(db_engine)

def get_or_create_sidebar_user() -> uuid.UUID:
    with get_db_session() as session:
        user = session.exec(select(UserProfile)).first()
        if not user:
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

def render_copilot_panel():
    """Render the side panel inside Streamlit's sidebar or as an overlay."""
    if not st.session_state.get("copilot_open", False):
        return

    # User ID Resolution
    user_id = get_or_create_sidebar_user()

    # Load / Create active conversation
    if "panel_conv_id" not in st.session_state or st.session_state.panel_conv_id is None:
        with get_db_session() as session:
            conv = CopilotConversation(
                user_id=user_id,
                title="Sidebar Chat",
                context_snapshot={}
            )
            session.add(conv)
            session.commit()
            session.refresh(conv)
            st.session_state.panel_conv_id = str(conv.id)

    panel_conv_id = st.session_state.panel_conv_id

    st.sidebar.markdown("---")
    st.sidebar.markdown("<h3 style='background: linear-gradient(135deg, #7C3AED 0%, #3B82F6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 700;'>🤖 AI Copilot Panel</h3>", unsafe_allow_html=True)
    
    # Close button
    if st.sidebar.button("✕ Close Panel", key="close_panel_btn", use_container_width=True):
        st.session_state["copilot_open"] = False
        st.rerun()

    # Fetch conversation messages
    with get_db_session() as session:
        conversation = session.get(CopilotConversation, uuid.UUID(panel_conv_id))
        messages = conversation.messages if conversation else []

        # Message container in sidebar
        for msg in messages:
            role_label = "👤 You" if msg.role == "user" else "🤖 Copilot"
            st.sidebar.markdown(f"**{role_label}**")
            st.sidebar.markdown(msg.content)
            
            # Show charts if any
            if msg.artifacts and "chart" in msg.artifacts:
                try:
                    fig = plotly.io.from_json(msg.artifacts["chart"])
                    st.sidebar.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    pass
            st.sidebar.markdown("---")

    # Handle pending explanation prompts from "Explain This" buttons
    pending_prompt = st.session_state.pop("copilot_pending_message", None)
    
    # Text input
    user_input = st.sidebar.chat_input("Ask about this dashboard...", key="panel_input")
    
    prompt_to_send = pending_prompt or user_input
    
    if prompt_to_send:
        # Display immediately in sidebar
        st.sidebar.markdown("**👤 You**")
        st.sidebar.markdown(prompt_to_send)
        
        ctx = build_copilot_context(st.session_state)
        
        # Stream response
        st.sidebar.markdown("**🤖 Copilot**")
        response_placeholder = st.sidebar.empty()
        chart_placeholder = st.sidebar.empty()
        
        full_text = ""
        plotly_json = None

        async def run_panel_stream():
            nonlocal full_text, plotly_json
            with get_db_session() as session:
                async for event in stream_chat(panel_conv_id, prompt_to_send, ctx, session):
                    if event["type"] == "text":
                        full_text += event["content"]
                        response_placeholder.write(full_text)
                    elif event["type"] == "chart":
                        plotly_json = event["content"]

        asyncio.run(run_panel_stream())

        if plotly_json:
            try:
                fig = plotly.io.from_json(plotly_json)
                chart_placeholder.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                pass
                
        st.rerun()
