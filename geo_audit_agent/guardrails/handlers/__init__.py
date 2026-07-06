"""Guardrail handlers. Each returns a list[Violation] (possibly empty).
Deterministic checks inline; semantic checks call NeMo / the LLM gateway."""
import os
import re
from urllib.parse import urlparse
from geo_audit_agent.guardrails.types import Violation, Severity as S

# ---- 1. INPUT GUARDRAIL (full) ----
_INJECTION = re.compile(r"(ignore (all|previous) instructions|system prompt|"
    r"you are now|disregard|reveal your|base64|<script|--\s*$|union select)", re.I)
_SQLI = re.compile(r"('|\")\s*(or|and)\s*\d+=\d+|;\s*drop\s+table", re.I)


def input_guardrail(payload: dict) -> list[Violation]:
    v = []
    text = (payload.get("user_message") or payload.get("input_text") or "")[:20000]
    if len(text) > 8000:
        v.append(Violation("input", "max_length", S.MEDIUM, "Prompt exceeds 8000 chars"))
    if _INJECTION.search(text):
        v.append(Violation("input", "prompt_injection", S.HIGH, "Injection/jailbreak pattern detected"))
    if _SQLI.search(text):
        v.append(Violation("input", "sql_injection", S.HIGH, "SQL injection pattern detected"))
    if "<script" in text.lower():
        v.append(Violation("input", "xss", S.HIGH, "XSS pattern detected"))
    brand = payload.get("brand_name")
    if brand is not None and (not brand.strip() or len(brand) > 255):
        v.append(Violation("input", "invalid_brand", S.MEDIUM, "Brand name empty or too long"))
    url = payload.get("website_url")
    if url:
        p = urlparse(url)
        if p.scheme not in ("http", "https") or not p.netloc:
            v.append(Violation("input", "invalid_url", S.MEDIUM, f"Malformed URL: {url}"))
    if os.getenv("FORCE_MOCK") != "true":
        try:
            from geo_audit_agent.services.guardrails import classify_input
            if classify_input(text).classification == "unsafe":
                v.append(Violation("input", "semantic_unsafe", S.HIGH, "Classifier flagged input unsafe"))
        except Exception:
            pass
    return v


# ---- 2. CONTEXT GUARDRAIL ----
def context_guardrail(payload: dict) -> list[Violation]:
    v = []
    evidence = payload.get("evidence", [])
    if payload.get("query") and not evidence:
        v.append(Violation("context", "no_evidence", S.MEDIUM, "No evidence retrieved for query"))
    sources = {e.get("source") for e in payload.get("evidence_meta", []) if isinstance(e, dict)}
    if len(evidence) > 2 and len(sources) < 2:
        v.append(Violation("context", "low_diversity", S.LOW, "Evidence from fewer than 2 sources"))
    est_tokens = sum(len(str(e)) for e in evidence) // 4
    budget = int(os.getenv("AGENTIC_MAX_TOKENS_PER_REQUEST", "120000"))
    if est_tokens > budget:
        v.append(Violation("context", "over_budget", S.HIGH, f"Context tokens {est_tokens} > budget {budget}"))
    return v


# ---- 3. RETRIEVAL GUARDRAIL ----
def retrieval_guardrail(payload: dict) -> list[Violation]:
    v = []
    results = payload.get("retrieval_results", [])
    for r in results:
        trust = r.get("trust_score", 1.0) if isinstance(r, dict) else 1.0
        if trust < 0.3:
            v.append(Violation("retrieval", "low_trust_source", S.MEDIUM,
                f"Retrieved doc has low trust score: {trust}"))
    if payload.get("query") and not results:
        v.append(Violation("retrieval", "empty_retrieval", S.LOW, "No documents retrieved"))
    return v


# ---- 4. MEMORY GUARDRAIL ----
_SENSITIVE_MEM = re.compile(r"\b(password|api[_ ]?key|ssn|credit card|secret|token)\b", re.I)

def memory_guardrail(payload: dict) -> list[Violation]:
    v = []
    text = payload.get("memory_text", "")
    if _SENSITIVE_MEM.search(text):
        v.append(Violation("memory", "sensitive_data", S.HIGH, "Memory contains sensitive information"))
    if payload.get("user_id") and payload.get("target_user_id"):
        if payload["user_id"] != payload["target_user_id"]:
            v.append(Violation("memory", "cross_user_access", S.CRITICAL,
                "Attempted to access another user's memory"))
    return v


# ---- 5. TOOL GUARDRAIL ----
_ALLOWED_TOOLS = {
    "generate_json_ld", "draft_technical_whitepaper", "generate_review_template",
    "deploy_json_ld", "deploy_faq_schema", "deploy_howto_schema",
    "generate_faq_page", "create_comparison_pages", "create_location_pages",
    "generate_blog_post", "create_best_of_listicle", "send_review_requests",
    "draft_review_responses", "publish_testimonials", "post_to_google_business",
    "update_google_business_info", "submit_to_directories", "post_to_linkedin",
    "generate_weekly_report",
}

def tool_guardrail(payload: dict) -> list[Violation]:
    v = []
    tool_name = payload.get("tool_name", "")
    if tool_name and tool_name not in _ALLOWED_TOOLS:
        v.append(Violation("tool", "unknown_tool", S.HIGH, f"Tool '{tool_name}' not in allowed registry"))
    tool_input = str(payload.get("tool_input", ""))
    if _INJECTION.search(tool_input):
        v.append(Violation("tool", "injection_in_input", S.HIGH, "Injection pattern in tool input"))
    return v


# ---- 6. AGENT GUARDRAIL ----
def agent_guardrail(payload: dict) -> list[Violation]:
    v = []
    depth = payload.get("recursion_depth", 0)
    if depth > 10:
        v.append(Violation("agent", "max_recursion", S.HIGH, f"Agent recursion depth {depth} > 10"))
    elapsed_s = payload.get("elapsed_seconds", 0)
    if elapsed_s > 120:
        v.append(Violation("agent", "timeout", S.HIGH, f"Agent running for {elapsed_s}s > 120s limit"))
    return v


# ---- 7. BUSINESS GUARDRAIL (full) ----
def business_guardrail(payload: dict) -> list[Violation]:
    v = []
    rec = payload.get("recommendation")
    if rec and not payload.get("evidence"):
        v.append(Violation("business", "rec_requires_evidence", S.HIGH,
            "Recommendation produced without supporting evidence"))
    if payload.get("visibility_score_invented"):
        v.append(Violation("business", "no_invented_scores", S.CRITICAL,
            "Visibility score not traceable to audit data"))
    if rec and payload.get("confidence") is None:
        v.append(Violation("business", "confidence_required", S.MEDIUM,
            "Recommendation missing confidence score"))
    return v


# ---- 8. OUTPUT GUARDRAIL ----
_LEAK_PATTERNS = re.compile(
    r"(system prompt|<\|im_start\||<\|endoftext\||internal instructions|"
    r"you are a|as an ai|my instructions say)", re.I)

def output_guardrail(payload: dict) -> list[Violation]:
    v = []
    text = payload.get("output_text", "")
    if _LEAK_PATTERNS.search(text):
        v.append(Violation("output", "prompt_leak", S.HIGH, "Output contains prompt/instruction leakage"))
    if len(text) > 15000:
        v.append(Violation("output", "excessive_length", S.MEDIUM, f"Output length {len(text)} > 15000"))
    if not text.strip():
        v.append(Violation("output", "empty_output", S.MEDIUM, "Output is empty"))
    return v


# ---- 9. SECURITY GUARDRAIL ----
_PII = re.compile(r"\b(\d{3}-\d{2}-\d{4}|\d{16}|[A-Z]{2}\d{6,8})\b")
_SECRETS = re.compile(r"\b(sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{36}|AKIA[A-Z0-9]{16})\b")

def security_guardrail(payload: dict) -> list[Violation]:
    v = []
    text = str(payload.get("text", "") or payload.get("output_text", "") or payload.get("input_text", ""))
    if _PII.search(text):
        v.append(Violation("security", "pii_detected", S.HIGH, "PII pattern detected (SSN/CC/passport)"))
    if _SECRETS.search(text):
        v.append(Violation("security", "secret_detected", S.CRITICAL, "API key or secret detected"))
    if payload.get("file_path"):
        path = payload["file_path"]
        if ".." in path or path.startswith("/etc") or path.startswith("/root"):
            v.append(Violation("security", "path_traversal", S.CRITICAL, f"Suspicious file path: {path}"))
    return v


# ---- 10. COST GUARDRAIL (full) ----
def cost_guardrail(payload: dict) -> list[Violation]:
    v = []
    ceiling = int(os.getenv("AGENTIC_MAX_TOKENS_PER_REQUEST", "120000"))
    if payload.get("projected_tokens", 0) > ceiling:
        v.append(Violation("cost", "max_tokens", S.HIGH,
            f"Projected {payload['projected_tokens']} > ceiling {ceiling}"))
    if payload.get("daily_spend_usd", 0) > float(os.getenv("AGENTIC_DAILY_USD_BUDGET", "50")):
        v.append(Violation("cost", "daily_budget", S.HIGH, "Daily USD budget exceeded"))
    return v


# ---- 11. WORKFLOW GUARDRAIL ----
_VALID_TRANSITIONS = {
    "input_guard": {"context", "inspector"},
    "context": {"policy"},
    "policy": {"audit", "competitor", "copilot", "action", "inspector"},
    "audit": {"inspector"},
    "competitor": {"inspector"},
    "copilot": {"inspector"},
    "action": {"inspector"},
}

def workflow_guardrail(payload: dict) -> list[Violation]:
    v = []
    current = payload.get("current_node", "")
    target = payload.get("target_node", "")
    if current and target:
        allowed = _VALID_TRANSITIONS.get(current, set())
        if allowed and target not in allowed:
            v.append(Violation("workflow", "invalid_transition", S.HIGH,
                f"Transition {current} -> {target} not allowed"))
    if payload.get("loop_count", 0) > 5:
        v.append(Violation("workflow", "loop_detected", S.HIGH, "Workflow loop detected"))
    return v


# ---- 12. HUMAN APPROVAL GUARDRAIL (full) ----
_APPROVAL_REQUIRED = {"deploy_json_ld", "deploy_faq_schema", "deploy_howto_schema",
    "post_to_google_business", "update_google_business_info", "post_to_linkedin",
    "send_review_requests", "submit_to_directories", "delete_data", "publish_testimonials"}

def human_approval_guardrail(payload: dict) -> list[Violation]:
    action = payload.get("action_id")
    if action in _APPROVAL_REQUIRED and not payload.get("human_approved"):
        return [Violation("human_approval", "approval_required", S.CRITICAL,
            f"Action '{action}' requires human approval before execution")]
    return []
