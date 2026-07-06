from typing import Dict, Any

def generate_competitor_mock_data() -> Dict[str, Any]:
    return {
        "brand": "Burger Hub",
        "category": "fast food",
        "city": "Islamabad",
        "competitors": [
            {
                "name": "McDonald's",
                "website": "https://mcdonalds.com.pk",
                "scores": {
                    "authority": 92,
                    "schema": 95,
                    "content": 78,
                    "reviews": 90,
                    "entities": 88,
                    "citations": 85,
                    "brand": 90,
                    "overall": 88
                },
                "strengths": [
                    "Strong authority (92%)",
                    "Complete schema (95%)",
                    "Rich content ecosystem"
                ],
                "strategy": "Build hyper-local content to compete.",
                "recommendations": [
                    "Add FAQ schema",
                    "Create comparison pages",
                    "Improve mobile performance"
                ]
            },
            {
                "name": "KFC",
                "website": "https://kfcpakistan.com",
                "scores": {
                    "authority": 89,
                    "schema": 85,
                    "content": 82,
                    "reviews": 92,
                    "entities": 80,
                    "citations": 88,
                    "brand": 91,
                    "overall": 87
                },
                "strengths": [
                    "Excellent reviews (92%)",
                    "Strong brand visibility (91%)",
                    "High citation consistency"
                ],
                "strategy": "Leverage customer reviews to boost trust.",
                "recommendations": [
                    "Implement Review schema",
                    "Enhance local entity associations",
                    "Optimize Google Business Profile"
                ]
            },
            {
                "name": "Hardee's",
                "website": "https://hardees.com.pk",
                "scores": {
                    "authority": 75,
                    "schema": 60,
                    "content": 70,
                    "reviews": 85,
                    "entities": 65,
                    "citations": 72,
                    "brand": 78,
                    "overall": 72
                },
                "strengths": [
                    "Good customer sentiment (85%)",
                    "Strong local brand presence (78%)"
                ],
                "strategy": "Improve technical SEO to close the gap.",
                "recommendations": [
                    "Fix missing local business schema",
                    "Audit inconsistent citations",
                    "Publish more targeted content"
                ]
            },
            {
                "name": "Cheezious",
                "website": "https://cheezious.com",
                "scores": {
                    "authority": 65,
                    "schema": 50,
                    "content": 85,
                    "reviews": 88,
                    "entities": 60,
                    "citations": 68,
                    "brand": 80,
                    "overall": 71
                },
                "strengths": [
                    "Highly relevant content (85%)",
                    "Strong reviews and ratings (88%)"
                ],
                "strategy": "Build authority to capitalize on great content.",
                "recommendations": [
                    "Launch link building campaign",
                    "Add comprehensive schema markup",
                    "Standardize local citations"
                ]
            }
        ],
        "leaderboard": [
            {"rank": 1, "name": "McDonald's", "overall": 88},
            {"rank": 2, "name": "KFC", "overall": 87},
            {"rank": 3, "name": "Hardee's", "overall": 72},
            {"rank": 4, "name": "Cheezious", "overall": 71},
            {"rank": 5, "name": "Burger Hub", "overall": 50}
        ],
        "market_avg": {
            "authority": 68,
            "schema": 70,
            "content": 65,
            "reviews": 60,
            "entities": 55,
            "citations": 50,
            "brand": 60
        },
        "alerts": [
            {"type": "new_competitor", "message": "KFC Express discovered as an emerging threat", "severity": "medium"},
            {"type": "visibility_change", "message": "McDonald's visibility increased 3% this week", "severity": "low"},
            {"type": "schema_drop", "message": "Cheezious dropped FAQ schema", "severity": "high"}
        ],
        "trend": {
            "McDonald's": [86, 87, 88, 87, 88, 88],
            "KFC": [85, 85, 86, 86, 87, 87],
            "Hardee's": [70, 71, 71, 72, 72, 72],
            "Cheezious": [65, 67, 68, 69, 70, 71],
            "Burger Hub": [40, 42, 45, 48, 50, 50]
        },
        "timestamp": "2026-06-27T10:00:00"
    }
