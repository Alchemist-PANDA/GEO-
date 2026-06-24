from langgraph.graph import StateGraph, END
from geo_audit_agent.agent.state import AuditState
from geo_audit_agent.agent.nodes import (
    guardrail_node,
    query_llm_node,
    check_citation_node,
    gap_analyst_node,
    planner_node,
    remediation_handler_node,
    validate_output_node,
    generate_report_node,
)


def should_remediate(state: AuditState) -> str:
    if state.gaps:
        return "planner"
    return "generate_report"


def should_repair(state: AuditState) -> str:
    if state.validation_errors and state.repair_attempts < state.max_repairs:
        return "remediation_handler"
    return "generate_report"


def build_audit_graph() -> StateGraph:
    graph = StateGraph(AuditState)

    graph.add_node("guardrail", guardrail_node)
    graph.add_node("query_llm", query_llm_node)
    graph.add_node("check_citation", check_citation_node)
    graph.add_node("gap_analyst", gap_analyst_node)
    graph.add_node("planner", planner_node)
    graph.add_node("remediation_handler", remediation_handler_node)
    graph.add_node("validate_output", validate_output_node)
    graph.add_node("generate_report", generate_report_node)

    graph.set_entry_point("guardrail")
    graph.add_edge("guardrail", "query_llm")
    graph.add_edge("query_llm", "check_citation")
    graph.add_edge("check_citation", "gap_analyst")

    graph.add_conditional_edges("gap_analyst", should_remediate, {
        "planner": "planner",
        "generate_report": "generate_report",
    })

    graph.add_edge("planner", "remediation_handler")
    graph.add_edge("remediation_handler", "validate_output")

    graph.add_conditional_edges("validate_output", should_repair, {
        "remediation_handler": "remediation_handler",
        "generate_report": "generate_report",
    })

    graph.add_edge("generate_report", END)

    return graph.compile()


audit_graph = build_audit_graph()
