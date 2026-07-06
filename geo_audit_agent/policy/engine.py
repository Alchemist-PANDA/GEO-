from geo_audit_agent.policy.rules import RULES, PolicyRule


class PolicyEngine:
    def __init__(self, rules: list[PolicyRule] | None = None):
        self.rules = rules if rules is not None else RULES

    def evaluate(self, context: dict) -> list[PolicyRule]:
        violated = []
        for rule in self.rules:
            try:
                if rule.condition(context):
                    violated.append(rule)
            except Exception:
                continue
        return violated

    def enforce(self, context: dict) -> dict:
        violations = self.evaluate(context)
        blocking = [r for r in violations if r.action == "BLOCK"]
        warnings = [r for r in violations if r.action == "WARN"]
        try:
            from geo_audit_agent.observability.metrics import POLICY_BLOCKS
            for r in blocking:
                POLICY_BLOCKS.labels(rule_id=r.id).inc()
        except Exception:
            pass
        return {
            "allowed": not blocking,
            "blocking": [{"id": r.id, "message": r.message} for r in blocking],
            "warnings": [{"id": r.id, "message": r.message} for r in warnings],
        }
