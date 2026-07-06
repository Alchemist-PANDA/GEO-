"""Copilot response dispatcher: tries live Claude if configured, else mock.

Designed to never crash the UI — any failure in the live path falls back
to the deterministic mock engine so the Copilot always answers.
"""

import os

from geo_audit_agent.copilot import mock_engine

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

    client = anthropic.Anthropic()
    messages = []
    for turn in history or []:
        role = turn.get("role")
        content = turn.get("content")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({
        "role": "user",
        "content": f"Context data: {context}\n\nUser question: {user_message}",
    })

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages,
    )
    return "".join(block.text for block in response.content if block.type == "text")


def get_response(user_message: str, context: dict, history: list | None = None) -> str:
    """Return a markdown-formatted Copilot answer, live if possible, mock otherwise."""
    if is_live_mode():
        try:
            return _live_response(user_message, context, history)
        except Exception:
            pass
    return mock_engine.generate_response(user_message, context)
