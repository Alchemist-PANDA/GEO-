def execute(ctx: dict) -> dict:
    """ctx: {brand, category, city, website_url, credentials?}.
    Always produces a fallback file even when the platform API is unavailable."""
    from geo_audit_agent.geo_remediation_tools import generate_json_ld
    product = {"name": ctx["brand"], "description": f"Best {ctx.get('category','')} in {ctx.get('city','')}",
               "address": ctx.get("city", ""), "telephone": ctx.get("phone", "")}
    schema = generate_json_ld(brand_name=ctx["brand"], product_info=product)
    # Primary: push to WordPress if creds present; else fallback artifact.
    if ctx.get("credentials", {}).get("wordpress"):
        try:
            _push_wordpress(ctx, schema)      # implement per WP REST API
            return {"status": "deployed", "platform": "WordPress", "artifact": schema}
        except Exception as e:
            return {"status": "fallback", "reason": str(e), "artifact": schema,
                    "instructions": "Paste this <script type=application/ld+json> into <head>."}
    return {"status": "fallback", "platform": "file", "artifact": schema,
            "instructions": "Add this JSON-LD block to your site <head>."}

def _push_wordpress(ctx, schema):  # template
    raise NotImplementedError("Wire WP REST API: POST /wp-json/wp/v2/... with app password")
