# Architecture Deep Dive: GEO Audit Agent

## 1. The LangGraph State Machine

The core intelligence of this repository is a **LangGraph** (cyclic state machine) defined in `geo_audit_agent/agent.py`. Unlike a linear script, this architecture allows the agent to pass a persistent `AgentState` through specialized nodes.

### Node Definitions
1.  **`query_llm`**: Probes the "mental model" of a target LLM (Gemini/Llama) to see if it recommends the brand.
2.  **`check_citation`**: A deterministic verification node that checks for exact or partial brand name matches in the LLM response.
3.  **`gap_analyst`**: Evaluates the brand against a forensic checklist (Structured Data, Review Recency, Authority).
4.  **`planner`**: Uses a high-reasoning model to select the best tools for remediation based on identified gaps.
5.  **`remediation_handler`**: Executes the selected tools (`generate_json_ld`, `create_review_snippet`, etc.).
6.  **`generate_report`**: Compiles all findings into a structured JSON audit.

## 2. Remediation Logic

The remediation engine is modular. Every tool in `geo_audit_agent/geo_remediation_tools.py` is designed to produce **structured outputs** that search engines and LLM crawlers prioritize.

-   **JSON-LD Generator**: Produces Schema.org compliant scripts.
-   **Whitepaper Drafter**: Generates long-form technical content to improve "Knowledge Graph" presence.
-   **Review Snippets**: Synthesizes high-confidence social proof indicators.

## 3. The Audit-to-Remediation Lifecycle

The `geo_upload` module demonstrates how this is used in a production SaaS context:

1.  **`run_baseline.py`**: Captures the state of the brand *before* any intervention.
2.  **`deploy_remediation.py`**: Takes the agent's plan and "deploys" it (generating files, email templates, and publishing instructions).
3.  **`wait_and_rerun.py`**: A utility to simulate the time required for re-indexing before running a post-audit.
4.  **`measure_lift.py`**: Compares the pre and post JSON audits to calculate a "Confidence Lift" score.

## 4. State Management (`AgentState`)
```python
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
```
This state object ensures that every node in the graph has access to the full context of the audit, making the system highly reliable and auditable.
