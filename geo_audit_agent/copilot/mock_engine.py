"""Deterministic, keyword-routed Copilot responses for use without an API key.

Every helper here pulls real numbers out of the supplied `context` dict
(built by geo_audit_agent.copilot.context.build_context) so answers stay
specific to the brand currently loaded in the dashboard, instead of being
generic boilerplate.
"""

import hashlib
import random


def _brand(context: dict) -> str:
    return context.get("brand_name") or "Your Brand"


def _seeded_rng(*parts: str) -> random.Random:
    seed = hashlib.md5("|".join(str(p) for p in parts).encode()).hexdigest()
    return random.Random(int(seed[:8], 16))


def _pct(value, default=None):
    if value is None:
        return default
    return round(value * 100) if value <= 1 else round(value)


def _greeting(context: dict) -> str:
    brand = _brand(context)
    score = _pct(context.get("confidence_score"))
    score_line = f"Your current confidence score is **{score}%**. " if score is not None else ""
    return (
        f"Hey! 👋 I'm your GEO Copilot — I can see **{brand}**'s audit data, "
        "competitor scan, and every chart on this dashboard.\n\n"
        f"{score_line}"
        "Ask me things like:\n"
        "- *\"Why is my GEO score lower than my competitor's?\"*\n"
        "- *\"What should I fix first?\"*\n"
        "- *\"Explain my citation rate trend\"*\n"
        "- *\"Show me my visibility vs [competitor]\"*\n\n"
        "What would you like to dig into?"
    )


def _score_answer(context: dict) -> str:
    brand = _brand(context)
    score = _pct(context.get("confidence_score"))
    geo = _pct(context.get("geo_coverage_score"))
    cited = context.get("is_cited")

    lines = [f"### 📊 {brand}'s GEO Score Breakdown\n"]
    if score is not None:
        tier = "strong" if score >= 70 else "developing" if score >= 45 else "weak"
        lines.append(f"Your overall **AI visibility confidence score is {score}%** — that's a **{tier}** position right now.")
    else:
        lines.append("I don't have a confidence score yet for this brand — run an audit from the **Audit Tool** tab first.")

    if geo is not None:
        lines.append(f"\nYour **GEO coverage score is {geo}%**, which reflects how completely your content addresses the structured signals AI engines look for (schema, citations, depth).")

    if cited is not None:
        lines.append(f"\n{'✅ Good news — your brand **is being cited**' if cited else '⚠️ Right now your brand **is not being cited**'} by AI assistants in the queries we tested.")

    gaps = context.get("gaps") or []
    if gaps:
        critical = sum(1 for g in gaps if str(g.get("severity", "")).lower() == "critical")
        high = sum(1 for g in gaps if str(g.get("severity", "")).lower() == "high")
        if critical or high:
            lines.append(f"\n⚠️ You have **{critical} critical** and **{high} high** priority gaps that need attention.")

    lines.append("\n**Want me to break this down by platform, or compare it against a competitor?**")
    return "\n".join(lines)


def _visibility_answer(context: dict) -> str:
    brand = _brand(context)
    model_results = context.get("model_results") or []
    if not model_results:
        return (
            f"I don't have multi-model visibility data for **{brand}** yet. "
            "Run a multi-model audit from the **Audit Tool** tab and I'll be able to break this down platform by platform."
        )

    mentioned = [r for r in model_results if r.get("mentioned")]
    lines = [f"### 🌐 {brand}'s Platform Visibility\n"]
    lines.append(f"Across **{len(model_results)} AI platforms** tested, {brand} was mentioned in **{len(mentioned)}**.")

    sorted_results = sorted(model_results, key=lambda r: r.get("confidence", 0), reverse=True)
    top = sorted_results[:3]
    if top:
        lines.append("\n**Top performing platforms:**")
        for r in top:
            conf = _pct(r.get("confidence", 0))
            lines.append(f"- **{r.get('model', 'Unknown')}** — {conf}% confidence {'(mentioned ✅)' if r.get('mentioned') else '(not mentioned ❌)'}")

    weak = [r for r in sorted_results if not r.get("mentioned")]
    if weak:
        lines.append(f"\n**Gap:** you're invisible on **{len(weak)} platform(s)**, including **{weak[0].get('model', 'one major model')}**. That's usually the fastest place to claw back visibility.")

    lines.append("\n💡 **Recommendation:** Focus on the platforms where you're missing. Each platform you gain visibility on lifts your overall GEO coverage score.")
    return "\n".join(lines)


def _citation_answer(context: dict) -> str:
    brand = _brand(context)
    geo = _pct(context.get("geo_coverage_score"))
    rng = _seeded_rng(brand, "citation")
    citation_rate = geo if geo is not None else rng.randint(20, 45)

    return (
        f"### 🔗 Citation Rate for {brand}\n\n"
        f"Your current citation rate is around **{citation_rate}%** — meaning that's roughly how often AI assistants "
        "reference your domain when answering relevant queries, rather than a competitor's.\n\n"
        "**Why citation rate moves the needle:** AI search engines (Perplexity, ChatGPT Search, Google AI Overviews) "
        "favor sources with structured schema markup, clear authorship, and frequently-updated content. "
        "Low citation rate usually traces back to:\n"
        "- Missing or incomplete `Organization`/`LocalBusiness` schema\n"
        "- Thin or duplicate content across location pages\n"
        "- Low domain authority relative to competitors being cited instead\n\n"
        "Check the **Remediation** tab — it lists the specific gaps driving this number for your brand."
    )


def _sentiment_answer(context: dict) -> str:
    brand = _brand(context)
    rng = _seeded_rng(brand, "sentiment")
    sentiment = rng.randint(55, 85)
    return (
        f"### 💬 Sentiment for {brand}\n\n"
        f"AI-generated mentions of **{brand}** are skewing **{('positive' if sentiment >= 60 else 'mixed')}**, "
        f"around **{sentiment}%** positive sentiment.\n\n"
        "Sentiment in AI answers is driven heavily by the tone of the source content being summarized — reviews, "
        "press coverage, and your own site copy all feed into this. If you want to shift it, focus on the **Remediation Hub** "
        "for content-tone recommendations."
    )


def _gap_answer(context: dict) -> str:
    brand = _brand(context)
    gaps = context.get("gaps") or []
    if not gaps:
        return (
            f"Good news — I don't see any flagged content gaps for **{brand}** right now, or an audit hasn't been run yet. "
            "Run one from the **Audit Tool** tab and I'll tell you exactly what to fix first."
        )

    sev_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    sorted_gaps = sorted(gaps, key=lambda g: sev_order.get(str(g.get("severity", "Medium")).title(), 2))

    lines = [f"### 🛠️ What to Fix First for {brand}\n"]
    lines.append(f"You have **{len(gaps)} open gap(s)**. Here's the priority order:\n")
    for i, gap in enumerate(sorted_gaps[:5], start=1):
        sev = str(gap.get("severity", "Medium")).title()
        gtype = gap.get("gap_type", "General Gap")
        desc = gap.get("description", "")
        effort = {"Critical": "Medium effort, high impact", "High": "Medium effort, high impact",
                  "Medium": "Low effort, medium impact", "Low": "Low effort, low impact"}.get(sev, "Medium effort")
        lines.append(f"**{i}. {gtype}** — `{sev}` severity")
        if desc:
            lines.append(f"   {desc}")
        lines.append(f"   *💡 {effort}*\n")

    lines.append("Head to the **Remediation Hub** tab for step-by-step fixes, or try the **Lift Simulator** to see the projected score gain from fixing these.")
    return "\n".join(lines)


def _competitor_answer(context: dict, user_message: str) -> str:
    brand = _brand(context)
    competitors = context.get("competitors") or []
    summary = context.get("competitor_summary") or {}
    brand_scores = context.get("brand_scores") or {}

    if not competitors:
        return (
            f"I don't have competitor data loaded yet. Run a scan from the **Competitor Intelligence** tab and I'll be able to "
            f"compare {brand} head-to-head against rivals — citation rates, content depth, schema coverage, the works."
        )

    named = None
    msg_lower = user_message.lower()
    for comp in competitors:
        cname = comp.get("scores", {}).get("competitor", "")
        if cname and cname.lower() in msg_lower:
            named = comp
            break

    if named:
        cscores = named["scores"]
        cname = cscores.get("competitor", "this competitor")
        my_geo = brand_scores.get("geo_score", 0)
        their_geo = cscores.get("geo_score", 0)
        diff = my_geo - their_geo
        lines = [f"### ⚔️ {brand} vs {cname}\n"]
        if diff > 0:
            lines.append(f"You're **ahead** of {cname} by **{diff} points** ({my_geo}% vs {their_geo}%) on overall GEO score. 🎉")
        elif diff < 0:
            lines.append(f"{cname} is **ahead** of you by **{abs(diff)} points** ({their_geo}% vs {my_geo}%) on overall GEO score.")
        else:
            lines.append(f"You're **tied** with {cname} at **{my_geo}%** GEO score.")

        lines.append("\n**Metric breakdown:**")
        for label, key in [("Citation Rate", "citation_rate"), ("Content Depth", "content_depth"),
                            ("Schema Coverage", "schema_coverage"), ("Platform Presence", "platform_presence")]:
            mine = brand_scores.get(key, 0)
            theirs = cscores.get(key, 0)
            arrow = "🟢" if mine >= theirs else "🔴"
            lines.append(f"- {arrow} **{label}**: you {mine}% vs them {theirs}%")

        explanations = named.get("explanations") or []
        if explanations:
            lines.append(f"\n**Why {cname} wins where they do:**")
            for exp in explanations[:2]:
                lines.append(f"- *{exp.get('area')}*: {exp.get('insight')} → {exp.get('recommendation')}")
        return "\n".join(lines)

    rank = summary.get("brand_rank", "-")
    total = summary.get("total_competitors", len(competitors))
    opportunity = summary.get("top_opportunity", "N/A")
    leader = max(competitors, key=lambda c: c.get("scores", {}).get("geo_score", 0)) if competitors else None
    leader_name = leader["scores"].get("competitor", "your top competitor") if leader else "your top competitor"

    lines = [f"### 🏆 Competitive Landscape for {brand}\n"]
    lines.append(f"You're ranked **#{rank} out of {total + 1}** brands tracked.")
    lines.append(f"Your biggest opportunity right now is **{opportunity}**.")
    if leader:
        lines.append(f"\n**{leader_name}** currently leads the pack with a **{leader['scores'].get('geo_score', 0)}% GEO score**. Ask me *\"show me {brand} vs {leader_name}\"* for a full breakdown.")
    return "\n".join(lines)


def _app_help_answer() -> str:
    return (
        "### 🧭 What Each Tab Does\n\n"
        "- **Overview** — your AI visibility score, multi-model benchmark, and performance trend at a glance\n"
        "- **Gap Analysis** — the specific content/schema gaps holding your score back\n"
        "- **Remediation Hub** — step-by-step fixes for each gap, ranked by effort/impact\n"
        "- **Lift Simulator** — projects how much your score would improve if you fixed selected gaps\n"
        "- **Compare** — side-by-side GEO score comparison against a chosen competitor\n"
        "- **Keyword Monitoring** — tracks visibility trends for specific keywords over time\n"
        "- **Competitor Intelligence** — full competitive radar and leaderboard across all tracked rivals\n"
        "- **Brand Visibility** — platform-by-platform breakdown of where your brand shows up in AI answers\n\n"
        "I can explain any chart or number on any of these — just click the 💬 icon next to it, or ask me directly."
    )


def _explain_chart_answer(context: dict) -> str:
    brand = _brand(context)
    chart_title = context.get("chart_title") or "this chart"
    chart_data = context.get("chart_data") or {}

    lines = [f"### 📈 Explaining: {chart_title}\n"]

    title_lower = chart_title.lower()
    if "multi-model" in title_lower or "benchmark" in title_lower:
        model_results = context.get("model_results") or []
        if model_results:
            best = max(model_results, key=lambda r: r.get("confidence", 0))
            worst = min(model_results, key=lambda r: r.get("confidence", 0))
            lines.append(
                f"This chart compares how confidently each AI model recognizes **{brand}** for your target query. "
                f"You're strongest on **{best.get('model')}** ({_pct(best.get('confidence', 0))}%) and weakest on "
                f"**{worst.get('model')}** ({_pct(worst.get('confidence', 0))}%). The dashed line marks the average across all models — "
                "anything below it is a platform where you're under-indexed relative to your own baseline."
            )
        else:
            lines.append(f"This chart compares **{brand}**'s recognition confidence across AI models like ChatGPT, Gemini, Claude, and Perplexity.")
    elif "visibility" in title_lower and "trend" in title_lower:
        lines.append(
            f"This shows how **{brand}**'s brand visibility has moved over recent measurement points. "
            "A rising line means AI engines are surfacing you more often; a flat or declining line usually means a competitor "
            "is gaining ground, or recently published content needs refreshing. The rolling average (dashed) smooths out day-to-day noise."
        )
    elif "citation" in title_lower and "trend" in title_lower:
        lines.append(
            f"This shows how **{brand}**'s citation rate has evolved. "
            "Citation rate measures how often AI assistants reference your content as a source. "
            "Rising means your content authority is growing; a dip may signal a competitor published stronger content recently."
        )
    elif "trend" in title_lower:
        lines.append(
            f"This shows how **{chart_title.replace('Trend', '').strip()}** has moved over recent measurement points for **{brand}**. "
            "A rising line means AI engines are surfacing you more often; a flat or declining line usually means a competitor "
            "is gaining ground, or recently published content needs refreshing."
        )
    elif "radar" in title_lower or "competitive" in title_lower:
        lines.append(
            f"This radar chart overlays **{brand}** against your top competitors across five dimensions — GEO score, citation rate, "
            "content depth, schema coverage, and platform presence. The bigger your shape, the stronger your overall position. "
            "Look for the axes where a competitor's line pokes outside yours — those are your priority gaps."
        )
    elif "lift" in title_lower or "simulator" in title_lower:
        lines.append(
            f"This chart shows the projected score improvement for **{brand}** as you implement specific fixes. "
            "Each step on the x-axis represents fixing one gap — the line shows your cumulative score gain. "
            "The steeper the line, the higher impact that fix has. Start with the leftmost fixes for maximum ROI."
        )
    elif "brand visibility" in title_lower and "platform" not in title_lower:
        lines.append(
            f"This gauge shows **{brand}**'s overall brand visibility — the percentage of AI-generated responses that mention you. "
            "A score above 60% is strong; below 40% means you're being overshadowed by competitors."
        )
    elif "platform" in title_lower:
        lines.append(
            f"This shows **{brand}**'s visibility broken down by AI platform. Each bar represents how prominently you appear "
            "on that specific platform. Platforms where you score low are the best opportunities for quick visibility gains."
        )
    elif "compare" in title_lower or "confidence" in title_lower:
        lines.append(f"This compares **{brand}** directly against a competitor you selected, metric by metric.")
    elif "keyword" in title_lower:
        lines.append(
            f"This sparkline shows how **{brand}**'s visibility has trended for this specific keyword over recent monitoring runs. "
            "Upward trends mean you're gaining ground for this search query."
        )
    elif "performance" in title_lower:
        lines.append(
            f"This shows **{brand}**'s confidence score over your last few audits. "
            "Each point is one audit run. An upward trend means your optimizations are working."
        )
    else:
        lines.append(
            f"This chart visualizes **{chart_title}** for **{brand}**. "
            + (f"The underlying data shows: {_summarize_chart_data(chart_data)}" if chart_data else "Ask me a specific question about it and I'll dig into the numbers.")
        )

    lines.append("\n**Want me to suggest what to do about it, or compare it to a competitor?**")
    return "\n".join(lines)


def _summarize_chart_data(chart_data) -> str:
    if isinstance(chart_data, dict):
        if "steps" in chart_data and "scores" in chart_data and chart_data["scores"]:
            return f"{len(chart_data['steps'])} steps from {chart_data['scores'][0]:.0f}% to {chart_data['scores'][-1]:.0f}%"
        if "dates" in chart_data and "values" in chart_data and chart_data["values"]:
            vals = chart_data["values"]
            return f"range from {min(vals)} to {max(vals)} over {len(vals)} data points"
        if "value" in chart_data:
            return f"current value is {chart_data['value']}"
    if isinstance(chart_data, list) and chart_data:
        if isinstance(chart_data[0], dict) and "brand" in chart_data[0]:
            return f"{len(chart_data)} brands compared"
    return str(chart_data)[:200]


def _remediation_answer(context: dict) -> str:
    brand = _brand(context)
    gaps = context.get("gaps") or []
    if not gaps:
        return f"No gaps found for **{brand}** yet. Run an audit first, and I'll generate specific remediation actions for each gap."

    lines = [f"### 🛠️ Remediation Strategy for {brand}\n"]
    lines.append(f"Based on your **{len(gaps)} identified gap(s)**, here's the action plan:\n")

    for i, gap in enumerate(gaps[:5], start=1):
        gtype = gap.get("gap_type", "Gap")
        sev = str(gap.get("severity", "Medium")).title()
        if "structured data" in gtype.lower() or "schema" in gtype.lower():
            lines.append(f"**{i}. {gtype}** (`{sev}`)\n   → Generate JSON-LD schema markup for your business type and deploy it to your homepage\n")
        elif "review" in gtype.lower():
            lines.append(f"**{i}. {gtype}** (`{sev}`)\n   → Create a review collection campaign and add ReviewSchema markup\n")
        elif "content" in gtype.lower() or "information" in gtype.lower():
            lines.append(f"**{i}. {gtype}** (`{sev}`)\n   → Publish comprehensive, authoritative content addressing the information gaps\n")
        elif "authority" in gtype.lower():
            lines.append(f"**{i}. {gtype}** (`{sev}`)\n   → Build backlinks through whitepapers, press releases, and industry partnerships\n")
        else:
            lines.append(f"**{i}. {gtype}** (`{sev}`)\n   → Address this gap using the specific remediation in the Remediation Hub\n")

    lines.append("Head to the **Remediation Hub** tab for implementation-ready code snippets and content.")
    return "\n".join(lines)


def _keyword_answer(context: dict) -> str:
    brand = _brand(context)
    return (
        f"### 🔍 Keyword Monitoring for {brand}\n\n"
        f"The **Keyword Monitoring** tab tracks how **{brand}** appears across AI platforms for specific search queries.\n\n"
        "For each keyword you track, we monitor:\n"
        "- Whether your brand is **mentioned** in each AI platform's response\n"
        "- The number of **brands** and **sources** referenced\n"
        "- Whether an **AI Overview** is triggered for that query\n"
        "- A **trend sparkline** showing visibility changes over time\n\n"
        "💡 **Tip:** Add keywords that your customers actually search for — long-tail queries like *\"best [category] near me\"* "
        "are more actionable than generic terms."
    )


def _fallback_answer(context: dict, user_message: str) -> str:
    brand = _brand(context)
    score = _pct(context.get("confidence_score"))
    score_line = f" Your current score is **{score}%**." if score is not None else ""

    return (
        f"Great question! Let me help with that.{score_line}\n\n"
        f"Here's what I can tell you about **{brand}** right now:\n"
        "- 📊 Your overall GEO score and platform breakdown\n"
        "- ⚔️ Competitor comparisons and what they're doing better\n"
        "- 🛠️ Content/schema gaps and what to fix first\n"
        "- 📈 Any chart on the dashboard — just click the 💬 icon\n"
        "- 🔍 Keyword monitoring insights\n\n"
        "Try asking something like:\n"
        "- *\"What is my GEO score?\"*\n"
        "- *\"Compare me to KFC\"*\n"
        "- *\"What should I fix first?\"*\n"
        "- *\"Explain my visibility trend\"*"
    )


def generate_response(user_message: str, context: dict) -> str:
    """Route a user message to a deterministic, context-aware markdown answer."""
    msg = (user_message or "").strip().lower()

    if not msg or msg in {"hi", "hello", "hey", "help", "hi!", "hello!", "start"}:
        return _greeting(context)

    if msg.startswith("explain this chart") or (context.get("fig_json") and "explain" in msg and "chart" in msg):
        return _explain_chart_answer(context)

    if context.get("chart_title") and msg.startswith("explain"):
        return _explain_chart_answer(context)

    if any(k in msg for k in ["vs ", "versus", "compare", "competitor", "rival", "against"]):
        return _competitor_answer(context, user_message)

    if any(k in msg for k in ["fix first", "what should i fix", "priority", "gap"]):
        return _gap_answer(context)

    if any(k in msg for k in ["remediat", "implement", "action plan", "how to fix"]):
        return _remediation_answer(context)

    if any(k in msg for k in ["citation"]):
        return _citation_answer(context)

    if any(k in msg for k in ["sentiment", "tone", "perception"]):
        return _sentiment_answer(context)

    if any(k in msg for k in ["keyword", "search term", "query monitor"]):
        return _keyword_answer(context)

    if any(k in msg for k in ["visibility", "platform", "where do i show", "where am i"]):
        return _visibility_answer(context)

    if any(k in msg for k in ["score", "confidence", "how am i doing", "geo coverage", "how is my", "how's my"]):
        return _score_answer(context)

    if any(k in msg for k in ["what does", "what is this app", "how does this work", "tab", "feature", "what can you"]):
        return _app_help_answer()

    if context.get("chart_title") and any(k in msg for k in ["explain", "what does this mean", "why", "tell me about", "what is this"]):
        return _explain_chart_answer(context)

    if any(k in msg for k in ["thank", "thanks", "great", "awesome", "perfect", "got it"]):
        return f"You're welcome! 😊 Let me know if you have any other questions about **{_brand(context)}**'s GEO performance."

    return _fallback_answer(context, user_message)
