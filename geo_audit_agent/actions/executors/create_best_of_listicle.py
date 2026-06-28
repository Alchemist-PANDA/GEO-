# Auto-generated executor for create_best_of_listicle
def execute(ctx: dict) -> dict:
    brand = ctx.get("brand", "Unknown")
    platform = "file"
    artifact_content = f"# Generated create_best_of_listicle for {brand}\nContext: {ctx}"
    
    # Check credentials or simulate fallback
    if ctx.get("credentials", {}).get(platform.lower()):
        return {"status": "deployed", "platform": platform, "artifact": artifact_content}
    
    return {"status": "fallback", "platform": "file", "artifact": artifact_content,
            "instructions": f"Paste or upload this create_best_of_listicle artifact to {platform}."}
