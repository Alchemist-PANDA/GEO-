# Auto-generated executor for submit_to_directories
def execute(ctx: dict) -> dict:
    brand = ctx.get("brand", "Unknown")
    platform = "Directories"
    artifact_content = f"# Generated submit_to_directories for {brand}\nContext: {ctx}"
    
    # Check credentials or simulate fallback
    if ctx.get("credentials", {}).get(platform.lower()):
        return {"status": "deployed", "platform": platform, "artifact": artifact_content}
    
    return {"status": "fallback", "platform": "file", "artifact": artifact_content,
            "instructions": f"Paste or upload this submit_to_directories artifact to {platform}."}
