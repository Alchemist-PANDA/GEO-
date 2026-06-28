# Auto-generated executor for generate_blog_post
def execute(ctx: dict) -> dict:
    brand = ctx.get("brand", "Unknown")
    platform = "file"
    artifact_content = f"# Generated generate_blog_post for {brand}\nContext: {ctx}"
    
    # Check credentials or simulate fallback
    if ctx.get("credentials", {}).get(platform.lower()):
        return {"status": "deployed", "platform": platform, "artifact": artifact_content}
    
    return {"status": "fallback", "platform": "file", "artifact": artifact_content,
            "instructions": f"Paste or upload this generate_blog_post artifact to {platform}."}
