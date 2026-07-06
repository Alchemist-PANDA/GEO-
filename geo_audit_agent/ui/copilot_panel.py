import streamlit as st
import uuid
import asyncio
import plotly.io
from sqlmodel import Session, select, SQLModel
from geo_audit_agent.db.session import engine

from geo_audit_agent.db.models import UserProfile, CopilotConversation
from geo_audit_agent.copilot.context import build_copilot_context
from geo_audit_agent.copilot.engine import stream_chat

# Ensure tables exist (critical for Streamlit Cloud with local sqlite)
SQLModel.metadata.create_all(engine)

def get_db_session():
    return Session(engine)

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
    """Render the side panel as a floating CSS overlay."""
    is_open = st.session_state.get("copilot_open", False)
    
    # User ID Resolution
    user_id = get_or_create_sidebar_user()

    # Load / Create active conversation
    if "panel_conv_id" not in st.session_state or st.session_state.panel_conv_id is None:
        with get_db_session() as session:
            conv = CopilotConversation(
                user_id=user_id,
                title="Floating Chat",
                context_snapshot={}
            )
            session.add(conv)
            session.commit()
            session.refresh(conv)
            st.session_state.panel_conv_id = str(conv.id)

    panel_conv_id = st.session_state.panel_conv_id

    # CSS to make the container float and toggle visibility
    transform = "translateX(0)" if is_open else "translateX(100%)"
    st.markdown(f"""
        <style>
        /* Target the specific container using the anchor */
        div[data-testid="stVerticalBlock"]:has(> div > #copilot-anchor) {{
            position: fixed !important;
            top: 0 !important;
            right: 0 !important;
            width: 420px !important;
            height: 100vh !important;
            background: rgba(255,255,255,0.98) !important;
            backdrop-filter: blur(12px) !important;
            box-shadow: -4px 0 20px rgba(0,0,0,0.1) !important;
            border-left: 1px solid #E2E8F0 !important;
            padding: 20px !important;
            padding-bottom: 80px !important;
            z-index: 99999 !important;
            overflow-y: auto !important;
            transition: transform 0.3s ease-in-out !important;
            transform: {transform} !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    # Always render the container, CSS will hide it if not open
    with st.container():
        st.markdown("<div id='copilot-anchor'></div>", unsafe_allow_html=True)
        
        # Header and Close Button
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown("<h3 style='background: linear-gradient(135deg, #7C3AED 0%, #3B82F6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 700; margin: 0;'>🤖 AI Copilot</h3>", unsafe_allow_html=True)
        with col2:
            if st.button("✕", key="close_panel_btn", help="Close Copilot"):
                st.session_state["copilot_open"] = False
                st.rerun()
                
        st.markdown("---")

        # Fetch conversation messages
        with get_db_session() as session:
            conversation = session.get(CopilotConversation, uuid.UUID(panel_conv_id))
            messages = conversation.messages if conversation else []

            # Message container
            for msg in messages:
                role_label = "👤 You" if msg.role == "user" else "🤖 Copilot"
                st.markdown(f"**{role_label}**")
                st.markdown(msg.content)
                
                # Show charts if any
                if msg.artifacts and "chart" in msg.artifacts:
                    try:
                        fig = plotly.io.from_json(msg.artifacts["chart"])
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception:
                        pass
                st.markdown("---")

        # Handle pending explanation prompts from "Explain This" buttons
        pending_prompt = st.session_state.pop("copilot_pending_message", None)
        
        # Text input
        user_input = st.chat_input("Ask about your brand visibility...", key="panel_input")
        
        prompt_to_send = pending_prompt or user_input
        
        if prompt_to_send:
            # Display immediately
            st.markdown("**👤 You**")
            st.markdown(prompt_to_send)
            
            ctx = build_copilot_context(st.session_state)
            
            # Stream response
            st.markdown("**🤖 Copilot**")
            response_placeholder = st.empty()
            chart_placeholder = st.empty()
            
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
                except Exception:
                    pass
                    
            st.rerun()
