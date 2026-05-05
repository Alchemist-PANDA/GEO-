import json
import os

def calculate_lift(pre_file, post_file):
    with open(pre_file, 'r') as f:
        pre = json.load(f)
    with open(post_file, 'r') as f:
        post = json.load(f)

    pre_cited = pre.get('is_cited', False)
    post_cited = post.get('is_cited', False)
    pre_score = pre.get('confidence_score', 0.0)
    post_score = post.get('confidence_score', 0.0)

    score_diff = post_score - pre_score
    score_pct_change = (score_diff / pre_score) * 100 if pre_score != 0 else 0

    if score_diff > 0.01:
        conclusion = f"Positive lift observed (+{round(score_pct_change, 1)}%). GEO deployment likely contributed to increased visibility."
    elif score_diff < -0.01:
        conclusion = f"Negative change observed ({round(score_pct_change, 1)}%). Visibility decreased after deployment."
    else:
        conclusion = "No significant change in confidence score."

    lift_report = {
        "brand_name": pre.get('brand_name'),
        "pre_remediation": {
            "is_cited": pre_cited,
            "confidence_score": pre_score
        },
        "post_remediation": {
            "is_cited": post_cited,
            "confidence_score": post_score
        },
        "lift": {
            "is_cited_improved": post_cited and not pre_cited,
            "is_cited_maintained": post_cited and pre_cited,
            "confidence_score_absolute_change": round(score_diff, 4),
            "confidence_score_percentage_change": round(score_pct_change, 2)
        },
        "conclusion": conclusion
    }

    with open('final_lift_report.json', 'w') as f:
        json.dump(lift_report, f, indent=4)

    return lift_report

if __name__ == "__main__":
    report = calculate_lift('pre_remediation_audit.json', 'post_remediation_audit.json')
    print(json.dumps(report, indent=4))
