"""
Multi-model GEO audit module.

Runs brand visibility audits across multiple AI systems (ChatGPT, Claude, Gemini, Perplexity)
to provide cross-platform visibility analysis.

IMPORTANT: This module supports both Live API Mode and Simulated Demo Mode.
Simulated mode uses deterministic sample outputs for demonstration purposes only.
"""

import hashlib


def run_multi_model_audit(
    brand: str, category: str, city: str, use_real: bool = False, user_id: str | None = None,
) -> dict:
    """
    Run GEO audit across multiple AI models.

    Args:
        brand: Brand name
        category: Business category
        city: City location
        use_real: If True, attempt live API calls. If False, use simulated responses.
        user_id: The ID of the user running the audit (for tier checks).

    Returns:
        Dictionary with per-model results and cross-model summary
    """
    from geo_audit_agent.auth.user import (
        can_run_audit,
        get_available_models,
        get_user_tier,
        increment_audit_usage,
        is_model_real,
    )

    if user_id and not can_run_audit(user_id):
        return {"error": "Audit limit reached. Please upgrade your plan."}

    all_models = [
        {"name": "ChatGPT", "provider": "openai", "style": "structured"},
        {"name": "Gemini", "provider": "google", "style": "concise"},
        {"name": "Meta.ai", "provider": "meta", "style": "verbose"},
        {"name": "Claude.ai", "provider": "anthropic", "style": "structured"},
        {"name": "DeepSeek", "provider": "deepseek", "style": "citation_heavy"},
        {"name": "Perplexity", "provider": "perplexity", "style": "structured"},
        {"name": "Grok", "provider": "x", "style": "concise"}
    ]

    tier = get_user_tier(user_id) if user_id else "free"
    allowed_models = get_available_models(user_id or "")

    # If free tier, show all standard models but force mock
    if tier == "free" or not allowed_models:
        allowed_models = ["ChatGPT", "Gemini", "Meta.ai", "Claude.ai", "DeepSeek"]

    results = []

    for model_info in all_models:
        if model_info["name"] not in allowed_models:
            continue

        # Direct/local calls have no entitlement context. When the caller
        # explicitly requests live mode, attempt the adapter and report any
        # configuration failure; never substitute a fixture.
        can_use_real = user_id is None or (is_model_real(user_id, model_info["name"]) and tier != "free")

        if use_real and can_use_real:
            result = _run_real_audit(brand, category, city, model_info)
        elif use_real:
            result = {
                "model": model_info["name"], "provider": model_info["provider"], "mentioned": None,
                "position": None, "sentiment": "unscored", "confidence": None, "raw_response": "",
                "evidence": "No observation: this provider is not included in the current entitlement",
                "evidence_type": "error", "mode": "failed", "error": "entitlement_required",
            }
        else:
            result = _run_simulated_audit(brand, category, city, model_info)

        results.append(result)

    # Record usage
    if user_id and any(result.get("mode") in {"live", "cached"} for result in results):
        increment_audit_usage(user_id)

    summary = _generate_summary(results, brand, use_real)

    return {
        "results": results,
        "summary": summary
    }


def _run_real_audit(brand: str, category: str, city: str, model_info: dict) -> dict:
    """Run one real provider query. Failures stay failures, never fixtures."""
    try:
        from geo_audit_agent.metrics.observation import interpret_observation
        from geo_audit_agent.providers import get_provider_adapter

        adapter = get_provider_adapter(model_info["provider"])
        prompt = f"What are the best {category} options in {city}? Explain your recommendations and cite sources."
        provider_result = adapter.query(prompt, prompt_id="category-recommendation", prompt_version="1.0")
        interpretation = interpret_observation(provider_result.text, brand)
        mentioned = interpretation.mentioned
        position = interpretation.position

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
            "recommended": interpretation.recommended,
            "recommendation": interpretation.recommended,
            "position": position,
            "sentiment": interpretation.sentiment,
            "confidence": interpretation.confidence,
            "citation_urls": interpretation.citation_urls,
            "raw_response": provider_result.text,
            "evidence": evidence,
            "evidence_type": "live_response",
            "mode": provider_result.mode.value,
            "prompt_id": provider_result.prompt_id,
            "prompt_version": provider_result.prompt_version,
            "latency_ms": provider_result.latency_ms,
            "input_tokens": provider_result.input_tokens,
            "output_tokens": provider_result.output_tokens,
            "cost_usd": provider_result.cost_usd,
        }
    except Exception as exc:
        return {
            "model": model_info["name"],
            "provider": model_info["provider"],
            "mentioned": None,
            "position": None,
            "sentiment": "unscored",
            "confidence": None,
            "raw_response": "",
            "evidence": "No observation: provider execution failed or is not configured",
            "evidence_type": "error",
            "mode": "failed",
            "error": type(exc).__name__,
        }


def _run_simulated_audit(brand: str, category: str, city: str, model_info: dict) -> dict:
    """Generate deterministic simulated audit result for demonstration purposes."""
    seed = _get_deterministic_seed(brand, model_info["name"])

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

        raw_response = _generate_simulated_response(brand, category, city, model_info["style"], mentioned=True)

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
        raw_response = _generate_simulated_response(brand, category, city, model_info["style"], mentioned=False)
        evidence = f"{brand} not mentioned in response"

    return {
        "model": model_info["name"],
        "provider": model_info["provider"],
        "mentioned": mentioned,
        "recommended": mentioned,
        "recommendation": mentioned,
        "position": position,
        "sentiment": sentiment,
        "confidence": confidence,
        "raw_response": raw_response,
        "evidence": evidence,
        "evidence_type": "simulated",
        "mode": "fixture",
        "disclosure": "Deterministic demo fixture; not a provider response",
        "prompt_id": "category-recommendation",
        "prompt_version": "1.0",
        "citation_urls": [],
    }


def _apply_model_variation(audit: dict, model_info: dict, brand: str) -> dict:
    """Apply controlled variation to make each model behave differently."""
    varied = audit.copy()
    seed = _get_deterministic_seed(brand, model_info["name"])

    if seed % 100 < 30:
        varied["citation_found"] = False
        varied["confidence_score"] = 0.0
        varied["citation_position_score"] = 0.0
        varied["sentiment"] = "none"
    else:
        position_variance = (seed % 20) / 100
        base_position = audit.get("citation_position_score", 0.5)
        varied["citation_position_score"] = min(1.0, max(0.0, base_position + position_variance - 0.1))

        if seed % 3 == 0 and audit["sentiment"] == "positive":
            varied["sentiment"] = "neutral"

    return varied


def _generate_simulated_response(brand: str, category: str, city: str, style: str, mentioned: bool) -> str:
    """Generate a simulated AI response in the specified style for demonstration purposes."""
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


def _generate_summary(results: list[dict], brand: str, use_real: bool = False) -> dict:
    """Generate cross-model summary and insight with data source labeling."""
    completed = [r for r in results if r.get("mode") != "failed"]
    models_tested = len(completed)
    models_requested = len(results)
    models_mentioned = sum(1 for r in completed if r["mentioned"])
    visibility_score = models_mentioned / models_tested if models_tested > 0 else 0.0

    # Determine data source
    live_count = sum(1 for r in completed if r.get("mode") in {"live", "cached", "live_api"})
    simulated_count = sum(1 for r in completed if r.get("mode") in {"fixture", "simulated"})

    if models_tested == 0:
        data_source = "unavailable"
    elif live_count == models_tested:
        data_source = "live_api"
    elif simulated_count == models_tested:
        data_source = "simulated"
    else:
        data_source = "mixed"

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

    mentioned_models = [r["model"] for r in completed if r["mentioned"]]
    not_mentioned_models = [r["model"] for r in completed if not r["mentioned"]]

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
        "models_requested": models_requested,
        "models_failed": models_requested - models_tested,
        "sample_size": models_tested,
        "models_mentioned": models_mentioned,
        "visibility_score": visibility_score,
        "geo_coverage_score": coverage_percentage,
        "coverage_label": coverage_label,
        "coverage_explanation": coverage_explanation,
        "insight": insight,
        "mentioned_models": mentioned_models,
        "not_mentioned_models": not_mentioned_models,
        "data_source": data_source
    }


def _get_deterministic_seed(brand: str, model: str) -> int:
    """Generate deterministic seed from brand and model name."""
    combined = f"{brand}:{model}"
    hash_obj = hashlib.md5(combined.encode())
    return int(hash_obj.hexdigest()[:8], 16) % 100
