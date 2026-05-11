"""Run lift simulation for GEO audit."""
from geo_audit_agent.agent import build_geo_audit_agent


def simulate_improved_audit(baseline: dict) -> dict:
    """
    Simulate an improved audit based on baseline.
    Does not fake impossible improvements.
    Preserves raw responses for before/after comparison.
    Includes simulation confidence and uncertainty indicators.
    """
    improved = baseline.copy()
    brand = baseline.get("brand")
    category = baseline.get("category", "service")

    # Store original raw response as "before"
    before_raw_response = baseline.get("raw_response", "")

    # Scenario 1: No presence -> Improvement to weak/medium
    if not baseline.get("citation_found"):
        improved["citation_found"] = True
        improved["citation_position_score"] = 0.45
        improved["sentiment"] = "neutral"
        improved["confidence_score"] = 0.42
        improved["raw_response"] = f"If you're looking for great {category} options, here are some solid choices.\n\n{brand} is a reliable option that many people recommend. They offer consistent quality and good service. Other popular choices include established brands in the area.\n\nFor a well-rounded experience, {brand} is worth considering alongside the other top options."
        improved["before_raw_response"] = before_raw_response
        improved["simulation_confidence"] = "medium"
        improved["simulation_notes"] = {
            "disclaimer": "This is a simulated improvement based on known ranking factors. Actual AI responses are highly dynamic and may vary depending on model updates, query phrasing, and regional data availability.",
            "expected_outcome": "Brand becomes visible in AI recommendations",
            "alternative_outcomes": [
                "Brand may appear but with neutral or weak positioning",
                "Improvement may take 60-90 days to reflect in AI training data"
            ],
            "risk_factors": [
                "Insufficient review volume may limit visibility",
                "Competitors improving simultaneously could offset gains",
                "Inconsistent data across sources may delay recognition"
            ]
        }

    # Scenario 2: Weak presence -> Improvement to strong
    elif baseline.get("confidence_score", 0.0) < 0.75:
        improved["citation_position_score"] = 0.82
        improved["sentiment"] = "positive"
        improved["confidence_score"] = 0.78
        improved["raw_response"] = f"If you're looking for the best {category} options, {brand} should be at the top of your list.\n\n{brand} consistently delivers excellent quality and has built a strong reputation. Customers frequently praise their attention to detail and reliable service. While there are other good options available, {brand} stands out for its commitment to quality.\n\nFor anyone seeking top-tier {category} services, {brand} is highly recommended."
        improved["before_raw_response"] = before_raw_response
        improved["simulation_confidence"] = "high"
        improved["simulation_notes"] = {
            "disclaimer": "This is a simulated improvement based on known ranking factors. Actual AI responses are highly dynamic and may vary depending on model updates, query phrasing, and regional data availability.",
            "expected_outcome": "Brand moves to top-tier positioning in AI recommendations",
            "alternative_outcomes": [
                "Brand may improve but not reach top position if competitors are very strong",
                "Sentiment may remain neutral if review language is not sufficiently positive"
            ],
            "risk_factors": [
                "Competitors with stronger review volume may maintain lead",
                "Timing of AI model updates may delay visibility improvements"
            ]
        }

    # Scenario 3: Strong presence -> Slight improvement
    else:
        current_score = baseline.get("confidence_score", 0.0)
        improved["simulation_confidence"] = "low"
        improved["simulation_notes"] = {
            "disclaimer": "This is a simulated improvement based on known ranking factors. Actual AI responses are highly dynamic and may vary depending on model updates, query phrasing, and regional data availability.",
            "expected_outcome": "Incremental strengthening of already-strong position",
            "alternative_outcomes": [
                "Improvements may be marginal as brand is already well-positioned",
                "Gains may be offset by competitor improvements"
            ],
            "risk_factors": [
                "Diminishing returns at high confidence levels",
                "Market saturation may limit further gains"
            ]
        }

        if current_score >= 0.85:
            improved["confidence_score"] = min(current_score + 0.02, 0.98)
            improved["simulation_notes"]["expected_outcome"] = "Already strong visibility. Focus on maintenance and monitoring."
        else:
            improved["confidence_score"] = min(current_score + 0.05, 0.85)

        improved["raw_response"] = f"When it comes to exceptional {category} options, {brand} is consistently ranked among the very best.\n\n{brand} has earned its reputation through years of outstanding service and quality. They're often the first recommendation from satisfied customers. The combination of expertise, reliability, and customer focus makes {brand} a standout choice.\n\nFor the best {category} experience, {brand} is the clear top choice."
        improved["before_raw_response"] = before_raw_response

    return improved


def run_lift_simulation(brand_name: str, category: str, city: str, business_data: dict = None):
    """
    Run lift simulation for a business using the industry-aware audit agent.

    Args:
        brand_name: Business name
        category: Business category (e.g., 'dental clinic')
        city: City location
        business_data: Business data dict

    Returns:
        Complete audit results with industry-specific template, normalized for dashboard.
    """
    print("RUN_LIFT_SIMULATION_ACTIVE_DIRECT_BYPASS")
    print(f"RUN_LIFT_INPUT_CATEGORY: {repr(category)}")

    if business_data is None:
        business_data = {}

    # Build and invoke the agent directly
    agent = build_geo_audit_agent()

    inputs = {
        "brand": brand_name,
        "brand_name": brand_name,
        "category": category,
        "city": city,
        "business_context": business_data,
        "force_mock": business_data.get("force_mock", True),
        "use_real": business_data.get("use_real", False),
    }

    results = agent.invoke(inputs)

    # Normalize the result to match dashboard expectations
    normalized = {
        "brand": results.get("brand_name", brand_name),
        "brand_name": results.get("brand_name", brand_name),
        "category": results.get("category", category),
        "city": results.get("city", city),
        "template_used": results.get("template_used", "Generic"),
        "citation_found": results.get("citation_found", False),
        "confidence_score": results.get("confidence_score", 0.0),
        "sentiment": results.get("sentiment", "none"),
        "raw_response": results.get("raw_response", ""),
        "competitors": results.get("competitors", []),
        "strengths": results.get("strengths", []),
        "gaps": results.get("gaps", []),
        "remediation": results.get("remediation", []),
        "planned_actions": results.get("planned_actions", []),
        "mode": results.get("mode", "simulated"),
        "call_path": "run_lift_simulation_direct_bypass",
    }

    return normalized


if __name__ == '__main__':
    # Example: Dental Solutions Islamabad
    dental_data = {
        "business_context": (
            "Dental Solutions Islamabad is a dental clinic in Islamabad. "
            "Services include braces, dental implants, teeth whitening, root canal, "
            "emergency dental care, pediatric dentistry, and cosmetic dentistry. "
            "The clinic emphasizes hygiene, painless treatment, professional dentists, "
            "appointment booking, and patient care."
        ),
        "force_mock": True,
    }

    results = run_lift_simulation(
        brand_name="Dental Solutions Islamabad",
        category="dental clinic",
        city="Islamabad",
        business_data=dental_data
    )

    print(f"Brand: {results['brand_name']}")
    print(f"Category: {results['category']}")
    print(f"Template: {results['template_used']}")
    print(f"Gaps: {len(results['gaps'])}")
    print(f"Remediation: {len(results['remediation'])}")
