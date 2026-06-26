import os
import json
import uuid
import logging
from datetime import datetime
from typing import AsyncIterator, Dict, Any, List, Optional
import anthropic
from sqlmodel import Session

from geo_audit_agent.db.models import CopilotConversation, CopilotMessage
from geo_audit_agent.copilot.chart_builder import build_chart

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are BrandSight Copilot, an AI assistant for Generative Engine Optimization (GEO).
You help users understand their brand's visibility across AI platforms (ChatGPT, Perplexity, Gemini, etc.).

You have access to the user's current audit data, competitor scans, and GEO scores.
When answering questions:
- Be specific with numbers from their actual data.
- Suggest concrete actions with effort/impact estimates (Low/Medium/High).
- Reference specific metrics: GEO Score, Citation Rate, Content Depth, Schema Coverage, Platform Presence.
- When asked to visualize data, use the generate_chart tool.
- When a user asks about something on a different tab, use the suggest_navigation tool.
- When a user asks to look up specific data, use the lookup_data tool.

Always be professional, concise, and structured in your explanations."""

TOOLS: List[Any] = [
    {
        "name": "generate_chart",
        "description": "Generate a Plotly chart from audit/competitor data. Use when the user asks for a visualization, comparison chart, trend graph, or any visual representation of data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "chart_type": {
                    "type": "string",
                    "enum": ["bar", "radar", "line", "pie", "scatter", "heatmap"],
                    "description": "The type of Plotly chart to generate"
                },
                "title": {"type": "string", "description": "Chart title"},
                "data_source": {
                    "type": "string",
                    "enum": ["audit_scores", "competitor_comparison", "gap_analysis", "platform_breakdown", "trend"],
                    "description": "Which data set to pull from"
                },
                "metrics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Which metrics to include"
                }
            },
            "required": ["chart_type", "title", "data_source"]
        }
    },
    {
        "name": "suggest_navigation",
        "description": "Suggest the user navigate to a different tab for relevant information. Use when the answer involves data on another tab.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tab_name": {
                    "type": "string",
                    "enum": ["GEO Score", "Gap Matrix", "Remediation Plan", "Lift Simulator", "Live Ticker", "Competitor Intelligence", "Brand Visibility"],
                    "description": "Which tab to suggest"
                },
                "reason": {"type": "string", "description": "Why this tab is relevant"}
            },
            "required": ["tab_name", "reason"]
        }
    },
    {
        "name": "lookup_data",
        "description": "Look up specific data points from the current audit. Use to fetch exact numbers before answering.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query_type": {
                    "type": "string",
                    "enum": ["brand_scores", "competitor_scores", "gaps", "remediations", "platform_breakdown"],
                    "description": "What data to retrieve"
                }
            },
            "required": ["query_type"]
        }
    }
]

def build_context_message(context: Dict[str, Any]) -> str:
    """
    Format session context information into a system-injected context message.
    """
    return f"""[CURRENT SESSION CONTEXT]
Brand: {context.get('brand_name', 'Unknown')}
Category: {context.get('category', 'Unknown')}
City: {context.get('city', 'Unknown')}
Current Active Tab: {context.get('current_tab', 'GEO Score')}
GEO Score: {context.get('geo_score', 'N/A')}
Citation Rate: {context.get('citation_rate', 'N/A')}
Sentiment: {context.get('sentiment', 'N/A')}

Competitors: {json.dumps(context.get('competitors', []), indent=2)}
Gaps Identified (first 5): {json.dumps(context.get('gaps', [])[:5], indent=2)}
"""

def execute_tool(name: str, tool_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute tool call and return response structure.
    """
    if name == "generate_chart":
        chart_json = build_chart(
            chart_type=tool_input.get("chart_type", "bar"),
            title=tool_input.get("title", "Data Visualization"),
            data_source=tool_input.get("data_source", "competitor_comparison"),
            metrics=tool_input.get("metrics"),
            context=context
        )
        return {"status": "success", "chart_json": chart_json}

    elif name == "suggest_navigation":
        return {
            "status": "success",
            "tab": tool_input.get("tab_name"),
            "reason": tool_input.get("reason")
        }

    elif name == "lookup_data":
        query_type = tool_input.get("query_type")
        if query_type == "brand_scores":
            return {"status": "success", "data": {"geo_score": context.get("geo_score"), "citation_rate": context.get("citation_rate")}}
        elif query_type == "competitor_scores":
            return {"status": "success", "data": context.get("competitors", [])}
        elif query_type == "gaps":
            return {"status": "success", "data": context.get("gaps", [])[:10]}
        elif query_type == "remediations":
            return {"status": "success", "data": context.get("remediations", {})}
        elif query_type == "platform_breakdown":
            return {"status": "success", "data": context.get("brand_scores", {})}
        
        return {"status": "error", "message": "Unknown query type"}

    return {"status": "error", "message": f"Unknown tool: {name}"}

async def stream_chat(
    conversation_id: str,
    user_message: str,
    context: Dict[str, Any],
    db_session: Session
) -> AsyncIterator[Dict[str, Any]]:
    """
    Streams responses from Claude, handles tool use loop, and saves conversation to DB.
    """
    # 1. Fetch conversation history
    conversation = db_session.get(CopilotConversation, uuid.UUID(conversation_id))
    if not conversation:
        raise ValueError(f"Conversation {conversation_id} not found")

    db_messages = conversation.messages
    formatted_messages: List[Dict[str, Any]] = []
    
    # 2. Build history
    for msg in db_messages:
        formatted_messages.append({
            "role": msg.role,
            "content": msg.content
        })

    # Append new user message with full context
    context_prefix = build_context_message(context)
    full_user_content = f"{context_prefix}\n\nUser Question: {user_message}"
    formatted_messages.append({
        "role": "user",
        "content": full_user_content
    })

    # Compact history if too long
    formatted_messages = compact_history(formatted_messages)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        # Mock mode fallback if no API key is present
        yield {"type": "text", "content": "*(API Key missing. Running in demo mode)*\n\nBased on your GEO Score of " + str(context.get("geo_score", 72)) + ", you have strong platform presence but can optimize Authority."}
        # Save user & assistant messages
        save_msg(conversation_id, "user", user_message, 0, db_session)
        save_msg(conversation_id, "assistant", "Based on your GEO Score, you have strong platform presence but can optimize Authority.", 0, db_session)
        yield {"type": "done", "conversation_id": conversation_id, "title": conversation.title}
        return

    client = anthropic.Anthropic(api_key=api_key)
    model = os.getenv("COPILOT_MODEL", "claude-haiku-4-5")
    max_tokens = int(os.getenv("COPILOT_MAX_TOKENS", "2048"))

    assistant_response = ""
    collected_artifacts = {}
    tokens_used = 0

    while True:
        with client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=formatted_messages,  # type: ignore
        ) as stream:
            for event in stream:
                if event.type == "content_block_delta" and event.delta.type == "text_delta":
                    assistant_response += event.delta.text
                    yield {"type": "text", "content": event.delta.text}
            
            final_message = stream.get_final_message()
            tokens_used += getattr(final_message.usage, "input_tokens", 0) + getattr(final_message.usage, "output_tokens", 0)

        tool_blocks = [b for b in final_message.content if b.type == "tool_use"]
        if not tool_blocks:
            break

        # Append assistant tool use message
        formatted_messages.append({"role": "assistant", "content": final_message.content})

        for tool_block in tool_blocks:
            result = execute_tool(tool_block.name, tool_block.input, context)
            
            # Append tool result
            formatted_messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": json.dumps(result)
                    }
                ]
            })

            if tool_block.name == "generate_chart" and result.get("status") == "success":
                collected_artifacts["chart"] = result.get("chart_json")
                yield {"type": "chart", "content": result.get("chart_json")}
            elif tool_block.name == "suggest_navigation" and result.get("status") == "success":
                collected_artifacts["navigation"] = result
                yield {"type": "navigation", "content": result}

    # Save messages to database
    save_msg(conversation_id, "user", user_message, 0, db_session)
    save_msg(conversation_id, "assistant", assistant_response, tokens_used, db_session, artifacts=collected_artifacts)

    # Auto-title generation after the first exchange
    if len(conversation.messages) <= 3:
        new_title = auto_title(user_message, api_key)
        if new_title:
            conversation.title = new_title
            conversation.updated_at = datetime.utcnow()
            db_session.add(conversation)
            db_session.commit()
            yield {"type": "title", "content": new_title}

    yield {"type": "done", "conversation_id": conversation_id, "title": conversation.title}

def save_msg(conversation_id: str, role: str, content: str, tokens: int, db_session: Session, artifacts: Optional[dict] = None):
    msg = CopilotMessage(
        conversation_id=uuid.UUID(conversation_id),
        role=role,
        content=content,
        tokens_used=tokens,
        artifacts=artifacts or {},
        created_at=datetime.utcnow()
    )
    db_session.add(msg)
    db_session.commit()

def auto_title(first_message: str, api_key: str) -> Optional[str]:
    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=os.getenv("COPILOT_MODEL", "claude-haiku-4-5"),
            max_tokens=20,
            messages=[{"role": "user", "content": f"Generate a 3-5 word title for a conversation that starts with: '{first_message[:200]}'. Return only the title, no quotes."}]
        )
        first_content = response.content[0]
        return getattr(first_content, "text", "").strip()
    except Exception as e:
        logger.error(f"Error generating auto title: {e}")
        return None

def compact_history(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if len(messages) <= 20:
        return messages

    # Keep first context message and the last 10 messages
    context_msg = messages[0]
    recent_messages = messages[-10:]
    
    # Placeholder summary statement representing compacted messages
    compacted = [
        context_msg,
        {"role": "user", "content": "[Older parts of conversation compacted to save memory]"},
        {"role": "assistant", "content": "Understood, I am retaining the context of our previous discussion."},
        *recent_messages
    ]
    return compacted
