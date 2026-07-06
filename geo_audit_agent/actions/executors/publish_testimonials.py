def execute(ctx: dict) -> dict:
    brand = ctx.get("brand", "Brand")
    category = ctx.get("category", "business")
    content = (f"# Customer Testimonials — {brand}\n\n"
               f"> \"{brand} transformed our {category} experience. Highly recommended!\"\n"
               f"> — Satisfied Customer\n\n"
               f"> \"Professional service and great results.\"\n"
               f"> — Happy Client\n")
    return {"status": "fallback", "platform": "WordPress", "artifact": content,
            "instructions": "Add these testimonials to your website's testimonials page."}
