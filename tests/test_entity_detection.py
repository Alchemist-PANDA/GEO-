from geo_audit_agent.metrics.entity_detection import EntityVerdict, detect_entity


def test_exact_entity_match_uses_boundaries():
    assert detect_entity("Ola is recommended", "Ola").verdict is EntityVerdict.MATCH
    assert detect_entity("Solar panels are recommended", "Ola").verdict is EntityVerdict.NO_MATCH


def test_alias_and_domain_match():
    assert detect_entity("Try Acme Coffee Co.", "Acme", aliases=["Acme Coffee Co"]).verdict is EntityVerdict.MATCH
    assert detect_entity("See acmecoffee.com", "Acme Coffee", domain="acmecoffee.com").verdict is EntityVerdict.MATCH


def test_partial_multiword_name_is_uncertain():
    result = detect_entity("The neighborhood hub is busy", "Burger Hub")
    assert result.verdict is EntityVerdict.UNCERTAIN
    assert result.confidence == 0.5
