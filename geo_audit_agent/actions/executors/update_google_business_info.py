def execute(ctx: dict) -> dict:
    brand = ctx.get("brand", "Brand")
    category = ctx.get("category", "business")
    city = ctx.get("city", "")
    checklist = (
        f"# Google Business Profile Update Checklist — {brand}\n\n"
        f"- [ ] Verify business name: {brand}\n"
        f"- [ ] Update category to: {category}\n"
        f"- [ ] Confirm address in {city}\n"
        f"- [ ] Add business hours\n"
        f"- [ ] Upload recent photos (minimum 5)\n"
        f"- [ ] Add business description with keywords\n"
        f"- [ ] Enable messaging\n"
        f"- [ ] Add products/services\n")
    return {"status": "fallback", "platform": "Google Business", "artifact": checklist,
            "instructions": "Follow this checklist to update your Google Business Profile."}
