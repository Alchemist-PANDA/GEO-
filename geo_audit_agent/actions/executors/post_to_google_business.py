def execute(ctx: dict) -> dict:
    from geo_audit_agent.llm import gateway
    brand = ctx.get("brand", "Brand")
    category = ctx.get("category", "business")
    city = ctx.get("city", "")
    res = gateway.router(
        f"Write a Google Business Profile post for {brand}, a {category} in {city}. "
        f"Keep it under 300 words. Include a call to action.", tier="balanced")
    content = res.text if not res.text.startswith("{") else (
        f"Looking for the best {category} in {city}? {brand} has you covered! "
        f"Visit us today to learn more about our services.")
    return {"status": "fallback", "platform": "Google Business", "artifact": content,
            "instructions": "Post this content to your Google Business Profile."}
