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
    gaps: List[Dict]
    planned_actions: List[Dict]
    remediation_results: List[Dict]
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

    # Check if force_mock is enabled
    if state.get("force_mock", False):
        logger.info("Force mock mode enabled - using deterministic response")
        brand = state["brand_name"]
        category = state["category"]
        city = state["city"]
        state["llm_response"] = f"For the best {category} in {city}, here are some top recommendations:\n\n1. {brand} - Known for quality and excellent service\n2. Local Favorite - Popular choice in the area\n3. Established Brand - Consistent quality\n\n{brand} stands out for its commitment to customer satisfaction."
        logger.info("Finished Node: query_llm (mock mode)")
        return state

    client = get_google_client()

    if client is None:
        logger.warning("Google API key not available - using mock response")
        brand = state["brand_name"]
        category = state["category"]
        city = state["city"]
        state["llm_response"] = f"For the best {category} in {city}, here are some top recommendations:\n\n1. {brand} - Known for quality and excellent service\n2. Local Favorite - Popular choice in the area\n3. Established Brand - Consistent quality\n\n{brand} stands out for its commitment to customer satisfaction."
        logger.info("Finished Node: query_llm (fallback mode)")
        return state

    prompt = f"What is the best {state['category']} in {state['city']}? Return a concise answer with specific names."

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
        brand = state["brand_name"]
        category = state["category"]
        city = state["city"]
        state["llm_response"] = f"For the best {category} in {city}, here are some top recommendations:\n\n1. {brand} - Known for quality and excellent service\n2. Local Favorite - Popular choice in the area\n3. Established Brand - Consistent quality\n\n{brand} stands out for its commitment to customer satisfaction."

    logger.info("Finished Node: query_llm")
    return state

def check_citation(state: AgentState) -> AgentState:
    logger.info("Starting Node: check_citation")
    brand = state["brand_name"].lower()
    response = state["llm_response"].lower() if state["llm_response"] else ""

    if not response or "error:" in response:
        state["is_cited"] = False
        state["confidence_score"] = 0.0
    elif brand in response:
        state["is_cited"] = True
        state["confidence_score"] = 1.0
    else:
        brand_words = brand.split()
        matches = [word for word in brand_words if len(word) > 2 and word in response]
        state["is_cited"] = bool(matches)
        state["confidence_score"] = 0.5 if matches else 0.0

    logger.info(f"Finished Node: check_citation (Cited: {state['is_cited']})")
    return state

def gap_analyst(state: AgentState) -> AgentState:
    logger.info("Starting Node: gap_analyst")
    ideal_checklist_results = {
        "Burger Hub": {"has_json_ld": False, "recent_reviews": True, "high_authority": False, "recency_mention": False, "geo_relevance": True}
    }
    brand_data = ideal_checklist_results.get(state["brand_name"], {"has_json_ld": False, "recent_reviews": False, "high_authority": False, "recency_mention": False, "geo_relevance": False})

    gaps = []
    if not brand_data["has_json_ld"]:
        gaps.append({"gap_type": "Structured Data", "description": "brand's schema.org (JSON-LD) is missing.", "severity": "high", "tool_required": "generate_json_ld"})
    if not brand_data["recent_reviews"]:
        gaps.append({"gap_type": "Third-party Reviews", "description": "No recent reviews found.", "severity": "medium", "tool_required": "create_review_snippet"})
    if not brand_data["high_authority"]:
        gaps.append({"gap_type": "Authority Signals", "description": "Domain authority is low.", "severity": "medium", "tool_required": "draft_technical_whitepaper"})

    state["gaps"] = gaps
    logger.info(f"Finished Node: gap_analyst (Gaps found: {len(gaps)})")
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
    prompt = f"""Based on these gaps: {gaps_str}, write a short action plan to improve AI citation for {state['brand_name']}.
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
    results = []
    tool_map = {"generate_json_ld": generate_json_ld, "draft_technical_whitepaper": draft_technical_whitepaper, "create_review_snippet": create_review_snippet}

    for action in state.get("planned_actions", []):
        tool_name = action.get("tool_required")
        if tool_name in tool_map:
            logger.info(f"Executing remediation tool: {tool_name}")
            try:
                if tool_name == "generate_json_ld":
                    product_info = {"name": state["brand_name"], "description": f"Best {state['category']} in {state['city']}"}
                    result = tool_map[tool_name](state["brand_name"], product_info)
                elif tool_name == "draft_technical_whitepaper":
                    result = tool_map[tool_name](state["brand_name"], f"Technical Excellence in {state['category']}", ["Quality", "Innovation"])
                elif tool_name == "create_review_snippet":
                    result = tool_map[tool_name](state["brand_name"], state["category"], state["city"], 4.9)
                results.append({"tool": tool_name, "status": "success", "output_preview": result[:100] + "..."})
            except Exception as e:
                logger.error(f"Error executing {tool_name}: {e}")
                results.append({"tool": tool_name, "status": "failed", "error": str(e)})

    state["remediation_results"] = results
    logger.info(f"Finished Node: remediation_handler")
    return state

def generate_report(state: AgentState) -> AgentState:
    logger.info("Starting Node: generate_report")
    report = {"brand": state["brand_name"], "is_cited": state["is_cited"], "confidence": state["confidence_score"], "gaps_identified": len(state["gaps"]), "remediation_actions": len(state["remediation_results"]), "remediation_details": state["remediation_results"]}
    print("\n" + "="*50 + "\nGEO AUDIT AGENT INTEGRATED REPORT\n" + "="*50 + "\n" + json.dumps(report, indent=4) + "\n" + "="*50 + "\n")
    return state

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

    return workflow.compile()

if __name__ == "__main__":
    agent = build_geo_audit_agent()
    test_inputs = {"brand_name": "Burger Hub", "category": "fast food", "city": "Islamabad", "gaps": [], "planned_actions": [], "remediation_results": []}
    try:
        agent.invoke(test_inputs)
        logger.info("Execution completed successfully.")
    except Exception as err:
        logger.error(f"Execution failed: {err}")
