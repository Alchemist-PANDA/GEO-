import json
from geo_audit_agent.geo_intelligence.predictor import predict_score

def main():
    kfc_features = {
        'brand_name': 'KFC',
        'category': 'fast food',
        'city': 'Islamabad',
        'has_json_ld': 0,
        'has_technical_whitepaper': 0,
        'has_reviews': 1,
        'competition_level': 2,
        'brand_age_months': 120,
        'backlink_count': 2000,
        'semantic_score': 0.7
    }
    
    score = predict_score(kfc_features)
    print(f"Predicted GEO Potential Score for KFC Islamabad: {score:.2f}")
    
    # Also predict with GEO improvements
    kfc_improved = kfc_features.copy()
    kfc_improved['has_json_ld'] = 1
    kfc_improved['has_technical_whitepaper'] = 1
    kfc_improved['semantic_score'] = 0.9
    
    improved_score = predict_score(kfc_improved)
    print(f"Predicted GEO Potential Score for KFC Islamabad (Optimized): {improved_score:.2f}")
    
    report = {
        "brand": "KFC",
        "current_score": round(score, 2),
        "optimized_score": round(improved_score, 2),
        "potential_lift": round(improved_score - score, 2)
    }
    
    with open('kfc_prediction.json', 'w') as f:
        json.dump(report, f, indent=4)

if __name__ == "__main__":
    main()
