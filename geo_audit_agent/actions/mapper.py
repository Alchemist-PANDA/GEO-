"""Map audit gap types to candidate actions, ranked by impact/effort ratio."""
from geo_audit_agent.actions.registry import REGISTRY, Action

_GAP_MAP = {
    "structured data": ["deploy_json_ld", "deploy_faq_schema"],
    "schema":          ["deploy_json_ld", "deploy_howto_schema"],
    "third-party reviews": ["send_review_requests", "draft_review_responses", "publish_testimonials"],
    "authority":       ["generate_blog_post", "create_comparison_pages"],
    "content":         ["generate_faq_page", "create_location_pages", "create_best_of_listicle"],
    "local":           ["post_to_google_business", "update_google_business_info", "submit_to_directories"],
}

def map_gaps_to_actions(gaps: list[dict]) -> list[Action]:
    chosen, seen = [], set()
    for gap in gaps:
        key = (gap.get("gap_type", "") + " " + gap.get("description", "")).lower()
        for gap_kw, action_ids in _GAP_MAP.items():
            if gap_kw in key:
                for aid in action_ids:
                    if aid not in seen:
                        seen.add(aid)
                        chosen.append(REGISTRY[aid])
    return sorted(chosen, key=lambda a: a.impact_pct / max(a.effort_min, 1), reverse=True)
