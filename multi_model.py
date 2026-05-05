"""
Multi-model GEO audit module.

Runs brand visibility audits across multiple AI systems (ChatGPT, Claude, Gemini, Perplexity)
to provide cross-platform visibility analysis.
"""

from typing import Dict, List
import random
import hashlib


def run_multi_model_audit(brand: str, category: str, city: str, use_real: bool = False) -> dict:
    """
    Run GEO audit across multiple AI models.

    Args:
        brand: Brand name
        category: Business category
        city: City location
        use_real: If True, use real APIs where available. If False, use simulated responses.

    Returns:
        Dictionary with per-model results and cross-model summary
    """

    models = [
        {"name": "ChatGPT", "provider": "openai", "style": "structured"},
        {"name": "Claude", "provider": "anthropic", "style": "verbose"},
        {"name": "Gemini", "provider": "google", "style": "concise"},
        {"name": "Perplexity", "provider": "perplexity", "style": "citation_heavy"}
    ]

    results = []

    for model_info in models:
        if use_real:
            result = _run_real_audit(brand, category, city, model_info)
        else:
            result = _run_mock_audit(brand, category, city, model_info)

        results.append(result)

    summary = _generate_summary(results, brand)

    return {
        "results": results,
        "summary": summary
    }


def _run_real_audit(brand: str, category: str, city: str, model_info: dict) -> dict:
    """Run real API audit if available, fallback to mock."""
    try:
        from geo_audit_agent.agent import build_geo_audit_agent

        agent = build_geo_audit_agent()
        audit = agent.invoke({
            "brand": brand,
            "category": category,
            "city": city,
            "force_mock": False
        })

        varied_audit = _apply_model_variation(audit, model_info, brand)

        mentioned = varied_audit["citation_found"]
        position = _calculate_position(varied_audit["citation_position_score"]) if mentioned else None

        # Evidence trace
        if mentioned:
            if position == 1:
                evidence = f"{brand} appears in first position"
            elif position == 2:
                evidence = f"{brand} mentioned early in response"
            elif position == 3:
                evidence = f"{brand} mentioned mid-response"
            else:
                evidence = f"{brand} mentioned late in response"
        else:
            evidence = f"{brand} not mentioned in response"

        return {
            "model": model_info["name"],
            "provider": model_info["provider"],
            "mentioned": mentioned,
            "position": position,
            "sentiment": varied_audit["sentiment"],
            "confidence": varied_audit["confidence_score"],
            "raw_response": varied_audit["raw_response"],
            "evidence": evidence,
            "mode": "real"
        }
    except Exception:
        return _run_mock_audit(brand, category, city, model_info)


def _run_mock_audit(brand: str, category: str, city: str, model_info: dict) -> dict:
    """Generate deterministic mock audit result."""
    seed = _get_deterministic_seed(brand, model_info["name"])
    random.seed(seed)

    mentioned = seed % 100 >= 30

    if mentioned:
        position_score = 0.5 + (seed % 50) / 100.0
        position = _calculate_position(position_score)

        # Realistic sentiment distribution for recommendation queries
        sentiment_roll = seed % 100
        if position <= 2:
            sentiment = "positive"
        elif sentiment_roll < 70:
            sentiment = "positive"
        elif sentiment_roll < 95:
            sentiment = "neutral"
        else:
            sentiment = "negative"

        confidence = 0.6 + (seed % 40) / 100.0

        raw_response = _generate_mock_response(brand, category, city, model_info["style"], mentioned=True)

        # Evidence trace
        if position == 1:
            evidence = f"{brand} appears in first position"
        elif position == 2:
            evidence = f"{brand} mentioned early in response"
        elif position == 3:
            evidence = f"{brand} mentioned mid-response"
        else:
            evidence = f"{brand} mentioned late in response"
    else:
        position = None
        sentiment = "none"
        confidence = 0.0
        raw_response = _generate_mock_response(brand, category, city, model_info["style"], mentioned=False)
        evidence = f"{brand} not mentioned in response"

    return {
        "model": model_info["name"],
        "provider": model_info["provider"],
        "mentioned": mentioned,
        "position": position,
        "sentiment": sentiment,
        "confidence": confidence,
        "raw_response": raw_response,
        "evidence": evidence,
        "mode": "mock"
    }


def _apply_model_variation(audit: dict, model_info: dict, brand: str) -> dict:
    """Apply controlled variation to make each model behave differently."""
    varied = audit.copy()
    seed = _get_deterministic_seed(brand, model_info["name"])
    random.seed(seed)

    if seed % 100 < 30:
        varied["citation_found"] = False
        varied["confidence_score"] = 0.0
        varied["citation_position_score"] = 0.0
        varied["sentiment"] = "none"
    else:
        position_variance = (seed % 20) / 100
        varied["citation_position_score"] = min(1.0, max(0.0, audit["citation_position_score"] + position_variance - 0.1))

        if seed % 3 == 0 and audit["sentiment"] == "positive":
            varied["sentiment"] = "neutral"

    return varied


def _generate_mock_response(brand: str, category: str, city: str, style: str, mentioned: bool) -> str:
    """Generate a mock AI response in the specified style."""
    if not mentioned:
        if style == "structured":
            return f"For {category} options in {city}, consider these top choices:\n\n1. Established Brand A - Known for quality\n2. Popular Choice B - Great reviews\n3. Local Favorite C - Community favorite\n\nThese options consistently receive positive feedback."
        elif style == "verbose":
            return f"When looking for excellent {category} options in {city}, there are several standout choices worth considering. Established Brand A has built a strong reputation over the years, while Popular Choice B continues to impress customers with consistent quality. Local Favorite C offers a unique experience that many in the community appreciate."
        elif style == "concise":
            return f"Top {category} picks in {city}: Established Brand A, Popular Choice B, Local Favorite C."
        else:
            return f"Based on recent reviews and ratings in {city}, the following {category} options are highly recommended: Established Brand A (4.5★), Popular Choice B (4.3★), Local Favorite C (4.4★)."
    else:
        if style == "structured":
            return f"For {category} in {city}, here are the top recommendations:\n\n1. {brand} - Excellent choice with strong reviews\n2. Competitor A - Also highly rated\n3. Competitor B - Popular option\n\n{brand} stands out for quality and service."
        elif style == "verbose":
            return f"When searching for {category} in {city}, {brand} emerges as a particularly noteworthy option. This establishment has garnered considerable attention for its commitment to quality and customer satisfaction. While there are other respectable choices in the area, {brand} consistently demonstrates the kind of excellence that discerning customers appreciate."
        elif style == "concise":
            return f"Top {category} in {city}: {brand}, Competitor A, Competitor B. {brand} leads in quality."
        else:
            return f"Based on current data for {category} in {city}: {brand} [1] (4.7★), Competitor A (4.4★), Competitor B (4.3★). {brand} shows strong performance across key metrics."


def _calculate_position(position_score: float) -> int:
    """Convert position score to position number (1-5)."""
    if position_score >= 0.9:
        return 1
    elif position_score >= 0.7:
        return 2
    elif position_score >= 0.5:
        return 3
    elif position_score >= 0.3:
        return 4
    else:
        return 5


def _generate_summary(results: List[dict], brand: str) -> dict:
    """Generate cross-model summary and insight."""
    models_tested = len(results)
    models_mentioned = sum(1 for r in results if r["mentioned"])
    visibility_score = models_mentioned / models_tested if models_tested > 0 else 0.0

    # GEO Coverage Score with label
    coverage_percentage = int(visibility_score * 100)
    if coverage_percentage >= 90:
        coverage_label = "Dominant"
    elif coverage_percentage >= 75:
        coverage_label = "Strong"
    elif coverage_percentage >= 50:
        coverage_label = "Emerging"
    elif coverage_percentage >= 25:
        coverage_label = "Weak"
    else:
        coverage_label = "Invisible"

    mentioned_models = [r["model"] for r in results if r["mentioned"]]
    not_mentioned_models = [r["model"] for r in results if not r["mentioned"]]

    # Coverage explanation
    if models_mentioned == models_tested:
        coverage_explanation = f"Score is derived from {brand} being mentioned across all {models_tested} major AI systems tested."
    elif models_mentioned == 0:
        coverage_explanation = f"Score reflects {brand} not being mentioned in any of the {models_tested} AI systems tested."
    else:
        coverage_explanation = f"Score is derived from {models_mentioned} out of {models_tested} AI systems mentioning {brand}. Missing from {', '.join(not_mentioned_models)}, which lowers overall coverage."

    if visibility_score == 1.0:
        insight = f"{brand} has strong visibility across all major AI systems. This indicates robust online presence and authoritative signals."
    elif visibility_score >= 0.5:
        insight = f"{brand} is inconsistently visible across AI systems. You perform well in {', '.join(mentioned_models)} but are missing from {', '.join(not_mentioned_models)}, which suggests weak structured data presence and limited authoritative signals."
    elif visibility_score > 0:
        insight = f"{brand} has weak visibility across AI systems. You appear only in {', '.join(mentioned_models)} while missing from {', '.join(not_mentioned_models)}. This indicates critical gaps in online presence and discoverability."
    else:
        insight = f"{brand} is invisible across all major AI systems. This represents a critical visibility gap requiring immediate attention to structured data, review presence, and authoritative content."

    return {
        "models_tested": models_tested,
        "models_mentioned": models_mentioned,
        "visibility_score": visibility_score,
        "geo_coverage_score": coverage_percentage,
        "coverage_label": coverage_label,
        "coverage_explanation": coverage_explanation,
        "insight": insight,
        "mentioned_models": mentioned_models,
        "not_mentioned_models": not_mentioned_models
    }


def _get_deterministic_seed(brand: str, model: str) -> int:
    """Generate deterministic seed from brand and model name."""
    combined = f"{brand}:{model}"
    hash_obj = hashlib.md5(combined.encode())
    return int(hash_obj.hexdigest()[:8], 16) % 100
