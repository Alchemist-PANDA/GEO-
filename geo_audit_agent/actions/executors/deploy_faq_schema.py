def execute(ctx: dict) -> dict:
    import json
    brand = ctx.get("brand", "Brand")
    category = ctx.get("category", "business")
    faqs = [
        {"q": f"What services does {brand} offer?", "a": f"{brand} offers comprehensive {category} services."},
        {"q": f"Where is {brand} located?", "a": f"{brand} is located in {ctx.get('city', 'your city')}."},
        {"q": f"How can I contact {brand}?", "a": "Visit our website or call us for more information."},
    ]
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": f["q"],
                        "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faqs]
    }
    return {"status": "fallback", "platform": "file", "artifact": json.dumps(schema, indent=2),
            "instructions": "Add this FAQ schema to your FAQ page <head>."}
