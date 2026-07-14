def execute(ctx: dict) -> dict:
    import json
    brand = ctx.get("brand", "Brand")
    category = ctx.get("category", "service")
    schema = {
        "@context": "https://schema.org",
        "@type": "HowTo",
        "name": f"How to get started with {brand}",
        "step": [
            {"@type": "HowToStep", "text": f"Visit {brand}'s website or location"},
            {"@type": "HowToStep", "text": f"Browse available {category} services"},
            {"@type": "HowToStep", "text": "Contact us to schedule a consultation"},
        ]
    }
    return {"status": "fallback", "platform": "file", "artifact": json.dumps(schema, indent=2),
            "instructions": "Add this HowTo schema to relevant service pages."}
