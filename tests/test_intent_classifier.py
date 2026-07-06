import os
os.environ["FORCE_MOCK"] = "true"

from geo_audit_agent.context.intent_classifier import classify


def test_audit_intent():
    assert classify("run an audit on my brand") == "audit"


def test_deploy_intent():
    assert classify("deploy the JSON-LD schema") == "deploy"


def test_compare_intent():
    assert classify("compare us vs competitors") == "compare"


def test_recommend_intent():
    assert classify("what should i fix first?") == "recommend"


def test_help_intent():
    assert classify("help me understand this") == "help"


def test_visibility_intent():
    assert classify("where am i visible?") == "visibility"


def test_score_intent():
    assert classify("what is my GEO score?") == "score"


def test_empty_message():
    assert classify("") == "smalltalk"


def test_keyword_intent():
    assert classify("track this keyword for me") == "keyword"


def test_chart_intent():
    assert classify("explain this chart please") == "explain_chart"
