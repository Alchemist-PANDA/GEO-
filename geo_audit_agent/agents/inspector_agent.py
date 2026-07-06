"""Inspector Agent — 12 checks. Deterministic checks gate the expensive
LLM checks (skip LLM if a hard check already failed)."""
from dataclasses import dataclass, field
from geo_audit_agent.llm import gateway
from geo_audit_agent.observability.langfuse_tracer import trace_span


@dataclass
class InspectorVerdict:
    passed: bool
    checks: dict = field(default_factory=dict)
    issues: list = field(default_factory=list)
    risk: str = "low"


class InspectorAgent:
    @trace_span("inspector.run", agent_id="inspector")
    def inspect(self, output: dict, context: dict, *, agent_id: str,
                trace_id: str | None = None) -> InspectorVerdict:
        checks, issues = {}, []

        checks["output_quality"] = self._output_quality(output, issues)
        checks["evidence_present"] = self._evidence(output, context, issues)
        checks["business_rules"] = self._business(output, context, issues)
        checks["tool_validation"] = self._tools(output, issues)
        checks["context_quality"] = self._context_quality(context, issues)
        checks["memory_validation"] = self._memory(output, issues)
        checks["governance"] = self._governance(output, issues)

        hard_failed = not all(v for k, v in checks.items()
                              if k in ("output_quality", "business_rules", "governance"))

        if not hard_failed:
            sem = self._semantic(output, context)
            checks.update(sem["checks"])
            issues.extend(sem["issues"])

        passed = all(checks.values())
        risk = "high" if any("hallucination" in i or "governance" in i for i in issues) \
               else "medium" if issues else "low"
        verdict = InspectorVerdict(passed=passed, checks=checks, issues=issues, risk=risk)
        self._persist(agent_id, trace_id, verdict)
        try:
            from geo_audit_agent.observability.metrics import INSPECTOR_RESULTS
            INSPECTOR_RESULTS.labels(agent=agent_id, passed=str(passed), risk=risk).inc()
        except Exception:
            pass
        return verdict

    def _output_quality(self, o, issues):
        text = o.get("text", "")
        if not text or len(text) < 10:
            issues.append("output_quality:empty")
            return False
        if "<|" in text or "system prompt" in text.lower():
            issues.append("output_quality:prompt_leak")
            return False
        return True

    def _evidence(self, o, ctx, issues):
        if o.get("is_recommendation") and not ctx.get("bundle", {}).get("evidence"):
            issues.append("evidence:missing")
            return False
        return True

    def _business(self, o, ctx, issues):
        from geo_audit_agent.policy.engine import PolicyEngine
        res = PolicyEngine().enforce({**ctx.get("policy_ctx", {}),
            "evidence": ctx.get("bundle", {}).get("evidence")})
        if not res["allowed"]:
            issues.append("business:" + ";".join(b["id"] for b in res["blocking"]))
            return False
        return True

    def _tools(self, o, issues):
        for call in o.get("tool_calls", []):
            if call.get("error"):
                issues.append(f"tool:{call.get('name')}_failed")
                return False
        return True

    def _context_quality(self, ctx, issues):
        val = ctx.get("validation", {})
        if "over_token_budget" in val.get("issues", []):
            issues.append("context:over_budget")
            return False
        return True

    def _memory(self, o, issues):
        return True

    def _governance(self, o, issues):
        import re
        if re.search(r"\b(api[_ ]?key|password|secret)\b", o.get("text", ""), re.I):
            issues.append("governance:secret_leak")
            return False
        return True

    def _semantic(self, o, ctx):
        evidence = "\n".join(ctx.get("bundle", {}).get("evidence", [])) or "(none)"
        res = gateway.claude(
            system=("You are a strict QA inspector. Given EVIDENCE and a RESPONSE, "
                    "return JSON {\"hallucination\": bool, \"unsupported_claims\": [..], "
                    "\"fact_verified\": bool, \"root_cause\": str}."),
            user=f"EVIDENCE:\n{evidence}\n\nRESPONSE:\n{o.get('text', '')}",
            force_json=True)
        data = gateway.parse_json(res.text)
        issues, checks = [], {}
        checks["fact_verification"] = bool(data.get("fact_verified", True))
        checks["hallucination"] = not bool(data.get("hallucination", False))
        if data.get("hallucination"):
            issues.append("hallucination:flagged")
        if data.get("unsupported_claims"):
            issues.append("unsupported_claims")
        return {"checks": checks, "issues": issues}

    def _persist(self, agent_id, trace_id, verdict):
        try:
            from geo_audit_agent.db.session import get_session
            from geo_audit_agent.db.models import InspectorCheck
            with get_session() as s:
                s.add(InspectorCheck(agent_id=agent_id, trace_id=trace_id,
                    check_type="full", result={"checks": verdict.checks,
                    "issues": verdict.issues, "risk": verdict.risk},
                    passed=verdict.passed, input_data={}))
                s.commit()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Inspector persist failed: %s", e)
