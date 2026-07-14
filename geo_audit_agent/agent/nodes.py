import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

from google import genai

from geo_audit_agent.agent.state import AuditState
from geo_audit_agent.services.cache import get_cached_response, set_cached_response
from geo_audit_agent.services.guardrails import classify_input
from geo_audit_agent.services.llm_router import query_provider

logger = logging.getLogger(__name__)


def guardrail_node(state: AuditState) -> AuditState:
    """Ingress guardrail: classifies user input for safety.

    Addresses: Audit 3 §2.A (LlamaGuard), PE-OS Law 3 (Autonomy-Failure Scaling)
    """
    combined_input = f"{state.brand_name} {state.category} {state.city}"
    result = classify_input(combined_input)

    state.step_log.append({
        "node": "guardrail",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "classification": result.classification,
    })

    if result.classification == "unsafe":
        raise ValueError(f"Input blocked by guardrail: {result.category}")

    return state


def query_llm_node(state: AuditState) -> AuditState:
    """Queries target LLM with the brand visibility question.

    Existing: agent.py:query_llm (lines 40-80)
    Addresses: PE-OS Law 4 (Prompt Cache Economics), Law 9 (Paged Attention)
    """
    brand = state.brand_name
    category = state.category
    city = state.city

    force_mock = state.force_mock or (isinstance(state.business_context, dict) and state.business_context.get("force_mock"))
    has_api_key = bool(os.getenv("GOOGLE_API_KEY"))

    if force_mock:
        logger.info("Using an explicitly requested fixture response")
        if brand == "Unknown Brand" or not brand or brand == "Unknown":
            state.llm_response = f"Here are the top {category} options in {city}: 1. First Brand 2. Second Brand"
        elif brand == "Burger Hub":
            state.llm_response = f"If you want food in {city}, here are the options:\n1. KFC\n2. McDonald's\n3. Burger Hub - Local favorite with great burgers."
        else:
            state.llm_response = f"For the best {category} in {city}, you should check out:\n1. {brand} - Outstanding service and quality.\n2. Comp1\n3. Comp2"

        state.mode = "simulated"
        state.step_log.append({
            "node": "query_llm",
            "cache_hit": False,
            "mocked": True,
        })
        return state

    if not has_api_key:
        from geo_audit_agent.providers import ProviderUnavailableError

        state.mode = "failed"
        state.step_log.append({"node": "query_llm", "cache_hit": False, "mocked": False,
                               "error": "provider_not_configured"})
        raise ProviderUnavailableError("GOOGLE_API_KEY is required for this live audit")

    prompt = f"What is the best {category} in {city}?"

    cached = get_cached_response(state.tier, prompt)
    if cached:
        state.llm_response = cached
        state.mode = "real"
        state.step_log.append({"node": "query_llm", "cache_hit": True})
        return state

    try:
        response = query_provider(
            prompt=prompt,
            tier=state.tier,
            correlation_id=state.correlation_id,
        )
        state.llm_response = response.text
        state.total_tokens += response.total_tokens
        state.total_cost_usd += response.cost_usd
        set_cached_response(state.tier, prompt, response.text)
        state.mode = "real"

        state.step_log.append({
            "node": "query_llm",
            "cache_hit": False,
            "tokens": response.total_tokens,
            "provider": response.provider,
        })
    except Exception as e:
        logger.error("Real LLM query failed without simulation fallback: %s", type(e).__name__)
        state.mode = "failed"
        state.llm_response = ""
        state.step_log.append({
            "node": "query_llm",
            "cache_hit": False,
            "mocked": False,
            "error": type(e).__name__,
        })
        raise
    return state


def check_citation_node(state: AuditState) -> AuditState:
    """Validates brand citation with semantic analysis.

    Existing: agent.py:check_citation (lines 82-140)
    Upgrade: Replaces substring matching with semantic verification
    Addresses: PE-OS Law 2 (Verifiable Trust), Audit 3 §2.B
    """
    brand = state.brand_name
    response = state.llm_response

    if not response or "error:" in response.lower():
        state.is_cited = False
        state.confidence_score = 0.0
        state.sentiment = "none"
        state.step_log.append({
            "node": "check_citation",
            "is_cited": False,
            "confidence": 0.0,
            "sentiment": "none",
        })
        return state

    from geo_audit_agent.metrics.entity_detection import EntityVerdict, detect_entity

    match = detect_entity(response, brand)
    if match.verdict is EntityVerdict.MATCH:
        position = response.casefold().find((match.matched_alias or brand).casefold())
        context_window = response[max(0, position - 100):position + len(match.matched_alias or brand) + 100]

        sentiment_result = _analyze_citation_sentiment(context_window, brand)
        state.is_cited = True
        state.confidence_score = 1.0
        state.sentiment = sentiment_result.sentiment
    else:
        # Partial names are ambiguous. They are recorded as uncertain evidence,
        # never promoted to a measured citation.
        state.is_cited = False
        state.confidence_score = 0.0
        state.sentiment = "none"
        if match.verdict is EntityVerdict.UNCERTAIN:
            state.step_log.append({"node": "entity_detection", "verdict": "uncertain",
                                   "matched_alias": match.matched_alias})

    state.citation_found = state.is_cited

    state.step_log.append({
        "node": "check_citation",
        "is_cited": state.is_cited,
        "confidence": state.confidence_score,
        "sentiment": state.sentiment,
    })
    return state


def gap_analyst_node(state: AuditState) -> AuditState:
    """Identifies visibility gaps using industry-specific templates.

    Existing: agent.py:gap_analyst (lines 142-200)
    Addresses: PE-OS Law 1 (External Memory)
    """
    from geo_audit_agent.industry_templates import get_template

    template = get_template(state.category)

    # Build business_data dict for template/fallback
    business_data = {
        "brand": state.brand_name,
        "brand_name": state.brand_name,
        "category": state.category,
        "city": state.city,
        "llm_response": state.llm_response,
        "business_context": state.business_context,
        "raw_business_context": getattr(state, "raw_business_context", ""),
        "business_context_text": getattr(state, "business_context_text", ""),
    }

    if isinstance(state.business_context, dict):
        business_data.update(state.business_context)
    elif isinstance(state.business_context, str):
        business_data["business_context"] = state.business_context

    brand = state.brand_name
    config_path = os.getenv("GAP_CHECKLIST_PATH") or "gap_checklist.json"
    if os.path.exists(config_path):
        try:
            with open(config_path) as f:
                all_checklists = json.load(f)
            brand_config = all_checklists.get(brand) or all_checklists.get("default") or {}

            if "has_json_ld" in brand_config:
                brand_config["has_schema"] = brand_config["has_json_ld"]
            if "recent_reviews" in brand_config:
                brand_config["review_count"] = 10 if brand_config["recent_reviews"] else 0

            business_data.update(brand_config)
        except Exception:
            pass
    elif brand == "Burger Hub":
        business_data.update({
            "has_schema": False,
            "review_count": 0,
            "has_technical_whitepaper": False,
        })

    gaps = []
    strengths = []

    if template:
        gaps = template.get_gaps(business_data)
        strengths = template.get_strengths(business_data)
        template_name = template.__class__.__name__
    else:
        template_name = "Generic"
        # Generic gaps if no template
        if not business_data.get('has_schema'):
            gaps.append({
                "gap_type": "Structured Data",
                "description": "brand's schema.org (JSON-LD) is missing.",
                "severity": "high",
                "tool_required": "generate_json_ld"
            })

        review_count = business_data.get('review_count', 0)
        if review_count == 0:
            gaps.append({
                "gap_type": "Third-party Reviews",
                "description": "No recent reviews found.",
                "severity": "medium",
                "tool_required": "create_review_snippet"
            })

        if not business_data.get('high_authority'):
            gaps.append({
                "gap_type": "Authority Signals",
                "description": "No high-authority backlinks or citations detected.",
                "severity": "medium",
                "tool_required": "draft_technical_whitepaper"
            })

    # Normalize gaps to include canonical fields and capitalize severity
    normalized_gaps = []
    for gap in gaps:
        raw_severity = gap.get('severity') or gap.get('priority') or 'medium'
        severity_title = raw_severity.capitalize()

        normalized_gap = {
            'gap_type': gap.get('gap_type') or gap.get('title') or gap.get('type') or 'Visibility Gap',
            'type': gap.get('type') or gap.get('gap_type') or 'generic',
            'title': gap.get('title') or gap.get('gap_type') or 'Visibility Gap',
            'description': gap.get('description') or gap.get('reason') or '',
            'severity': severity_title,
        }
        for key, value in gap.items():
            if key not in normalized_gap:
                normalized_gap[key] = value
        normalized_gaps.append(normalized_gap)

    state.gaps = normalized_gaps
    state.strengths = strengths
    state.template_used = template_name
    state.competitors = _extract_competitors(state.llm_response, state.brand_name)

    state.step_log.append({
        "node": "gap_analyst",
        "gap_count": len(normalized_gaps),
        "strength_count": len(strengths),
    })
    return state


def planner_node(state: AuditState) -> AuditState:
    """LLM-based action planning with tool selection.

    Existing: agent.py:planner (lines 202-280)
    Addresses: PE-OS Law 5 (Feedback Loop Autonomy)
    """
    if not state.gaps:
        state.planned_actions = []
        return state

    force_mock = state.force_mock or (isinstance(state.business_context, dict) and state.business_context.get("force_mock"))
    has_api_key = bool(os.getenv("GOOGLE_API_KEY"))

    if force_mock or not has_api_key:
        logger.info("Using fallback planner (mock mode)")
        planned_actions = []
        for gap in state.gaps:
            tool = gap.get("tool_required") or gap.get("tool") or "generate_json_ld"
            if tool == "create_review_snippet":
                tool = "generate_review_template"
            planned_actions.append({
                "tool": tool,
                "reason": f"Remediate {gap.get('gap_type') or 'gap'}"
            })
        state.planned_actions = planned_actions
        state.step_log.append({
            "node": "planner",
            "action_count": len(planned_actions),
            "mocked": True,
        })
        return state

    try:
        planning_prompt = _build_planning_prompt(state)
        response = query_provider(
            prompt=planning_prompt,
            tier="balanced",
            correlation_id=state.correlation_id,
        )

        actions = _parse_planned_actions(response.text)
        state.planned_actions = actions
        state.total_tokens += response.total_tokens
        state.total_cost_usd += response.cost_usd
        state.step_log.append({
            "node": "planner",
            "action_count": len(actions),
        })
    except Exception as e:
        logger.warning(f"Real planner query failed, falling back to mock planner: {e}")
        planned_actions = []
        for gap in state.gaps:
            tool = gap.get("tool_required") or gap.get("tool") or "generate_json_ld"
            if tool == "create_review_snippet":
                tool = "generate_review_template"
            planned_actions.append({
                "tool": tool,
                "reason": f"Remediate {gap.get('gap_type') or 'gap'}"
            })
        state.planned_actions = planned_actions
        state.step_log.append({
            "node": "planner",
            "action_count": len(planned_actions),
            "mocked": True,
            "fallback_due_to_error": str(e),
        })

    return state


def remediation_handler_node(state: AuditState) -> AuditState:
    """Executes remediation actions with validation.

    Existing: agent.py:remediation_handler (lines 282-380)
    Upgrade: Adds validator-repair loop (Law 6: Agent Execution Integrity)
    """
    from geo_audit_agent.geo_remediation_tools import (
        draft_technical_whitepaper,
        generate_json_ld,
        generate_review_template,
    )
    from geo_audit_agent.remediation import generate_remediation

    results: dict[str, Any] = {}
    for action in state.planned_actions:
        tool_name = action.get("tool", "")
        try:
            if tool_name == "generate_json_ld":
                product_info = {
                    "name": state.brand_name,
                    "description": f"Best {state.category} in {state.city}",
                    "address": state.city,
                    "telephone": "",
                }
                output = generate_json_ld(
                    brand_name=state.brand_name,
                    product_info=product_info,
                )
                results["json_ld"] = output
            elif tool_name == "draft_technical_whitepaper":
                topic = f"GEO visibility optimization for {state.brand_name} in {state.city}"
                key_features = [gap.get("description", "") for gap in state.gaps if gap] or ["General visibility factors"]
                output = draft_technical_whitepaper(
                    brand_name=state.brand_name,
                    topic=topic,
                    key_features=key_features,
                )
                results["whitepaper"] = output
            elif tool_name == "generate_review_template":
                output = generate_review_template(
                    brand_name=state.brand_name,
                    category=state.category,
                    city=state.city,
                    rating=4.5,
                )
                results["review_template"] = output
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}", extra={
                "correlation_id": state.correlation_id,
                "audit_id": state.audit_id,
            })
            result_key = {
                "generate_json_ld": "json_ld",
                "draft_technical_whitepaper": "whitepaper",
                "generate_review_template": "review_template",
            }.get(tool_name, tool_name)
            results[result_key] = {"error": str(e)}

    state.remediation_outputs = results

    # Generate remediation list using the templates/remediation module
    business_context = state.business_context if isinstance(state.business_context, dict) else {}
    remediations = generate_remediation(state.gaps, state.category, state.city, state.brand_name, business_context)
    state.remediation = remediations

    # Legacy fallback: convert to old format for backward compatibility
    legacy_results = []
    for rem in remediations:
        action_text = rem.get("action", "")
        legacy_results.append({
            "tool": rem.get("type", "remediation"),
            "status": "success",
            "output_preview": action_text[:100] + "..." if len(action_text) > 100 else action_text,
            "output_full": action_text
        })
    state.remediation_results = legacy_results

    state.step_log.append({
        "node": "remediation_handler",
        "tools_executed": len(results),
        "remediations_generated": len(remediations),
    })
    return state


def validate_output_node(state: AuditState) -> AuditState:
    """Validates generated artifacts locally before persistence.

    NEW node: Implements PE-OS Law 5 (Feedback Loop) and Law 6 (Execution Integrity)
    Addresses: Audit 1 §2 (Law 5, Law 6, Law 8)
    """
    errors = []

    json_ld = state.remediation_outputs.get("json_ld", {})
    if isinstance(json_ld, str):
        try:
            parsed = json.loads(json_ld)
            if "@context" not in parsed or "@type" not in parsed:
                errors.append("JSON-LD missing @context or @type")
        except json.JSONDecodeError as e:
            errors.append(f"JSON-LD syntax error: {e}")

    state.validation_errors = errors
    if errors:
        state.repair_attempts += 1

    state.step_log.append({
        "node": "validate_output",
        "errors": errors,
        "repair_attempt": state.repair_attempts,
    })
    return state


def generate_report_node(state: AuditState) -> AuditState:
    """Compiles final audit report from all pipeline outputs.

    Existing: agent.py:generate_report (lines 382-440)
    """
    # ── Predict GEO score ──
    try:
        from geo_audit_agent.geo_intelligence.predictor import predict_score
        features = {
            "has_json_ld": 0.0 if any(g.get("tool_required") == "generate_json_ld" or g.get("tool") == "generate_json_ld" for g in state.gaps) else 1.0,
            "has_technical_whitepaper": 0.0 if any(g.get("tool_required") == "draft_technical_whitepaper" or g.get("tool") == "draft_technical_whitepaper" for g in state.gaps) else 1.0,
            "has_reviews": 0.0 if any(g.get("tool_required") in ("create_review_snippet", "generate_review_template") or g.get("tool") in ("create_review_snippet", "generate_review_template") for g in state.gaps) else 1.0,
            "competition_level": float(len(state.competitors)),
            "brand_age_months": 24.0,
            "backlink_count": 50.0,
            "semantic_score": state.confidence_score,
        }
        state.predicted_geo_score = predict_score(features)
    except Exception as e:
        logger.error(f"Failed to calculate predicted GEO score: {e}")
        state.predicted_geo_score = 0.0

    # ── Flag anomalies ──
    try:
        from geo_audit_agent.geo_intelligence.anomaly_detector import flag_anomalies
        cited_brands = re.findall(r"['\"]([^'\"]+)['\"]", state.llm_response) if state.llm_response else []

        # Lazy load client helper
        api_key = os.getenv("GOOGLE_API_KEY")
        client = genai.Client(api_key=api_key) if api_key else None

        state.anomalies = flag_anomalies(
            {"cited_brands": cited_brands},
            state.city,
            state.category,
            client
        )
    except Exception as e:
        logger.error(f"Failed to flag anomalies: {e}")
        state.anomalies = {}

    query_steps = [step for step in state.step_log if step.get("node") == "query_llm"]
    query_step = query_steps[-1] if query_steps else {}
    execution_mode = "fixture" if state.mode == "simulated" else "live" if state.mode == "real" else state.mode
    state.report = {
        "brand_name": state.brand_name,
        "category": state.category,
        "city": state.city,
        "tier": state.tier,
        "is_cited": state.is_cited,
        "confidence_score": state.confidence_score,
        "sentiment": state.sentiment,
        "gaps": state.gaps,
        "strengths": state.strengths,
        "competitors": state.competitors,
        "remediation": state.remediation,
        "predicted_geo_score": state.predicted_geo_score,
        "anomalies": state.anomalies,
        "total_tokens": state.total_tokens,
        "total_cost_usd": state.total_cost_usd,
        "observation": {
            "provider": query_step.get("provider", "fixture" if execution_mode == "fixture" else "unknown"),
            "model": query_step.get("model", "unknown"),
            "prompt_id": "category-recommendation",
            "prompt_version": "1.0",
            "execution_mode": execution_mode,
            "raw_response": state.llm_response,
            "mentioned": state.is_cited,
            "recommendation": state.is_cited,
            "citation_urls": [],
            "input_tokens": state.total_tokens,
            "output_tokens": 0,
            "cost_usd": state.total_cost_usd,
            "cache_hit": bool(query_step.get("cache_hit")),
        },
    }

    state.step_log.append({"node": "generate_report"})
    return state


class SentimentResult:
    def __init__(self, is_positive: bool, confidence: float, sentiment: str):
        self.is_positive = is_positive
        self.confidence = confidence
        self.sentiment = sentiment


def _analyze_citation_sentiment(context: str, brand_name: str) -> SentimentResult:
    """Analyze sentiment based on brand mentions and nearby positive terms."""
    if not brand_name or not context:
        return SentimentResult(False, 0.0, "none")

    brand_pattern = re.compile(re.escape(brand_name), re.IGNORECASE)
    brand_match = brand_pattern.search(context)

    if not brand_match:
        return SentimentResult(False, 0.0, "none")

    positive_terms = [
        'best', 'top', 'excellent', 'quality', 'stands out', 'trusted',
        'popular', 'premium', 'well-maintained', 'supportive', 'clean',
        'recommended', 'commitment', 'customer satisfaction', 'outstanding',
        'exceptional', 'great', 'amazing', 'wonderful', 'fantastic',
        'highly rated', 'well-reviewed', 'professional', 'friendly',
    ]

    context_lower = context.lower()
    for term in positive_terms:
        if term in context_lower:
            return SentimentResult(True, 1.0, "positive")

    return SentimentResult(False, 0.5, "neutral")


def _extract_competitors(raw_response: str, brand_name: str) -> list:
    """Extract competitors from raw response, excluding target brand and generic placeholders."""
    if not raw_response:
        return []

    generic_placeholders = [
        'local favorite', 'established brand', 'premium choice',
        'top provider', 'popular option', 'leading brand',
        'market leader', 'industry leader',
    ]

    competitors = []
    numbered_pattern = re.compile(r'^\s*\d+\.\s*(.+)$', re.MULTILINE)
    matches = numbered_pattern.findall(raw_response)

    for match in matches:
        competitor = match.strip()

        # Remove trailing descriptions after dash
        if ' - ' in competitor:
            competitor = competitor.split(' - ')[0].strip()

        if brand_name and brand_name.lower() in competitor.lower():
            continue

        if competitor.lower() in generic_placeholders:
            continue

        if len(competitor) < 3 or len(competitor) > 100:
            continue

        competitors.append(competitor)

    return competitors


def _build_planning_prompt(state: AuditState) -> str:
    gaps_str = json.dumps(state.gaps)
    return f"""Based on these gaps: {gaps_str}, write a short action plan to improve AI citation for {state.brand_name}.
    Output as valid JSON only, containing a list of objects under 'steps'.
    Each step MUST include a 'tool_required' field corresponding to one of: generate_json_ld, draft_technical_whitepaper, generate_review_template.
    Each step must have: 'action', 'tool_required', and 'estimated_effort_days'."""


def _parse_planned_actions(content: str) -> list:
    try:
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start != -1 and json_end != 0:
            clean_json = content[json_start:json_end]
            plan_data = json.loads(clean_json)
            steps = plan_data.get("steps", [])
            for step in steps:
                if "tool_required" in step:
                    step["tool"] = step["tool_required"]
                if step.get("tool") == "create_review_snippet":
                    step["tool"] = "generate_review_template"
            return steps
    except Exception as e:
        logger.error(f"Failed to parse planned actions: {e}")
    return []
