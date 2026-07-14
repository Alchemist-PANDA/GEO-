"""The 16 actions. Each ACTION is metadata + an executor reference."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Action:
    id: str
    title: str
    category: str
    impact_pct: float
    effort_min: int
    platform: str
    requires_approval: bool
    executor: str


REGISTRY: dict[str, Action] = {
    "deploy_json_ld":      Action("deploy_json_ld", "Deploy JSON-LD Schema", "structured_data", 8.0, 5, "WordPress", True, "deploy_json_ld"),
    "deploy_faq_schema":   Action("deploy_faq_schema", "Deploy FAQ Schema", "structured_data", 5.0, 5, "WordPress", True, "deploy_faq_schema"),
    "deploy_howto_schema": Action("deploy_howto_schema", "Deploy HowTo Schema", "structured_data", 4.0, 5, "WordPress", True, "deploy_howto_schema"),
    "generate_faq_page":   Action("generate_faq_page", "Generate FAQ Page", "content", 6.0, 15, "file", False, "generate_faq_page"),
    "create_comparison_pages": Action("create_comparison_pages", "Create Comparison Pages", "content", 7.0, 20, "file", False, "create_comparison_pages"),
    "create_location_pages":   Action("create_location_pages", "Create Location Pages", "content", 6.5, 20, "file", False, "create_location_pages"),
    "generate_blog_post":  Action("generate_blog_post", "Generate Blog Post", "content", 4.0, 25, "file", False, "generate_blog_post"),
    "create_best_of_listicle": Action("create_best_of_listicle", "Create 'Best of' Listicle", "content", 5.5, 20, "file", False, "create_best_of_listicle"),
    "send_review_requests":    Action("send_review_requests", "Send Review Requests", "reviews", 7.5, 10, "Email", True, "send_review_requests"),
    "draft_review_responses":  Action("draft_review_responses", "Draft Review Responses", "reviews", 3.0, 15, "file", False, "draft_review_responses"),
    "publish_testimonials":    Action("publish_testimonials", "Publish Testimonials", "reviews", 3.5, 10, "WordPress", True, "publish_testimonials"),
    "post_to_google_business": Action("post_to_google_business", "Post to Google Business", "local_seo", 6.0, 5, "Google Business", True, "post_to_google_business"),
    "update_google_business_info": Action("update_google_business_info", "Update Google Business Info", "local_seo", 5.0, 10, "Google Business", True, "update_google_business_info"),
    "submit_to_directories":   Action("submit_to_directories", "Submit to Directories", "local_seo", 4.5, 15, "Directories", True, "submit_to_directories"),
    "post_to_linkedin":        Action("post_to_linkedin", "Post to LinkedIn", "social", 3.0, 10, "LinkedIn", True, "post_to_linkedin"),
    "generate_weekly_report":  Action("generate_weekly_report", "Generate Weekly Report", "monitoring", 0.0, 5, "file", False, "generate_weekly_report"),
}
