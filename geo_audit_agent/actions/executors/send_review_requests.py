def execute(ctx: dict) -> dict:
    from geo_audit_agent.geo_remediation_tools import generate_review_template
    brand = ctx.get("brand", "Brand")
    category = ctx.get("category", "business")
    city = ctx.get("city", "")
    template = generate_review_template(brand_name=brand, category=category, city=city, rating=4.5)
    return {"status": "fallback", "platform": "Email", "artifact": template,
            "instructions": "Send this email template to recent customers to collect reviews."}
