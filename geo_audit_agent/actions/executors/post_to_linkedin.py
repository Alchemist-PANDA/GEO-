def execute(ctx: dict) -> dict:
    from geo_audit_agent.llm import gateway
    brand = ctx.get("brand", "Brand")
    category = ctx.get("category", "business")
    city = ctx.get("city", "")
    res = gateway.router(
        f"Write a LinkedIn post for {brand}, a {category} in {city}. "
        f"Professional tone, under 200 words, include relevant hashtags.", tier="balanced")
    content = res.text if not res.text.startswith("{") else (
        f"Excited to share how {brand} is innovating in {city}'s {category} industry! "
        f"Our commitment to excellence drives everything we do.\n\n"
        f"#GEO #{category.replace(' ', '')} #{city.replace(' ', '')}")
    return {"status": "fallback", "platform": "LinkedIn", "artifact": content,
            "instructions": "Post this content to your LinkedIn company page."}
