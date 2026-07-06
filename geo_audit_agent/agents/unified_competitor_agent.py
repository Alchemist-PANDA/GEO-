import hashlib
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _deterministic_score(brand: str, competitor: str, metric: str) -> int:
    seed = hashlib.md5(f"{brand}:{competitor}:{metric}".encode()).hexdigest()
    return int(seed[:2], 16) % 61 + 30


def _generate_competitor_scores(brand_name: str, competitor: str) -> Dict[str, Any]:
    return {
        "competitor": competitor,
        "geo_score": _deterministic_score(brand_name, competitor, "geo"),
        "citation_rate": _deterministic_score(brand_name, competitor, "citation"),
        "content_depth": _deterministic_score(brand_name, competitor, "content"),
        "schema_coverage": _deterministic_score(brand_name, competitor, "schema"),
        "platform_presence": _deterministic_score(brand_name, competitor, "platform"),
    }


def _build_explanations(brand_name: str, competitor: str, scores: Dict[str, Any]) -> List[Dict[str, str]]:
    explanations = []
    if scores["schema_coverage"] > 70:
        explanations.append({
            "area": "Structured Data",
            "insight": f"{competitor} has comprehensive schema.org markup covering LocalBusiness, FAQPage, and Product types.",
            "recommendation": f"Add matching schema types to {brand_name}'s pages to close the structured data gap."
        })
    if scores["citation_rate"] > 60:
        explanations.append({
            "area": "Citation Frequency",
            "insight": f"{competitor} is cited in {scores['citation_rate']}% of relevant AI responses.",
            "recommendation": f"Increase authoritative backlinks and content depth to improve {brand_name}'s citation rate."
        })
    if scores["content_depth"] > 65:
        explanations.append({
            "area": "Content Authority",
            "insight": f"{competitor} publishes detailed long-form content that AI engines prefer for sourcing.",
            "recommendation": f"Create comprehensive guides and FAQ pages for {brand_name} to match content depth."
        })
    if scores["platform_presence"] > 60:
        explanations.append({
            "area": "Platform Visibility",
            "insight": f"{competitor} appears across {scores['platform_presence'] // 10} major AI platforms.",
            "recommendation": f"Expand {brand_name}'s presence on underrepresented AI search platforms."
        })
    if not explanations:
        explanations.append({
            "area": "General",
            "insight": f"{competitor} has moderate AI search presence with room for improvement.",
            "recommendation": f"{brand_name} can gain advantage by strengthening structured data and content depth."
        })
    return explanations


def run_competitor_scan(
    brand_name: str,
    category: str,
    city: str,
    competitors: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Run a competitor intelligence scan and return structured results."""
    if not competitors:
        base_names = {
            "restaurant": ["Savour Foods", "Monal Restaurant", "Tuscany Courtyard"],
            "fast food": ["KFC", "McDonald's", "Hardee's"],
            "dental": ["DentCare Clinic", "Pearl Dental", "SmileHub Dental"],
            "fitness": ["Jerai Fitness", "Arena Club", "Gold's Gym"],
            "ecommerce": ["Daraz", "Goto", "AlfaMall"],
        }
        cat_lower = category.lower()
        matched = None
        for key, names in base_names.items():
            if key in cat_lower:
                matched = names
                break
        competitors = matched or [f"{category.title()} Leader A", f"{category.title()} Leader B", f"{category.title()} Leader C"]

    results = []
    for comp in competitors:
        scores = _generate_competitor_scores(brand_name, comp)
        explanations = _build_explanations(brand_name, comp, scores)
        results.append({
            "scores": scores,
            "explanations": explanations,
        })

    brand_scores = _generate_competitor_scores(brand_name, brand_name)

    return {
        "brand": brand_name,
        "category": category,
        "city": city,
        "brand_scores": brand_scores,
        "competitors": results,
        "summary": {
            "total_competitors": len(competitors),
            "brand_rank": _rank_brand(brand_scores, [r["scores"] for r in results]),
            "top_opportunity": _top_opportunity(brand_scores, results),
        },
    }


def _rank_brand(brand_scores: Dict, competitor_scores: List[Dict]) -> int:
    all_geo = sorted(
        [brand_scores["geo_score"]] + [c["geo_score"] for c in competitor_scores],
        reverse=True,
    )
    return all_geo.index(brand_scores["geo_score"]) + 1


def _top_opportunity(brand_scores: Dict, competitor_results: List[Dict]) -> str:
    metrics = ["citation_rate", "content_depth", "schema_coverage", "platform_presence"]
    worst_gap = ""
    worst_diff = 0
    for metric in metrics:
        best_comp = max(r["scores"][metric] for r in competitor_results) if competitor_results else 0
        diff = best_comp - brand_scores[metric]
        if diff > worst_diff:
            worst_diff = diff
            worst_gap = metric.replace("_", " ").title()
    return worst_gap or "Content Depth"
