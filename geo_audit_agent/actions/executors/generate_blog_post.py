def execute(ctx: dict) -> dict:
    from geo_audit_agent.llm import gateway
    brand = ctx.get("brand", "Brand")
    category = ctx.get("category", "business")
    city = ctx.get("city", "")
    res = gateway.router(
        f"Write a 600-word blog post about GEO visibility best practices for {brand}, "
        f"a {category} in {city}. Include actionable tips. Format as markdown.",
        tier="balanced")
    content = res.text if not res.text.startswith("{") else (
        f"# How {brand} Improves AI Visibility in {city}\n\n"
        f"As AI-powered search grows, {category} businesses like {brand} need to adapt.\n")
    return {"status": "complete", "platform": "file", "artifact": content,
            "filename": f"blog_{brand.lower().replace(' ', '_')}.md"}
