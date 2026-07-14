def execute(ctx: dict) -> dict:
    from geo_audit_agent.llm import gateway
    brand = ctx.get("brand", "Brand")
    category = ctx.get("category", "business")
    city = ctx.get("city", "")
    res = gateway.router(
        f"Write a location-specific landing page for {brand}, a {category} in {city}. "
        f"Include local keywords, address section, and service area. Format as markdown.",
        tier="balanced")
    content = res.text if not res.text.startswith("{") else (
        f"# {brand} — {category} in {city}\n\n"
        f"## Serving {city} and Surrounding Areas\n"
        f"Find us at the heart of {city}.\n")
    return {"status": "complete", "platform": "file", "artifact": content,
            "filename": f"location_{city.lower().replace(' ', '_')}.md"}
