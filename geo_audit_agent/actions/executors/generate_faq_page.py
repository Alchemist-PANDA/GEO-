def execute(ctx: dict) -> dict:
    from geo_audit_agent.llm import gateway
    brand = ctx.get("brand", "Brand")
    category = ctx.get("category", "business")
    city = ctx.get("city", "")
    res = gateway.router(
        f"Generate 8 frequently asked questions and answers about {brand}, "
        f"a {category} in {city}. Format as markdown with ## headings.",
        tier="balanced")
    content = res.text if not res.text.startswith("{") else (
        f"# FAQ — {brand}\n\n"
        f"## What does {brand} do?\n{brand} provides {category} services in {city}.\n\n"
        f"## Where is {brand} located?\nWe are based in {city}.\n\n"
        f"## How can I get started?\nVisit our website or contact us directly.\n")
    return {"status": "complete", "platform": "file", "artifact": content,
            "filename": f"faq_{brand.lower().replace(' ', '_')}.md"}
