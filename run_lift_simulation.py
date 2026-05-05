import argparse
import json
import os
import sys
import re
from datetime import datetime
from geo_audit_agent.agent import build_geo_audit_agent

def compare_audits(baseline: dict, improved: dict) -> dict:
    """Compare baseline and improved audits to calculate lift."""
    before_score = baseline.get("confidence_score", 0.0)
    after_score = improved.get("confidence_score", 0.0)
    absolute_lift = after_score - before_score
    percentage_lift = (absolute_lift / before_score * 100) if before_score > 0 else 0

    if absolute_lift > 0.1:
        summary = f"Significant improvement: confidence increased by {percentage_lift:.1f}%"
    elif absolute_lift > 0:
        summary = f"Moderate improvement: confidence increased by {percentage_lift:.1f}%"
    else:
        summary = "No significant change in confidence score"

    return {
        "before_score": before_score,
        "after_score": after_score,
        "absolute_lift": round(absolute_lift, 4),
        "percentage_lift": round(percentage_lift, 2),
        "summary": summary
    }

def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

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
        improved["confidence_score"] = min(baseline.get("confidence_score", 0.0) + 0.05, 0.85)
        improved["raw_response"] = f"When it comes to exceptional {category} options, {brand} is consistently ranked among the very best.\n\n{brand} has earned its reputation through years of outstanding service and quality. They're often the first recommendation from satisfied customers. The combination of expertise, reliability, and customer focus makes {brand} a standout choice.\n\nFor the best {category} experience, {brand} is the clear top choice."
        improved["before_raw_response"] = before_raw_response
        improved["simulation_confidence"] = "low"
        improved["simulation_notes"] = {
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

    return improved

def main():
    parser = argparse.ArgumentParser(description="GEO Audit Lift Simulation")
    parser.add_argument("--brand", required=True, help="Brand name")
    parser.add_argument("--category", required=True, help="Category")
    parser.add_argument("--city", required=True, help="City")

    args = parser.parse_args()
    brand_slug = slugify(args.brand)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"--- GEO Lift Simulation for '{args.brand}' ---")

    # 1. Run Baseline Audit
    print("1. Running baseline audit...")
    agent = build_geo_audit_agent()
    baseline = agent.invoke({
        "brand": args.brand,
        "category": args.category,
        "city": args.city
    })

    # 2. Generate Remediation
    print("2. Generating targeted remediation...")
    # Remediation is already inside agent.invoke result now
    remediations = baseline.get("remediation", [])

    # 3. Simulate Improved Audit
    print("3. Simulating improved follow-up audit...")
    improved = simulate_improved_audit(baseline)

    # 4. Compare
    print("4. Calculating lift...")
    lift_report = compare_audits(baseline, improved)

    # Combine into full report
    full_report = {
        "brand": args.brand,
        "simulation_timestamp": datetime.now().isoformat(),
        "baseline": baseline,
        "improved": improved,
        "lift": lift_report,
        "remediations": remediations
    }

    # Save JSON
    os.makedirs("data/lift_reports", exist_ok=True)
    output_path = f"data/lift_reports/{brand_slug}_{timestamp}.json"
    with open(output_path, "w") as f:
        json.dump(full_report, f, indent=4)

    # Print Summary
    print("\n" + "="*50)
    print(f"LIFT REPORT: {args.brand}")
    print("-" * 50)
    print(f"Baseline Score:    {lift_report['before_score']}")
    print(f"Improved Score:    {lift_report['after_score']}")
    print(f"Absolute Lift:     +{lift_report['absolute_lift']}")
    print(f"Percentage Lift:   {lift_report['percentage_lift']}%")
    print("-" * 50)
    print(f"Summary: {lift_report['summary']}")
    print("="*50)
    print(f"Full report saved to: {output_path}\n")

if __name__ == "__main__":
    main()
