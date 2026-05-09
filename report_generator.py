import os
import re
from datetime import datetime
from typing import Optional


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def generate_markdown_report(audit_result: dict, lift_report: Optional[dict] = None) -> str:
    """
    Generate a markdown report from audit results and optional lift report.

    Args:
        audit_result: Audit result dictionary
        lift_report: Optional lift report dictionary

    Returns:
        Markdown-formatted report string
    """
    brand = audit_result.get("brand", "Unknown Brand")
    category = audit_result.get("category", "N/A")
    city = audit_result.get("city", "N/A")
    mode = audit_result.get("mode", "unknown")

    # Determine data source label
    if mode in ["simulated", "mock"]:
        mode_label = "Simulated Demo Mode"
        is_simulated = True
    elif mode in ["live_api", "real"]:
        mode_label = "Live API Mode"
        is_simulated = False
    else:
        mode_label = "Unknown"
        is_simulated = True

    # Header with strong disclaimer for simulated mode
    if is_simulated:
        report = f"""# GEO Visibility Report for {brand}

⚠️ **IMPORTANT: SIMULATED DEMO MODE**

**This report was generated in Simulated Demo Mode and should not be used as a real visibility measurement.**

Simulated Demo Mode uses deterministic sample outputs for product demonstration purposes only. It does not represent actual AI model responses or real brand visibility data.

For accurate visibility analysis, configure API keys and run in Live API Mode.

---

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Category:** {category}
**Location:** {city}
**Data Source:** {mode_label}

---

## Executive Summary

This report analyzes {brand}'s visibility in AI-generated search recommendations for the {category} category in {city}.

**Note:** All data in this report is simulated for demonstration purposes.

"""
    else:
        report = f"""# GEO Visibility Report for {brand}

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Category:** {category}
**Location:** {city}
**Data Source:** {mode_label} (Live API responses collected at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

---

## Executive Summary

This report is based on live API responses collected at the time of generation. AI recommendation algorithms evolve continuously, so regular monitoring is recommended.

This report analyzes {brand}'s visibility in AI-generated search recommendations for the {category} category in {city}.

"""

    # AI Visibility Score
    confidence_score = audit_result.get("confidence_score", 0.0)
    citation_found = audit_result.get("citation_found", False)

    report += f"""## AI Visibility Score

**Overall Confidence Score:** {confidence_score:.2f} / 1.00

"""

    if confidence_score >= 0.7:
        report += "✅ **Strong Visibility** - Your brand is frequently mentioned in AI recommendations.\n\n"
    elif confidence_score >= 0.4:
        report += "⚠️ **Moderate Visibility** - Your brand appears occasionally but could be stronger.\n\n"
    else:
        report += "❌ **Weak Visibility** - Your brand rarely or never appears in AI recommendations.\n\n"

    # Citation Status
    report += f"""## Citation Status

**Citation Found:** {"Yes" if citation_found else "No"}
"""

    if citation_found:
        position_score = audit_result.get("citation_position_score", 0.0)
        sentiment = audit_result.get("sentiment", "none")

        report += f"""**Citation Position Score:** {position_score:.2f} / 1.00
**Sentiment:** {sentiment.capitalize()}

"""

        if position_score >= 0.8:
            report += "Your brand appears early in AI responses, indicating strong positioning.\n\n"
        elif position_score >= 0.5:
            report += "Your brand appears in the middle of AI responses. Consider improving positioning.\n\n"
        else:
            report += "Your brand appears late in AI responses. Significant improvement needed.\n\n"
    else:
        report += "\nYour brand is not currently appearing in AI-generated recommendations for this category and location.\n\n"

    # AI Response Analysis (Proof Mode)
    raw_response = audit_result.get("raw_response", "")
    parsed = audit_result.get("parsed", {})

    if raw_response:
        report += """## AI Response Analysis

This section shows the raw AI output and how we interpreted it.

### Raw AI Response

```
"""
        # Trim if too long (keep first 1000 chars)
        trimmed_response = raw_response[:1000] + ("..." if len(raw_response) > 1000 else "")
        report += trimmed_response
        report += """
```

### What We Detected

"""
        citation_found_parsed = parsed.get("citation_found", False)
        position_score_parsed = parsed.get("citation_position_score", 0.0)
        sentiment_parsed = parsed.get("sentiment", "none")
        competitors_parsed = parsed.get("competitors", [])

        report += f"- **Brand Mentioned:** {'Yes' if citation_found_parsed else 'No'}\n"
        report += f"- **Position Score:** {position_score_parsed:.2f}\n"
        report += f"- **Sentiment:** {sentiment_parsed.capitalize()}\n"
        report += f"- **Competitors Detected:** {', '.join(competitors_parsed[:3]) if competitors_parsed else 'None'}\n\n"

        report += "### Interpretation\n\n"

        if not citation_found_parsed:
            report += f"The AI response does not mention {brand}, indicating zero visibility in AI recommendations. "
            if competitors_parsed:
                report += f"Competitors like {', '.join(competitors_parsed[:2])} are mentioned instead, suggesting stronger presence in AI training data.\n\n"
            else:
                report += "This suggests the brand lacks sufficient online presence for AI models to recommend it.\n\n"
        elif position_score_parsed < 0.5:
            report += f"{brand} appears in the AI response but late in the list (position score: {position_score_parsed:.2f}). "
            report += f"This indicates weak visibility — the AI knows about the brand but prioritizes competitors.\n\n"
        else:
            report += f"{brand} appears early in the AI response (position score: {position_score_parsed:.2f}) with {sentiment_parsed} sentiment. "
            report += f"This indicates strong visibility in AI recommendations.\n\n"

        report += "**Disclaimer:** Interpretation is based on NLP heuristics and may vary with different AI outputs.\n\n"

    # Competitors
    competitors = audit_result.get("competitors", [])
    if competitors:
        report += f"""## Competitors

The following brands are frequently mentioned alongside or instead of {brand}:

"""
        for i, competitor in enumerate(competitors[:5], 1):
            report += f"{i}. {competitor}\n"
        report += "\n"

    # Key Gaps
    gaps = audit_result.get("gaps", [])
    if gaps:
        report += """## Key Gaps

The following gaps were identified in your GEO strategy:

"""
        for gap in gaps:
            report += f"- {gap}\n"
        report += "\n"

    # Remediation Plan
    remediation = audit_result.get("remediation", [])
    if remediation:
        report += """## Remediation Plan

### Recommended Actions

"""

        # Group by priority
        high_priority = [r for r in remediation if r.get("priority") == "high"]
        medium_priority = [r for r in remediation if r.get("priority") == "medium"]
        low_priority = [r for r in remediation if r.get("priority") == "low"]

        if high_priority:
            report += "### High Priority\n\n"
            for rec in high_priority:
                quick_win = " 🎯 **Quick Win**" if rec.get("quick_win") else ""
                report += f"#### {rec.get('title', 'Untitled')}{quick_win}\n\n"
                report += f"**Reason:** {rec.get('reason', 'N/A')}\n\n"

                # Add "Why This Works" section
                why_this_works = rec.get("why_this_works")
                if why_this_works:
                    report += f"**Why This Works:** {why_this_works}\n\n"

                report += f"**Action:**\n{rec.get('action', 'N/A')}\n\n"
                report += f"**Expected Impact:** {rec.get('expected_impact', 'N/A')}\n\n"
                report += f"**Effort:** {rec.get('effort', 'N/A').capitalize()} | **Impact:** {rec.get('impact', 'N/A').capitalize()}\n\n"
                report += "---\n\n"

        if medium_priority:
            report += "### Medium Priority\n\n"
            for rec in medium_priority:
                report += f"#### {rec.get('title', 'Untitled')}\n\n"
                report += f"**Reason:** {rec.get('reason', 'N/A')}\n\n"

                # Add "Why This Works" section
                why_this_works = rec.get("why_this_works")
                if why_this_works:
                    report += f"**Why This Works:** {why_this_works}\n\n"

                report += f"**Expected Impact:** {rec.get('expected_impact', 'N/A')}\n\n"
                report += "---\n\n"

        if low_priority:
            report += "### Low Priority\n\n"
            for rec in low_priority:
                report += f"- **{rec.get('title', 'Untitled')}**: {rec.get('expected_impact', 'N/A')}\n"
            report += "\n"

    # Lift Simulation
    if lift_report:
        lift = lift_report.get("lift", {})
        before_score = lift.get("before_score", 0.0)
        after_score = lift.get("after_score", 0.0)
        absolute_lift = lift.get("absolute_lift", 0.0)
        percentage_lift = lift.get("percentage_lift", 0.0)

        report += f"""## Lift Simulation

**Baseline Score:** {before_score:.2f}
**Projected Score:** {after_score:.2f}
**Absolute Lift:** +{absolute_lift:.2f}
**Percentage Lift:** {percentage_lift:.1f}%

**Summary:** {lift.get('summary', 'N/A')}

"""

        # Before/After AI Response Comparison
        baseline = lift_report.get("baseline", {})
        improved = lift_report.get("improved", {})

        before_response = improved.get('before_raw_response') or baseline.get('raw_response', '')
        after_response = improved.get('raw_response', '')

        if before_response and after_response:
            report += """### Before vs After: AI Response Transformation

This section shows how AI recommendations changed after implementing improvements.

#### 🔴 BEFORE

```
"""
            report += before_response[:800] + ("..." if len(before_response) > 800 else "")
            report += """
```

**Detection:**
"""
            report += f"- Brand mentioned: {'Yes' if baseline.get('citation_found') else 'No'}\n"
            report += f"- Position score: {baseline.get('citation_position_score', 0):.2f}\n"
            report += f"- Sentiment: {baseline.get('sentiment', 'none')}\n\n"

            report += """#### 🟢 AFTER

```
"""
            report += after_response[:800] + ("..." if len(after_response) > 800 else "")
            report += """
```

**Detection:**
"""
            report += f"- Brand mentioned: {'Yes' if improved.get('citation_found') else 'No'}\n"
            report += f"- Position score: {improved.get('citation_position_score', 0):.2f}\n"
            report += f"- Sentiment: {improved.get('sentiment', 'none')}\n\n"

            report += "**What Changed:**\n\n"

            changes = []
            if not baseline.get('citation_found') and improved.get('citation_found'):
                changes.append("✅ Brand became visible in AI recommendations")
            if improved.get('citation_position_score', 0) > baseline.get('citation_position_score', 0):
                changes.append(f"📈 Position improved from {baseline.get('citation_position_score', 0):.2f} to {improved.get('citation_position_score', 0):.2f}")
            if improved.get('sentiment') != baseline.get('sentiment'):
                changes.append(f"💭 Sentiment shifted from {baseline.get('sentiment', 'none')} to {improved.get('sentiment', 'none')}")

            if changes:
                for change in changes:
                    report += f"- {change}\n"
            else:
                report += "- Incremental improvements across multiple factors\n"

            report += "\n"

            # Simulation Credibility
            sim_conf = improved.get('simulation_confidence', 'medium')
            report += f"**Simulation Confidence:** {sim_conf.upper()}\n\n"
            report += "> ⚠️ **Disclaimer:** This is a simulated improvement based on known ranking factors. Actual AI responses are highly dynamic and may vary depending on model updates, timing, and regional data availability.\n\n"

            sim_notes = improved.get('simulation_notes', {})
            if sim_notes:
                report += "#### Expected Outcome\n"
                report += f"{sim_notes.get('expected_outcome', 'N/A')}\n\n"

                report += "#### Alternative Possible Outcomes\n"
                for alt in sim_notes.get('alternative_outcomes', []):
                    report += f"- {alt}\n"
                report += "\n"

                report += "#### Risk Factors & Mitigation\n"
                for risk in sim_notes.get('risk_factors', []):
                    report += f"- {risk}\n"
                report += "\n"

    # Methodology
    report += """## Methodology

This report analyzes your brand's visibility in AI-generated search recommendations by:

1. Querying AI models with category-specific search prompts
2. Analyzing citation presence, position, and sentiment
3. Comparing against competitor mentions
4. Identifying gaps in your GEO strategy
5. Generating targeted remediation recommendations

"""

    # Disclaimer
    if is_simulated:
        report += """## Disclaimer

⚠️ **This report was generated in Simulated Demo Mode for demonstration purposes.**

The results shown are deterministic sample outputs and do not reflect actual AI model behavior or real brand visibility. All scores, citations, and recommendations are simulated for product demonstration only.

**For accurate, real-time analysis:**
- Configure GROQ_API_KEY or GOOGLE_API_KEY in your environment
- Enable Live API Mode in the dashboard
- Run a new audit to collect live API responses

"""
    else:
        report += f"""## Disclaimer

This report is based on live API responses collected at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.

AI recommendation algorithms evolve continuously, so regular monitoring is recommended. Results may vary based on:
- Model updates and training data changes
- Regional data availability
- Query timing and context
- Competitive landscape shifts

"""

    report += f"""---

*Report generated by BrandSight GEO - AI Visibility Optimization Platform*
*For questions or support, contact your account manager*
"""

    return report


def save_markdown_report(
    audit_result: dict,
    lift_report: Optional[dict] = None,
    output_dir: str = "reports"
) -> str:
    """
    Generate and save a markdown report.

    Args:
        audit_result: Audit result dictionary
        lift_report: Optional lift report dictionary
        output_dir: Directory to save reports

    Returns:
        Path to saved report file
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Generate filename
    brand = audit_result.get("brand", "unknown")
    brand_slug = slugify(brand)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{brand_slug}_report_{timestamp}.md"
    filepath = os.path.join(output_dir, filename)

    # Generate report
    report_content = generate_markdown_report(audit_result, lift_report)

    # Save to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report_content)

    return filepath
