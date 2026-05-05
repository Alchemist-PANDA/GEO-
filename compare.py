from geo_audit_agent.agent import build_geo_audit_agent


def compare_brands(brand_a: str, brand_b: str, category: str, city: str, force_mock: bool = False) -> dict:
    """
    Compare two brands side-by-side for GEO visibility.

    Args:
        brand_a: First brand name
        brand_b: Second brand name
        category: Business category
        city: City location
        force_mock: If True, use simulated mode

    Returns:
        Dictionary with both audit results and comparison analysis
    """
    agent = build_geo_audit_agent()

    # Run audits for both brands
    audit_a = agent.invoke({
        "brand": brand_a,
        "category": category,
        "city": city,
        "force_mock": force_mock
    })

    audit_b = agent.invoke({
        "brand": brand_b,
        "category": category,
        "city": city,
        "force_mock": force_mock
    })

    # Calculate differences
    score_a = audit_a.get("confidence_score", 0.0)
    score_b = audit_b.get("confidence_score", 0.0)
    score_difference = round(score_b - score_a, 2)

    position_a = audit_a.get("citation_position_score", 0.0)
    position_b = audit_b.get("citation_position_score", 0.0)
    position_difference = round(position_b - position_a, 2)

    sentiment_a = audit_a.get("sentiment", "none")
    sentiment_b = audit_b.get("sentiment", "none")

    # Determine winner (use tie-breaker logic from insight generation)
    score_a = audit_a.get('confidence_score', 0)
    score_b = audit_b.get('confidence_score', 0)
    position_a = audit_a.get('citation_position_score', 0)
    position_b = audit_b.get('citation_position_score', 0)
    cited_a = audit_a.get("citation_found", False)
    cited_b = audit_b.get("citation_found", False)
    gaps_a = audit_a.get("gaps", [])
    gaps_b = audit_b.get("gaps", [])
    sentiment_order = {"positive": 3, "neutral": 2, "none": 1, "negative": 0}

    # Apply same tie-breaker logic as insight generation
    if abs(score_difference) >= 0.05:
        winner = "brand_b" if score_b > score_a else "brand_a"
    elif abs(position_b - position_a) >= 0.01:
        winner = "brand_b" if position_b > position_a else "brand_a"
    elif sentiment_order.get(sentiment_b, 0) != sentiment_order.get(sentiment_a, 0):
        winner = "brand_b" if sentiment_order.get(sentiment_b, 0) > sentiment_order.get(sentiment_a, 0) else "brand_a"
    elif len(gaps_a) != len(gaps_b):
        winner = "brand_b" if len(gaps_b) < len(gaps_a) else "brand_a"
    elif cited_a != cited_b:
        winner = "brand_a" if cited_a else "brand_b"
    else:
        winner = "brand_a" if brand_a < brand_b else "brand_b"

    # Generate insight
    insight = _generate_comparison_insight(
        brand_a, brand_b,
        audit_a, audit_b,
        score_difference, position_difference,
        sentiment_a, sentiment_b
    )

    # Generate competitive actions
    recommended_actions = _generate_competitive_actions(
        brand_a, brand_b,
        audit_a, audit_b,
        winner
    )

    return {
        "brand_a": audit_a,
        "brand_b": audit_b,
        "comparison": {
            "score_difference": score_difference,
            "position_difference": position_difference,
            "sentiment_comparison": f"{sentiment_a} vs {sentiment_b}",
            "winner": winner,
            "insight": insight,
            "recommended_actions": recommended_actions,
            "winner_reason": recommended_actions[0].get("winner_reason", "") if recommended_actions else "",
            "loser_gap": recommended_actions[0].get("loser_gap", "") if recommended_actions else "",
            "fastest_way_to_win": recommended_actions[0].get("fastest_path", "") if recommended_actions else ""
        }
    }


def _generate_comparison_insight(
    brand_a: str,
    brand_b: str,
    audit_a: dict,
    audit_b: dict,
    score_diff: float,
    position_diff: float,
    sentiment_a: str,
    sentiment_b: str
) -> str:
    """Generate natural language insight about the comparison."""

    score_a = audit_a.get('confidence_score', 0)
    score_b = audit_b.get('confidence_score', 0)
    position_a = audit_a.get('citation_position_score', 0)
    position_b = audit_b.get('citation_position_score', 0)
    cited_a = audit_a.get("citation_found", False)
    cited_b = audit_b.get("citation_found", False)
    gaps_a = audit_a.get("gaps", [])
    gaps_b = audit_b.get("gaps", [])
    sentiment_order = {"positive": 3, "neutral": 2, "none": 1, "negative": 0}

    # Forced tie-breaker logic: ALWAYS declare a winner
    winner_brand = None
    loser_brand = None
    winning_reason = []

    # Primary: confidence score
    if abs(score_diff) >= 0.05:
        winner_brand = brand_b if score_diff > 0 else brand_a
        loser_brand = brand_a if score_diff > 0 else brand_b
        winning_reason.append("higher confidence score")
    # Tie-breaker 1: position score
    elif abs(position_b - position_a) >= 0.01:
        winner_brand = brand_b if position_b > position_a else brand_a
        loser_brand = brand_a if position_b > position_a else brand_b
        winning_reason.append("earlier citation position")
    # Tie-breaker 2: sentiment
    elif sentiment_order.get(sentiment_b, 0) != sentiment_order.get(sentiment_a, 0):
        winner_brand = brand_b if sentiment_order.get(sentiment_b, 0) > sentiment_order.get(sentiment_a, 0) else brand_a
        loser_brand = brand_a if sentiment_order.get(sentiment_b, 0) > sentiment_order.get(sentiment_a, 0) else brand_b
        winning_reason.append("stronger sentiment")
    # Tie-breaker 3: fewer gaps
    elif len(gaps_a) != len(gaps_b):
        winner_brand = brand_b if len(gaps_b) < len(gaps_a) else brand_a
        loser_brand = brand_a if len(gaps_b) < len(gaps_a) else brand_b
        winning_reason.append("fewer optimization gaps")
    # Tie-breaker 4: citation presence
    elif cited_a != cited_b:
        winner_brand = brand_a if cited_a else brand_b
        loser_brand = brand_b if cited_a else brand_a
        winning_reason.append("citation presence")
    # Final fallback: alphabetical (deterministic)
    else:
        winner_brand = brand_a if brand_a < brand_b else brand_b
        loser_brand = brand_b if brand_a < brand_b else brand_a
        winning_reason.append("marginal technical advantages")

    # Build decisive insight
    insight_parts = []

    # Lead with winner (decisive language)
    if abs(score_diff) >= 0.3:
        insight_parts.append(f"{winner_brand} significantly outperforms {loser_brand} in AI visibility")
    elif abs(score_diff) >= 0.05:
        insight_parts.append(f"{winner_brand} outperforms {loser_brand} in AI visibility")
    else:
        # Close scores: use "edges ahead" language
        insight_parts.append(f"While both brands perform similarly overall, {winner_brand} edges ahead of {loser_brand}")

    # Add winning reason for close matches
    if abs(score_diff) < 0.05 and winning_reason:
        insight_parts.append(f"due to {' and '.join(winning_reason)}")

    # Position difference (if significant)
    if abs(position_diff) >= 0.2:
        if position_diff > 0:
            insight_parts.append(f"{brand_b} appears earlier in AI responses")
        else:
            insight_parts.append(f"{brand_a} appears earlier in AI responses")

    # Sentiment difference (if significant)
    if sentiment_order.get(sentiment_b, 0) > sentiment_order.get(sentiment_a, 0):
        insight_parts.append(f"and is described with stronger {sentiment_b} sentiment")
    elif sentiment_order.get(sentiment_a, 0) > sentiment_order.get(sentiment_b, 0):
        insight_parts.append(f"though {brand_a} benefits from stronger {sentiment_a} sentiment")

    # Citation status (critical differentiator)
    if cited_b and not cited_a:
        insight_parts.append(f"while {loser_brand} is not appearing in AI recommendations at all")
    elif cited_a and not cited_b:
        insight_parts.append(f"despite {brand_a} being the only one currently appearing in AI recommendations")

    # Likely drivers (competitive advantage explanation)
    drivers = []
    if "Low review count" in gaps_a and "Low review count" not in gaps_b:
        drivers.append("higher review volume")
    if "Missing JSON-LD" in gaps_a and "Missing JSON-LD" not in gaps_b:
        drivers.append("stronger structured data presence")

    if drivers:
        insight_parts.append(f". {winner_brand}'s advantage is driven by {' and '.join(drivers)}")
    else:
        insight_parts.append(".")

    return " ".join(insight_parts).replace(" .", ".").replace("  ", " ")


def _generate_competitive_actions(
    brand_a: str,
    brand_b: str,
    audit_a: dict,
    audit_b: dict,
    winner: str
) -> list:
    """Generate actions to help the losing brand catch up."""

    # No more ties - always provide directional actions
    # Even in close matches, focus on how to surpass the competitor

    # Determine which brand needs help
    losing_brand = brand_a if winner == "brand_b" else brand_b
    winning_brand = brand_b if winner == "brand_b" else brand_a
    losing_audit = audit_a if winner == "brand_b" else audit_b
    winning_audit = audit_b if winner == "brand_b" else audit_a

    actions = []

    # Gap-based recommendations
    losing_gaps = set(losing_audit.get("gaps", []))
    winning_gaps = set(winning_audit.get("gaps", []))

    # Gaps that winner doesn't have
    competitive_gaps = losing_gaps - winning_gaps

    if "Missing JSON-LD" in competitive_gaps:
        actions.append({
            "title": "Match Competitor's Structured Data",
            "reason": f"{winning_brand} has structured data implemented while {losing_brand} does not. This gives them a significant algorithmic advantage.",
            "action": f"Implement Schema.org LocalBusiness markup immediately. {winning_brand} is benefiting from machine-readable data that AI models can parse directly.",
            "priority": "high"
        })

    if "Low review count" in competitive_gaps:
        actions.append({
            "title": "Close the Review Gap",
            "reason": f"{winning_brand} likely has substantially more reviews than {losing_brand}, creating a trust signal advantage.",
            "action": f"Launch aggressive review acquisition campaign. Target matching {winning_brand}'s review volume within 90 days.",
            "priority": "high"
        })

    # Position-based recommendations (always add if there's any difference)
    position_a = audit_a.get("citation_position_score", 0.0)
    position_b = audit_b.get("citation_position_score", 0.0)

    if winner == "brand_b" and position_b > position_a + 0.1:
        actions.append({
            "title": "Improve Citation Positioning to Surpass Competitor",
            "reason": f"{winning_brand} appears earlier in AI responses, capturing more attention and clicks.",
            "action": f"Create comparison content positioning {losing_brand} against {winning_brand}. Publish '{losing_brand} vs {winning_brand}' pages and 'Why choose {losing_brand}' content to appear in the same recommendation context.",
            "priority": "high" if position_b > position_a + 0.3 else "medium"
        })
    elif winner == "brand_a" and position_a > position_b + 0.1:
        actions.append({
            "title": "Improve Citation Positioning to Surpass Competitor",
            "reason": f"{winning_brand} appears earlier in AI responses, capturing more attention and clicks.",
            "action": f"Create comparison content positioning {losing_brand} against {winning_brand}. Publish '{losing_brand} vs {winning_brand}' pages and 'Why choose {losing_brand}' content to appear in the same recommendation context.",
            "priority": "high" if position_a > position_b + 0.3 else "medium"
        })

    # Sentiment-based recommendations (always add if there's any difference)
    sentiment_a = audit_a.get("sentiment", "none")
    sentiment_b = audit_b.get("sentiment", "none")
    sentiment_order = {"positive": 3, "neutral": 2, "none": 1, "negative": 0}

    if winner == "brand_b" and sentiment_order.get(sentiment_b, 0) > sentiment_order.get(sentiment_a, 0):
        actions.append({
            "title": "Strengthen Brand Sentiment to Match Competitor",
            "reason": f"{winning_brand} is described with {sentiment_b} sentiment while {losing_brand} has {sentiment_a} sentiment. This sentiment gap directly impacts recommendation frequency.",
            "action": f"To surpass {winning_brand}, {losing_brand} must generate detailed, positive reviews using strong language ('excellent', 'best', 'highly recommend'). Target 50+ new positive reviews within 60 days to shift AI model perception.",
            "priority": "high" if sentiment_order.get(sentiment_b, 0) - sentiment_order.get(sentiment_a, 0) >= 2 else "medium"
        })
    elif winner == "brand_a" and sentiment_order.get(sentiment_a, 0) > sentiment_order.get(sentiment_b, 0):
        actions.append({
            "title": "Strengthen Brand Sentiment to Match Competitor",
            "reason": f"{winning_brand} is described with {sentiment_a} sentiment while {losing_brand} has {sentiment_b} sentiment. This sentiment gap directly impacts recommendation frequency.",
            "action": f"To surpass {winning_brand}, {losing_brand} must generate detailed, positive reviews using strong language ('excellent', 'best', 'highly recommend'). Target 50+ new positive reviews within 60 days to shift AI model perception.",
            "priority": "high" if sentiment_order.get(sentiment_a, 0) - sentiment_order.get(sentiment_b, 0) >= 2 else "medium"
        })

    # Always provide at least one action - even in close matches
    if not actions:
        # Close match: focus on incremental advantages
        score_a = audit_a.get("confidence_score", 0)
        score_b = audit_b.get("confidence_score", 0)

        actions.append({
            "title": f"Surpass {winning_brand} Through Incremental Optimization",
            "reason": f"While {losing_brand} and {winning_brand} are closely matched (scores: {score_a:.2f} vs {score_b:.2f}), {winning_brand} currently edges ahead. Small improvements compound quickly in AI rankings.",
            "action": f"To overtake {winning_brand}, {losing_brand} should: (1) Add Schema.org markup if missing, (2) Launch review acquisition campaign targeting 100+ reviews, (3) Create '{losing_brand} vs {winning_brand}' comparison content, (4) Optimize for local search terms where {winning_brand} appears.",
            "priority": "high",
            "fastest_path": "Review volume + structured data implementation (30-60 day timeline)"
        })

    # Add strategic summary to first action
    if actions:
        actions[0]["winner_reason"] = f"{winning_brand} currently leads due to stronger overall AI visibility signals"
        actions[0]["loser_gap"] = f"{losing_brand} is disadvantaged in citation frequency and positioning"
        if "fastest_path" not in actions[0]:
            actions[0]["fastest_path"] = "Close competitive gaps identified above within 60-90 days"

    return actions
