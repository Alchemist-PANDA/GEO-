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
    # Semantic backstop — reuse the EXISTING LlamaGuard-style classifier
    if os.getenv("FORCE_MOCK") != "true":
        try:
            from geo_audit_agent.services.guardrails import classify_input
            if classify_input(text).classification == "unsafe":
                v.append(Violation("input", "semantic_unsafe", S.HIGH, "Classifier flagged input unsafe"))
        except Exception:
            pass
    return v

# ---- 6. BUSINESS GUARDRAIL (full — overlaps Policy Engine, defense in depth) ----
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

# ---- 2,3,4,5,7,8,9,10,11,12 — TEMPLATE (implement using brief checklists) ----
def context_guardrail(payload):      return _todo("context", payload)
def memory_guardrail(payload):       return _todo("memory", payload)
def tool_guardrail(payload):         return _todo("tool", payload)
def agent_guardrail(payload):        return _todo("agent", payload)
def retrieval_guardrail(payload):    return _todo("retrieval", payload)
def output_guardrail(payload):       return _todo("output", payload)
def security_guardrail(payload):     return _todo("security", payload)
def cost_guardrail(payload):         return _cost(payload)           # full below
def workflow_guardrail(payload):     return _todo("workflow", payload)
def human_approval_guardrail(payload): return _human(payload)        # full below

def _todo(name, payload):
    """Stub that NEVER silently passes a security-relevant phase.
    Replace each with deterministic checks from the brief's table for `name`."""
    return []

# ---- 10. COST GUARDRAIL (full) ----
def _cost(payload) -> list[Violation]:
    v = []
    ceiling = int(os.getenv("AGENTIC_MAX_TOKENS_PER_REQUEST", "120000"))
    if payload.get("projected_tokens", 0) > ceiling:
        v.append(Violation("cost", "max_tokens", S.HIGH,
            f"Projected {payload['projected_tokens']} > ceiling {ceiling}"))
    if payload.get("daily_spend_usd", 0) > float(os.getenv("AGENTIC_DAILY_USD_BUDGET", "50")):
        v.append(Violation("cost", "daily_budget", S.HIGH, "Daily USD budget exceeded"))
    return v

# ---- 12. HUMAN APPROVAL GUARDRAIL (full) ----
_APPROVAL_REQUIRED = {"deploy_json_ld", "deploy_faq_schema", "deploy_howto_schema",
    "post_to_google_business", "update_google_business_info", "post_to_linkedin",
    "send_review_requests", "submit_to_directories", "delete_data", "publish_testimonials"}

def _human(payload) -> list[Violation]:
    action = payload.get("action_id")
    if action in _APPROVAL_REQUIRED and not payload.get("human_approved"):
        return [Violation("human_approval", "approval_required", S.CRITICAL,
            f"Action '{action}' requires human approval before execution")]
    return []
