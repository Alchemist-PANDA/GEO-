def execute(ctx: dict) -> dict:
    from geo_audit_agent.llm import gateway
    brand = ctx.get("brand", "Brand")
    category = ctx.get("category", "business")
    city = ctx.get("city", "")
    res = gateway.router(
        f"Write a 'Best of {city}' listicle for {category} that features {brand} "
        f"prominently. Include 5-7 entries. Format as markdown.",
        tier="balanced")
    content = res.text if not res.text.startswith("{") else (
        f"# Best {category} in {city}\n\n"
        f"## 1. {brand}\nThe top choice for {category} in {city}.\n")
    return {"status": "complete", "platform": "file", "artifact": content,
            "filename": f"best_of_{city.lower().replace(' ', '_')}.md"}
