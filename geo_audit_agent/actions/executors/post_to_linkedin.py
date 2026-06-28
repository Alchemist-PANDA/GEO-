# Auto-generated executor for post_to_linkedin
def execute(ctx: dict) -> dict:
    brand = ctx.get("brand", "Unknown")
    platform = "LinkedIn"
    artifact_content = f"# Generated post_to_linkedin for {brand}\nContext: {ctx}"
    
    # Check credentials or simulate fallback
    if ctx.get("credentials", {}).get(platform.lower()):
        return {"status": "deployed", "platform": platform, "artifact": artifact_content}
    
    return {"status": "fallback", "platform": "file", "artifact": artifact_content,
            "instructions": f"Paste or upload this post_to_linkedin artifact to {platform}."}
