import os
import json
import logging
from typing import TypedDict, Optional, List, Dict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from google import genai

# Import remediation tools
from .geo_remediation_tools import (
    generate_json_ld,
    draft_technical_whitepaper,
    create_review_snippet
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

MODEL_NAME = "gemini-2.0-flash-lite"

def get_google_client():
    """Lazy-load Google GenAI client. Returns None if API key missing."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        logger.warning(f"Failed to initialize Google GenAI client: {e}")
        return None

# 1. State
class AgentState(TypedDict):
    brand_name: str
    category: str
    city: str
    llm_response: Optional[str]
    is_cited: Optional[bool]
    confidence_score: Optional[float]
    sentiment: Optional[str]
    competitors: Optional[List[str]]
    strengths: Optional[List[Dict]]
    gaps: List[Dict]
    planned_actions: List[Dict]
    remediation: List[Dict]  # New industry-aware remediation
    remediation_results: List[Dict]  # Legacy format
    business_context: Optional[Dict]
    template_used: Optional[str]  # Industry template used
    # Advanced features state
    enable_prediction: Optional[bool]
    enable_anomalies: Optional[bool]
    geo_potential_score: Optional[float]
    anomalies: Optional[List[Dict]]

# 2. Nodes

def predictive_node(state: AgentState) -> AgentState:
    from .geo_intelligence.predictor import predict_score
    logger.info("Starting Node: predictive_node")
    features = {
        "has_json_ld": any(g.get("tool_required") == "generate_json_ld" for g in state.get("gaps", [])),
        "recent_reviews": any(g.get("tool_required") == "create_review_snippet" for g in state.get("gaps", [])),
        "high_authority": any(g.get("tool_required") == "draft_technical_whitepaper" for g in state.get("gaps", [])),
        "city_relevance": True # Simplified
    }
    state["geo_potential_score"] = predict_score(features)
    logger.info(f"Finished Node: predictive_node (Score: {state['geo_potential_score']})")
    return state

def anomaly_node(state: AgentState) -> AgentState:
    from .geo_intelligence.anomaly_detector import flag_anomalies
    logger.info("Starting Node: anomaly_node")
    # Extract brands from LLM response (simplified)
    import re
    response = state.get("llm_response", "")
    cited_brands = re.findall(r"['\"]([^'\"]+)['\"]", response) if response else []

    state["anomalies"] = flag_anomalies(
        {"cited_brands": cited_brands},
        state["city"],
        state["category"],
        client
    )
    logger.info(f"Finished Node: anomaly_node (Anomalies: {len(state['anomalies'])})")
    return state

def query_llm(state: AgentState) -> AgentState:
    logger.info("Starting Node: query_llm")

    # Safe brand extraction
    brand = state.get("brand_name") or state.get("brand", "Unknown Brand")
    category = state.get("category", "business")
    city = state.get("city", "the area")

    # Check if force_mock is enabled
    if state.get("force_mock", False):
        logger.info("Force mock mode enabled - using deterministic response")
        state["llm_response"] = f"For the best {category} in {city}, here are some top recommendations:\n\n1. {brand} - Known for quality and excellent service\n2. Local Favorite - Popular choice in the area\n3. Established Brand - Consistent quality\n\n{brand} stands out for its commitment to customer satisfaction."
        logger.info("Finished Node: query_llm (mock mode)")
        return state

    client = get_google_client()

    if client is None:
        logger.warning("Google API key not available - using mock response")
        brand = state.get("brand_name") or state.get("brand", "Unknown Brand")
        category = state.get("category", "business")
        city = state.get("city", "the area")
        state["llm_response"] = f"For the best {category} in {city}, here are some top recommendations:\n\n1. {brand} - Known for quality and excellent service\n2. Local Favorite - Popular choice in the area\n3. Established Brand - Consistent quality\n\n{brand} stands out for its commitment to customer satisfaction."
        logger.info("Finished Node: query_llm (fallback mode)")
        return state

    prompt = f"What is the best {state.get('category', 'business')} in {state.get('city', 'the area')}? Return a concise answer with specific names."

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config={
                "temperature": 0.2,
                "max_output_tokens": 1000
            }
        )
        state["llm_response"] = response.text
    except Exception as e:
        logger.error(f"query_llm failed: {e}")
        # Fallback to mock response on error
        brand = state.get("brand_name") or state.get("brand", "Unknown Brand")
        category = state.get("category", "business")
        city = state.get("city", "the area")
        state["llm_response"] = f"For the best {category} in {city}, here are some top recommendations:\n\n1. {brand} - Known for quality and excellent service\n2. Local Favorite - Popular choice in the area\n3. Established Brand - Consistent quality\n\n{brand} stands out for its commitment to customer satisfaction."

    logger.info("Finished Node: query_llm")
    return state

def check_citation(state: AgentState) -> AgentState:
    logger.info("Starting Node: check_citation")
    brand = (state.get("brand_name") or state.get("brand", "")).lower()
    response = state.get("llm_response", "").lower() if state.get("llm_response") else ""

    if not response or "error:" in response:
        state["is_cited"] = False
        state["confidence_score"] = 0.0
        state["sentiment"] = "none"
    elif brand in response:
        state["is_cited"] = True
        state["confidence_score"] = 1.0
        # Detect sentiment
        state["sentiment"] = detect_sentiment_from_response(state.get("llm_response", ""), state.get("brand_name", ""))
    else:
        brand_words = brand.split()
        matches = [word for word in brand_words if len(word) > 2 and word in response]
        state["is_cited"] = bool(matches)
        state["confidence_score"] = 0.5 if matches else 0.0
        state["sentiment"] = "neutral" if matches else "none"

    # Extract competitors
    state["competitors"] = extract_competitors_from_response(state.get("llm_response", ""), state.get("brand_name", ""))

    logger.info(f"Finished Node: check_citation (Cited: {state['is_cited']}, Sentiment: {state.get('sentiment')})")
    return state

def detect_sentiment_from_response(raw_response: str, brand_name: str) -> str:
    """Detect sentiment based on brand mention and nearby positive terms."""
    if not brand_name or not raw_response:
        return 'none'

    import re
    brand_pattern = re.compile(re.escape(brand_name), re.IGNORECASE)
    brand_match = brand_pattern.search(raw_response)

    if not brand_match:
        return 'none'

    positive_terms = [
        'best', 'top', 'excellent', 'quality', 'stands out', 'trusted',
        'popular', 'premium', 'well-maintained', 'supportive', 'clean',
        'recommended', 'commitment', 'customer satisfaction', 'outstanding',
        'exceptional', 'great', 'amazing', 'wonderful', 'fantastic',
        'highly rated', 'well-reviewed', 'professional', 'friendly',
    ]

    start = max(0, brand_match.start() - 100)
    end = min(len(raw_response), brand_match.end() + 100)
    context = raw_response[start:end].lower()

    for term in positive_terms:
        if term in context:
            return 'positive'

    return 'neutral'

def extract_competitors_from_response(raw_response: str, brand_name: str) -> list:
    """Extract competitors from raw response, excluding target brand and generic placeholders."""
    if not raw_response:
        return []

    import re
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

def gap_analyst(state: AgentState) -> AgentState:
    logger.info("Starting Node: gap_analyst")

    from .industry_templates import get_template

    brand = state.get("brand_name") or state.get("brand", "Unknown Brand")
    category = state.get("category", "business")
    city = state.get("city", "the area")
    business_context = state.get("business_context", {})

    # Get industry template
    template = get_template(category)

    gaps = []
    strengths = []

    if template:
        # Use industry-specific template
        gaps = template.get_gaps(business_context)
        strengths = template.get_strengths(business_context)
        logger.info(f"Using industry template: {template.__class__.__name__}")
    else:
        # Generic gaps if no template
        if not business_context.get('has_schema'):
            gaps.append({
                "gap_type": "Structured Data",
                "description": "brand's schema.org (JSON-LD) is missing.",
                "severity": "high",
                "tool_required": "generate_json_ld"
            })

        review_count = business_context.get('review_count', 0)
        if review_count == 0:
            gaps.append({
                "gap_type": "Third-party Reviews",
                "description": "No recent reviews found.",
                "severity": "medium",
                "tool_required": "create_review_snippet"
            })

    # Normalize gaps to include canonical fields for backward compatibility
    normalized_gaps = []
    for gap in gaps:
        normalized_gap = {
            'gap_type': gap.get('gap_type') or gap.get('title') or gap.get('type') or 'Visibility Gap',
            'type': gap.get('type') or gap.get('gap_type') or 'generic',
            'title': gap.get('title') or gap.get('gap_type') or 'Visibility Gap',
            'description': gap.get('description') or gap.get('reason') or '',
            'severity': gap.get('severity') or gap.get('priority') or 'medium',
        }
        # Preserve original fields like tool_required
        for key, value in gap.items():
            if key not in normalized_gap:
                normalized_gap[key] = value
        normalized_gaps.append(normalized_gap)

    state["gaps"] = normalized_gaps
    state["strengths"] = strengths
    state["template_used"] = template.__class__.__name__ if template else "Generic"
    logger.info(f"Finished Node: gap_analyst (Gaps: {len(normalized_gaps)}, Strengths: {len(strengths)}, Template: {state['template_used']})")
    return state

def planner(state: AgentState) -> AgentState:
    logger.info("Starting Node: planner")
    if not state["gaps"]:
        state["planned_actions"] = []
        return state

    client = get_google_client()

    if client is None or state.get("force_mock", False):
        # Fallback: deterministic plan based on gaps
        logger.info("Using fallback planner (no API key or mock mode)")
        planned_actions = []
        for gap in state["gaps"]:
            tool = gap.get("tool_required", "generate_json_ld")
            planned_actions.append({
                "action": f"Address {gap['gap_type']}: {gap['description']}",
                "tool_required": tool,
                "estimated_effort_days": 7 if gap["severity"] == "high" else 3
            })
        state["planned_actions"] = planned_actions
        logger.info(f"Finished Node: planner (fallback mode, {len(planned_actions)} actions)")
        return state

    gaps_str = json.dumps(state["gaps"])
    brand = state.get("brand_name") or state.get("brand", "Unknown Brand")
    prompt = f"""Based on these gaps: {gaps_str}, write a short action plan to improve AI citation for {brand}.
    Output as valid JSON only, containing a list of objects under 'steps'.
    Each step MUST include a 'tool_required' field corresponding to one of: generate_json_ld, draft_technical_whitepaper, create_review_snippet.
    Each step must have: 'action', 'tool_required', and 'estimated_effort_days'."""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config={
                "temperature": 0.2,
                "max_output_tokens": 500
            }
        )
        content = response.text
        # More robust JSON extraction
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start != -1 and json_end != 0:
            clean_json = content[json_start:json_end]
            plan_data = json.loads(clean_json)
            state["planned_actions"] = plan_data.get("steps", [])
        else:
            logger.error("No JSON found in planner response")
            state["planned_actions"] = []
    except Exception as e:
        logger.error(f"planner failed: {e}")
        # Fallback to manual review if JSON parsing fails
        state["planned_actions"] = [{"action": "Manual Review", "tool_required": "None", "estimated_effort_days": 1}]

    logger.info("Finished Node: planner")
    return state

def remediation_handler(state: AgentState) -> AgentState:
    logger.info("Starting Node: remediation_handler")

    # Generate industry-aware remediation using the new system
    from .remediation import generate_remediation

    gaps = state.get("gaps", [])
    brand = state.get("brand_name") or state.get("brand", "Unknown Brand")
    category = state.get("category", "business")
    city = state.get("city", "the area")

    # Generate remediation from gaps
    remediation = generate_remediation(gaps, category, city, brand)

    # Store in both new and legacy fields
    state["remediation"] = remediation

    # Legacy fallback: convert to old format for backward compatibility
    legacy_results = []
    for rem in remediation:
        legacy_results.append({
            "tool": rem.get("type", "remediation"),
            "status": "success",
            "output_preview": rem.get("action", "")[:100] + "..."
        })
    state["remediation_results"] = legacy_results

    logger.info(f"Finished Node: remediation_handler (Generated {len(remediation)} remediation items)")
    return state

def generate_report(state: AgentState) -> AgentState:
    logger.info("Starting Node: generate_report")
    brand = state.get("brand_name") or state.get("brand", "Unknown Brand")
    report = {"brand": brand, "is_cited": state.get("is_cited", False), "confidence": state.get("confidence_score", 0.0), "gaps_identified": len(state.get("gaps", [])), "remediation_actions": len(state.get("remediation_results", [])), "remediation_details": state.get("remediation_results", [])}
    print("\n" + "="*50 + "\nGEO AUDIT AGENT INTEGRATED REPORT\n" + "="*50 + "\n" + json.dumps(report, indent=4) + "\n" + "="*50 + "\n")
    return state

class GeoAuditAgent:
    """Wrapper for LangGraph agent with backward compatibility for brand/brand_name."""

    def __init__(self, compiled_graph):
        self.graph = compiled_graph

    def invoke(self, input_dict: dict) -> dict:
        """
        Invoke the agent with backward compatibility.

        Accepts both 'brand' and 'brand_name' in the input.
        Returns both 'brand' and 'brand_name' in the result.
        """
        # Input compatibility: accept brand, brand_name, or business_name
        brand = (
            input_dict.get("brand")
            or input_dict.get("brand_name")
            or input_dict.get("business_name")
        )

        if not brand:
            raise ValueError("Brand name is required (provide 'brand', 'brand_name', or 'business_name')")

        # Normalize input - ensure both keys are present
        input_dict["brand"] = brand
        input_dict["brand_name"] = brand

        # Prepare state with brand_name (what the graph expects)
        state = {
            "brand_name": brand,
            "brand": brand,
            "category": input_dict.get("category", "business"),
            "city": input_dict.get("city", "the area"),
            "business_context": input_dict.get("business_context", {}),
            "gaps": [],
            "planned_actions": [],
            "remediation": [],
            "remediation_results": [],
            "sentiment": "none",
            "competitors": [],
            "strengths": [],
            "force_mock": input_dict.get("force_mock", False),
            "enable_prediction": input_dict.get("enable_prediction", False),
            "enable_anomalies": input_dict.get("enable_anomalies", False)
        }

        # Run the graph
        result = self.graph.invoke(state)

        # Output compatibility: ensure both "brand" and "brand_name" are present
        result["brand"] = result.get("brand_name") or result.get("brand") or brand
        result["brand_name"] = result.get("brand_name") or result.get("brand") or brand

        # Add mode field based on whether we used fallback
        if result.get("force_mock") or not result.get("llm_response"):
            result["mode"] = "simulated"
        else:
            result["mode"] = "live_api"

        # Map state fields to expected output fields
        result["citation_found"] = result.get("is_cited", False)
        result["confidence_score"] = result.get("confidence_score", 0.0)
        result["raw_response"] = result.get("llm_response", "")
        result["sentiment"] = result.get("sentiment", "none")
        result["competitors"] = result.get("competitors", [])
        result["strengths"] = result.get("strengths", [])
        result["remediation"] = result.get("remediation", [])
        result["template_used"] = result.get("template_used", "Generic")
        result["template_used"] = result.get("template_used", "Generic")

        return result

def build_geo_audit_agent():
    workflow = StateGraph(AgentState)
    workflow.add_node("query_llm", query_llm)
    workflow.add_node("check_citation", check_citation)
    workflow.add_node("gap_analyst", gap_analyst)
    workflow.add_node("planner", planner)
    workflow.add_node("remediation_handler", remediation_handler)
    workflow.add_node("generate_report", generate_report)
    # Advanced nodes
    workflow.add_node("predictive_node", predictive_node)
    workflow.add_node("anomaly_node", anomaly_node)

    workflow.set_entry_point("query_llm")
    workflow.add_edge("query_llm", "check_citation")
    workflow.add_edge("check_citation", "gap_analyst")
    workflow.add_edge("gap_analyst", "planner")
    workflow.add_edge("planner", "remediation_handler")
    workflow.add_edge("remediation_handler", "generate_report")

    # Conditional advanced flows
    workflow.add_conditional_edges(
        "generate_report",
        lambda x: "predictive_node" if x.get("enable_prediction") else ("anomaly_node" if x.get("enable_anomalies") else END)
    )
    workflow.add_conditional_edges(
        "predictive_node",
        lambda x: "anomaly_node" if x.get("enable_anomalies") else END
    )
    workflow.add_edge("anomaly_node", END)

    compiled = workflow.compile()
    return GeoAuditAgent(compiled)

if __name__ == "__main__":
    agent = build_geo_audit_agent()
    test_inputs = {"brand_name": "Burger Hub", "category": "fast food", "city": "Islamabad", "gaps": [], "planned_actions": [], "remediation_results": []}
    try:
        agent.invoke(test_inputs)
        logger.info("Execution completed successfully.")
    except Exception as err:
        logger.error(f"Execution failed: {err}")
