# Auto-generated executor for deploy_howto_schema
def execute(ctx: dict) -> dict:
    brand = ctx.get("brand", "Unknown")
    platform = "WordPress"
    artifact_content = f"# Generated deploy_howto_schema for {brand}\nContext: {ctx}"
    
    # Check credentials or simulate fallback
    if ctx.get("credentials", {}).get(platform.lower()):
        return {"status": "deployed", "platform": platform, "artifact": artifact_content}
    
    return {"status": "fallback", "platform": "file", "artifact": artifact_content,
            "instructions": f"Paste or upload this deploy_howto_schema artifact to {platform}."}
