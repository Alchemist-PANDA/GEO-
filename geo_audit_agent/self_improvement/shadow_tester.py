"""Replay the proposed variant against the golden set; promote only if
aggregate score does not regress."""
from geo_audit_agent.evaluation import golden_set, deep_eval


def shadow_test(apply_variant) -> dict:
    cases = golden_set.load()
    if not cases:
        return {"passed": False, "reason": "empty_golden_set"}
    before = after = 0.0
    for c in cases:
        base = deep_eval.evaluate_case(input_text=c["input"],
            actual_output=c.get("baseline_output", ""), expected_output=c["expected_output"],
            context=c.get("context"))
        variant_output = apply_variant(c)
        var = deep_eval.evaluate_case(input_text=c["input"], actual_output=variant_output,
            expected_output=c["expected_output"], context=c.get("context"))
        before += sum(base.values()) / len(base)
        after += sum(var.values()) / len(var)
    n = len(cases)
    return {"passed": after >= before, "before": round(before / n, 3),
            "after": round(after / n, 3)}
