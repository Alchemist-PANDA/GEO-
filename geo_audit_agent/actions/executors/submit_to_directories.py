def execute(ctx: dict) -> dict:
    brand = ctx.get("brand", "Brand")
    category = ctx.get("category", "business")
    city = ctx.get("city", "")
    directories = [
        "Yelp", "Yellow Pages", "BBB", "Foursquare", "Apple Maps",
        "Bing Places", "Facebook Business", "TripAdvisor", "Angi", "Thumbtack"
    ]
    checklist = f"# Directory Submission Plan — {brand}\n\n"
    for d in directories:
        checklist += f"- [ ] Submit to {d} (category: {category}, location: {city})\n"
    checklist += f"\n**NAP Consistency:** Ensure Name ({brand}), Address ({city}), Phone match everywhere.\n"
    return {"status": "fallback", "platform": "Directories", "artifact": checklist,
            "instructions": "Submit your business to each directory with consistent NAP information."}
