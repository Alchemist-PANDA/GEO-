def execute(ctx: dict) -> dict:
    from geo_audit_agent.llm import gateway
    brand = ctx.get("brand", "Brand")
    category = ctx.get("category", "business")
    city = ctx.get("city", "")
    res = gateway.router(
        f"Write a comparison page for {brand} vs competitors in the {category} "
        f"space in {city}. Highlight unique strengths. Format as markdown.",
        tier="balanced")
    content = res.text if not res.text.startswith("{") else (
        f"# {brand} vs Competitors — {category} in {city}\n\n"
        f"## Why Choose {brand}?\n{brand} stands out in {city}'s {category} market.\n")
    return {"status": "complete", "platform": "file", "artifact": content,
            "filename": f"comparison_{brand.lower().replace(' ', '_')}.md"}
