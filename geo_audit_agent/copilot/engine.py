"""Copilot response dispatcher with explicit live and demo behavior."""

import logging
import os

from geo_audit_agent.copilot import mock_engine

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the GEO Copilot, embedded inside a brand visibility \
dashboard. You help users understand their AI-search visibility data, \
competitor standing, and recommended fixes. Be conversational and specific \
— use the real numbers given in context, not generic advice. Format with \
markdown headings, bullet points, and bold for key numbers. If a chart is \
in context, explain it using its actual data."""


def is_live_mode() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY"))


def _live_response(user_message: str, context: dict, history: list | None) -> str:
    import anthropic
    from anthropic.types import MessageParam

    client = anthropic.Anthropic()
    messages: list[MessageParam] = []
    for turn in history or []:
        role = turn.get("role")
        content = turn.get("content")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})  # type: ignore[typeddict-item]
    messages.append({
        "role": "user",
        "content": f"Context data: {context}\n\nUser question: {user_message}",
    })

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages,  # type: ignore[arg-type]
    )
    return "".join(block.text for block in response.content if block.type == "text")


def get_response(user_message: str, context: dict, history: list | None = None) -> str:
    """Return a live answer, or an explicitly disclosed offline demo answer."""
    if is_live_mode():
        try:
            return _live_response(user_message, context, history)
        except Exception as e:
            logger.warning("Live Copilot failed without demo fallback: %s", type(e).__name__)
            return "Live Copilot is temporarily unavailable. No simulated answer was substituted."
    return "**DEMO ASSISTANT — not a live model response**\n\n" + mock_engine.generate_response(user_message, context)


def compact_history(history: list, max_messages: int = 15) -> list:
    """Keep the first message (which is usually the context / system-like message)
    and keep the latest (max_messages - 1) messages.
    """
    if not history:
        return []
    if len(history) <= max_messages:
        return history
    return [history[0]] + history[-(max_messages - 1):]


async def stream_chat(conversation_id: str, message: str, context: dict, session):
    """Asynchronous generator to stream chat events and persist them to DB."""
    import asyncio
    import uuid
    from datetime import datetime

    from geo_audit_agent.db.models import CopilotConversation, CopilotMessage

    # 1. Save user message to database
    user_msg = CopilotMessage(
        conversation_id=uuid.UUID(conversation_id),
        role="user",
        content=message,
        tokens_used=len(message) // 4
    )
    session.add(user_msg)

    # Update conversation's updated_at
    conv = session.get(CopilotConversation, uuid.UUID(conversation_id))
    if conv:
        conv.updated_at = datetime.utcnow()
        session.add(conv)
    session.commit()

    # 2. Get history from DB
    history = []
    if conv:
        history = [{"role": m.role, "content": m.content} for m in conv.messages[:-1]]

    # 3. Get response from engine
    response = get_response(message, context, history)

    # 4. Save assistant message to database
    assistant_msg = CopilotMessage(
        conversation_id=uuid.UUID(conversation_id),
        role="assistant",
        content=response,
        tokens_used=len(response) // 4
    )
    session.add(assistant_msg)
    session.commit()

    # 5. Stream the response chunks to simulate streaming
    chunks = [response[i:i+8] for i in range(0, len(response), 8)] if response else [""]
    for chunk in chunks:
        yield {"type": "text", "content": chunk}
        await asyncio.sleep(0.01)

