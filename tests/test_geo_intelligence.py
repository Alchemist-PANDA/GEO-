import sys
import os
import unittest

# Ensure the package is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geo_audit_agent.geo_intelligence.predictor import build_training_data
from geo_audit_agent.geo_intelligence.anomaly_detector import compute_semantic_similarity
from geo_audit_agent.geo_intelligence.fingerprint_generator import extract_tfidf_keywords

class TestGeoIntelligence(unittest.TestCase):
    def test_predictor_data(self):
        df = build_training_data()
        self.assertFalse(df.empty)
    
    def test_anomaly_similarity(self):
        # Using exact same words to ensure intersection/union > 0.5 in dummy logic
        score = compute_semantic_similarity("Burger Hub", "Burger Hub")
        self.assertEqual(score, 1.0)

    def test_fingerprint_keywords(self):
        keywords = extract_tfidf_keywords("Burger Hub offers the best fast food.")
        self.assertIn('burger', keywords)

if __name__ == '__main__':
    unittest.main()
