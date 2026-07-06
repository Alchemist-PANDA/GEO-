def execute(ctx: dict) -> dict:
    from geo_audit_agent.llm import gateway
    brand = ctx.get("brand", "Brand")
    res = gateway.router(
        f"Draft 3 professional review response templates for {brand}: "
        f"one for a positive review, one for a neutral review, and one for a negative review. "
        f"Format as markdown with ## headings.", tier="balanced")
    content = res.text if not res.text.startswith("{") else (
        f"# Review Response Templates — {brand}\n\n"
        f"## Positive Review Response\nThank you for your kind words!\n\n"
        f"## Neutral Review Response\nThank you for your feedback.\n\n"
        f"## Negative Review Response\nWe're sorry to hear about your experience.\n")
    return {"status": "complete", "platform": "file", "artifact": content,
            "filename": f"review_responses_{brand.lower().replace(' ', '_')}.md"}
