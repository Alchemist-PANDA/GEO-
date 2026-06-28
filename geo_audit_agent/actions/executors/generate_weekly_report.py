def execute(ctx: dict) -> dict:
    md = (f"# Weekly GEO Report — {ctx['brand']}\n\n"
          f"- Visibility score: {ctx.get('score','N/A')}%\n"
          f"- Open gaps: {len(ctx.get('gaps', []))}\n"
          f"- Actions completed this week: {ctx.get('actions_done', 0)}\n")
    return {"status": "complete", "platform": "file", "artifact": md,
            "filename": f"weekly_report_{ctx['brand']}.md"}
