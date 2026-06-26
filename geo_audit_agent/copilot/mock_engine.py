import asyncio
import json
import uuid
from typing import AsyncIterator, Dict, Any
from sqlmodel import Session

class MockCopilotEngine:
    async def stream_chat(
        self,
        conversation_id: str,
        user_message: str,
        context: Dict[str, Any],
        db_session: Session,
        save_msg_func: Any  # Pass the save_msg function from engine.py
    ) -> AsyncIterator[Dict[str, Any]]:
        # Simulate processing delay
        await asyncio.sleep(0.5)

        msg_lower = user_message.lower()
        response = ""
        chart_data = None
        
        # Check context for "Explain This"
        chart_title = context.get("chart_title")
        chart_summary = context.get("chart_data")
        
        if chart_title and chart_summary and "explain" in msg_lower:
            response = f"This chart shows your '{chart_title}'. Here is the data summary: {chart_summary}. Based on this trend, you've seen a +17 gain recently, likely correlating with your recent FAQ schema deployment."
            # Generate a mock chart based on the fact that they clicked a chart
            chart_data = {
                "data": [{"x": ["Last Week", "This Week"], "y": [50, 75], "type": "bar", "marker": {"color": "#7C3AED"}}],
                "layout": {"title": f"Copilot Generated: {chart_title}"}
            }
        elif any(word in msg_lower for word in ["visibility", "score", "trend"]):
            response = "Your current Brand Visibility is 68%, up 5% from last month. ChatGPT drives 86% of your visibility, while Claude lags at 34%. The trend is upward with 'Fast' acceleration."
        elif any(word in msg_lower for word in ["competitor", "mcdonald's", "winning"]):
            response = "McDonald's leads on Authority (92%) and Schema (95%). You trail by 16 points in Authority and 6 points in Entities. Focus on building backlinks to close the gap."
        elif any(word in msg_lower for word in ["fix", "recommend", "action"]):
            response = "Top priority: Add FAQ schema (+12% visibility, 2 hours). Next: Build 10 backlinks (+8%, 20 hours)."
        elif any(word in msg_lower for word in ["chart", "explain this"]):
            response = "This chart shows your Brand Visibility trend over 30 days. You started at 54% and reached 71% (a +17 gain). The sharp rise between June 20-24 likely correlates with your recent FAQ schema deployment."
            # Optionally mock a chart
            chart_data = {
                "data": [{"x": ["Jun 19", "Jun 20", "Jun 26"], "y": [54, 58, 71], "type": "scatter", "mode": "lines+markers"}],
                "layout": {"title": "Mock Visibility Trend"}
            }
        elif "platform" in msg_lower:
            response = "Your strongest platform is ChatGPT (86%), followed by Perplexity (84%) and Mistral (73%). DeepSeek (40%) and Claude (34%) need urgent improvement."
        else:
            response = "I'm your GEO analyst (Mock Mode). Ask about visibility, competitors, recommendations, or specific charts. I can also simulate 'what-if' scenarios."

        # Save user message
        save_msg_func(conversation_id, "user", user_message, 0, db_session)

        # Stream response
        for chunk in response.split():
            yield {"type": "text", "content": chunk + " "}
            await asyncio.sleep(0.02)
        
        if chart_data:
            yield {"type": "chart", "content": json.dumps(chart_data)}

        # Save assistant message
        artifacts = {"chart": json.dumps(chart_data)} if chart_data else {}
        save_msg_func(conversation_id, "assistant", response, 0, db_session, artifacts=artifacts)
        
        # We need the conversation to return the title at the end
        from geo_audit_agent.db.models import CopilotConversation
        conversation = db_session.get(CopilotConversation, uuid.UUID(conversation_id))
        
        yield {"type": "done", "conversation_id": conversation_id, "title": conversation.title if conversation else "Mock Chat"}
