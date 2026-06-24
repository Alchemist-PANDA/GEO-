# agent_init.py
from .graph import audit_graph
from .nodes import check_citation_node, gap_analyst_node
from .state import AuditState

def build_geo_audit_agent():
    """Legacy compatibility entry point returning compiled LangGraph graph."""
    return audit_graph

def check_citation(state):
    """Wrapper mapping legacy TypedDict states to Pydantic AuditState checks."""
    if isinstance(state, dict):
        model_state = AuditState(**state)
        res = check_citation_node(model_state)
        state.update(res.model_dump())
        state["brand"] = model_state.brand_name
        return state
        
    return check_citation_node(state)

def gap_analyst(state):
    """Wrapper mapping legacy TypedDict states to Pydantic gap analyst checks."""
    if isinstance(state, dict):
        model_state = AuditState(**state)
        res = gap_analyst_node(model_state)
        state.update(res.model_dump())
        state["brand"] = model_state.brand_name
        return state
        
    return gap_analyst_node(state)

