"""DeepEval harness. Offline -> deterministic proxy metrics; online -> LLM judges."""
import os


def evaluate_case(*, input_text, actual_output, expected_output=None, context=None):
    if os.getenv("FORCE_MOCK") == "true" or not os.getenv("ANTHROPIC_API_KEY"):
        if expected_output:
            a, b = set(actual_output.lower().split()), set(expected_output.lower().split())
            return {"answer_relevancy": len(a & b) / max(len(b), 1)}
        return {"answer_relevancy": 1.0 if actual_output else 0.0}
    from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
    from deepeval.test_case import LLMTestCase
    tc = LLMTestCase(input=input_text, actual_output=actual_output,
                     expected_output=expected_output, retrieval_context=context or [])
    out = {}
    for M in (AnswerRelevancyMetric(threshold=0.7), FaithfulnessMetric(threshold=0.7)):
        M.measure(tc)
        out[M.__class__.__name__] = M.score
    return out
