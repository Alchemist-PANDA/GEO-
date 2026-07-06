import os
os.environ["FORCE_MOCK"] = "true"

from geo_audit_agent.actions.mapper import map_gaps_to_actions


def test_mapper_maps_structured_data_gap():
    gaps = [{"gap_type": "structured data", "description": "Missing JSON-LD schema"}]
    actions = map_gaps_to_actions(gaps)
    assert len(actions) >= 1
    assert any(a.id == "deploy_json_ld" for a in actions)


def test_mapper_maps_review_gap():
    gaps = [{"gap_type": "third-party reviews", "description": "Few reviews"}]
    actions = map_gaps_to_actions(gaps)
    assert any(a.id == "send_review_requests" for a in actions)


def test_mapper_maps_content_gap():
    gaps = [{"gap_type": "content", "description": "Limited content pages"}]
    actions = map_gaps_to_actions(gaps)
    assert any(a.id == "generate_faq_page" for a in actions)


def test_mapper_ranks_by_roi():
    gaps = [
        {"gap_type": "structured data", "description": "Missing schema"},
        {"gap_type": "content", "description": "Needs more content"},
    ]
    actions = map_gaps_to_actions(gaps)
    if len(actions) >= 2:
        for i in range(len(actions) - 1):
            roi_a = actions[i].impact_pct / max(actions[i].effort_min, 1)
            roi_b = actions[i+1].impact_pct / max(actions[i+1].effort_min, 1)
            assert roi_a >= roi_b


def test_mapper_deduplicates():
    gaps = [
        {"gap_type": "structured data", "description": "Missing schema"},
        {"gap_type": "schema", "description": "No schema markup"},
    ]
    actions = map_gaps_to_actions(gaps)
    ids = [a.id for a in actions]
    assert len(ids) == len(set(ids))


def test_mapper_empty_gaps():
    actions = map_gaps_to_actions([])
    assert actions == []
