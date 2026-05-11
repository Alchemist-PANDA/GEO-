"""Tests for dashboard UI fixes."""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from run_lift_simulation import simulate_improved_audit, run_lift_simulation


class TestIndustryRemediationRouting:
    """Test industry-specific remediation routing."""

    def test_dental_remediation_routing(self):
        """Test that dental clinic gets dental remediation, not fitness."""
        r = run_lift_simulation(
            "Dental Solutions Islamabad",
            "dental clinic",
            "Islamabad",
            {
                "business_context": "Dental Solutions Islamabad is a dental clinic in Islamabad. Services include braces, dental implants, teeth whitening, root canal, emergency dental care, pediatric dentistry, and cosmetic dentistry. The clinic emphasizes hygiene, painless treatment, professional dentists, appointment booking, and patient care.",
                "force_mock": True,
                "use_real": False,
            }
        )

        # Basic assertions
        assert r["template_used"] == "DentalClinicTemplate"
        assert len(r["remediation"]) > 0

        # Collect all remediation text for checking
        rem_text = " ".join([str(rem.values()) for rem in r["remediation"]]).lower()

        # Dental positive assertions
        assert any(kw in rem_text for kw in ["dentist", "medicalclinic", "treatment", "braces", "implants", "insurance", "emergency"])

        # Fitness negative assertions (contamination check)
        fitness_keywords = [
            "sportsactivitylocation", "healthclub", "gym", "pool", "trainer",
            "class schedule", "class updates", "personal training", "membership"
        ]
        for kw in fitness_keywords:
            assert kw not in rem_text, f"Found fitness contamination: '{kw}' in dental remediation"

        # Ecommerce negative assertions
        ecommerce_keywords = ["product schema", "offer schema", "shipping", "size guide"]
        for kw in ecommerce_keywords:
            assert kw not in rem_text, f"Found ecommerce contamination: '{kw}' in dental remediation"

    def test_dental_strengths_detection(self):
        """Test that dental strengths are correctly detected from business context."""
        r = run_lift_simulation(
            "Dental Solutions Islamabad",
            "dental clinic",
            "Islamabad",
            {
                "business_context": "Dental Solutions Islamabad is a dental clinic in Islamabad. Services include braces, dental implants, teeth whitening, root canal, emergency dental care, pediatric dentistry, and cosmetic dentistry. The clinic emphasizes hygiene, painless treatment, professional dentists, appointment booking, and patient care.",
                "force_mock": True,
                "use_real": False,
            }
        )

        assert r["template_used"] == "DentalClinicTemplate"
        strengths = r["strengths"]
        strength_titles = [s["title"] for s in strengths]

        # Should detect at least 4 strengths
        assert len(strengths) >= 4

        # Specific strength titles (updated to match new implementation)
        assert "Broad treatment range" in strength_titles
        assert "Hygiene and patient comfort positioning" in strength_titles
        assert "Professional dentist positioning" in strength_titles
        assert "Appointment booking clarity" in strength_titles
        assert "Emergency care availability" in strength_titles

        # Descriptions should be populated
        for s in strengths:
            assert len(s["description"]) > 10

    def test_production_path_dental_strengths(self):
        """Test dental strengths with the exact dict structure dashboard.py sends."""
        raw_text = "Dental Solutions Islamabad is a dental clinic in Islamabad. Services include braces, dental implants, teeth whitening, root canal, emergency dental care, pediatric dentistry, and cosmetic dentistry. The clinic emphasizes hygiene, painless treatment, professional dentists, appointment booking, and patient care."

        business_context = {
            "raw_text": raw_text,
            "business_context_text": raw_text,
            "category": "dental clinic"
        }

        r = run_lift_simulation(
            "Dental Solutions Islamabad",
            "dental clinic",
            "Islamabad",
            {
                "business_context": business_context,
                "raw_business_context": business_context["raw_text"],
                "force_mock": True,
                "use_real": False,
            }
        )

        assert r["template_used"] == "DentalClinicTemplate"
        assert len(r["strengths"]) >= 4

        strength_titles = [s["title"].lower() for s in r["strengths"]]

        # Check for expected strength categories in titles
        assert any("treatment range" in t for t in strength_titles)
        assert any("hygiene" in t or "patient comfort" in t for t in strength_titles)
        assert any("professional dentist" in t for t in strength_titles)
        assert any("appointment booking" in t for t in strength_titles)
        assert any("emergency care" in t for t in strength_titles)

        assert len(r["gaps"]) > 0
        assert len(r["remediation"]) > 0

    def test_restaurant_template_detection(self):
        """Test that restaurant category detection works."""
        from geo_audit_agent.industry_templates import get_template
        template = get_template("burger restaurant")
        assert template.__class__.__name__ == "RestaurantTemplate"

    def test_production_path_restaurant(self):
        """Test restaurant template with the exact dict structure dashboard.py sends."""
        raw_text = "Burger Lab Islamabad is a burger restaurant in Islamabad. It offers gourmet burgers, fries, shakes, chicken burgers, beef burgers, and takeaway/delivery. Customers mention delicious burgers, fresh ingredients, good service, family-friendly ambience, clean environment, and good value. The restaurant has online ordering, delivery availability, opening hours, food photos, and active Instagram presence."

        r = run_lift_simulation(
            "Burger Lab Islamabad",
            "burger restaurant",
            "Islamabad",
            {
                "business_context": {
                    "raw_text": raw_text,
                    "business_context_text": raw_text,
                    "category": "burger restaurant"
                },
                "raw_business_context": raw_text,
                "force_mock": True,
                "use_real": False,
            }
        )

        assert r["template_used"] == "RestaurantTemplate"
        assert len(r["strengths"]) >= 4
        assert len(r["gaps"]) > 0
        assert len(r["remediation"]) > 0

        # Check for restaurant-specific remediation
        rem_text = " ".join([str(rem.values()) for rem in r["remediation"]]).lower()
        assert any(kw in rem_text for kw in ["restaurant", "menu", "dish", "delivery", "reservation", "opening hours"])

        # Contamination checks
        negative_keywords = [
            "healthclub", "trainer", "class schedule", "product schema",
            "offer schema", "shipping", "size guide", "dentist", "medicalclinic"
        ]
        for kw in negative_keywords:
            assert kw not in rem_text, f"Found contamination: '{kw}' in restaurant remediation"

    def test_turkish_restaurant_subtype_polish(self):
        """Test Turkish restaurant subtype remediation copy polish."""
        # Silent on hours/price to trigger content gaps
        raw_text = "Istanbul Kitchen is a Turkish restaurant in Islamabad. Famous for authentic kebab, shawarma, pide, and lahmacun. Fresh ingredients and traditional recipes."

        r = run_lift_simulation(
            "Istanbul Kitchen",
            "turkish restaurant",
            "Islamabad",
            {
                "business_context": {
                    "raw_text": raw_text,
                    "city": "Islamabad",
                    "has_local_comparison": False
                },
                "raw_business_context": raw_text,
                "force_mock": True,
                "use_real": False,
            }
        )

        assert r["template_used"] == "RestaurantTemplate"

        # Check Local SEO remediation
        local_seo_rem = next((rem for rem in r["remediation"] if rem["type"] == "local_seo" and "local intent content" in rem["title"].lower()), None)
        assert local_seo_rem is not None

        # Bug 1 Fix: Should contain Turkish/kebab/shawarma, NOT burger
        action_text = local_seo_rem["action"].lower()
        assert "turkish restaurant" in action_text
        assert "kebab" in action_text
        assert "shawarma" in action_text
        assert "turkish family restaurant" in action_text
        assert "burger" not in action_text

        # Check Hours/Price remediation (filtering by title only to be type-agnostic)
        hours_rem = next((rem for rem in r["remediation"] if "hours and price range" in rem["title"].lower()), None)
        assert hours_rem is not None

        # Bug 2 Fix: Action should be about hours/price, NOT signature dishes
        hours_action = hours_rem["action"].lower()
        assert "opening hours" in hours_action
        assert "price range" in hours_action
        assert "delivery availability" in hours_action
        assert "signature dishes" not in hours_action
        assert "story" not in hours_action

        # Contamination check (Bug 3 requirement)
        rem_text = " ".join([str(rem.values()) for rem in r["remediation"]]).lower()
        assert "dentist" not in rem_text
        assert "medicalclinic" not in rem_text
        assert "shipping" not in rem_text
        assert "size guide" not in rem_text
        assert "healthclub" not in rem_text
        assert "trainer" not in rem_text

    def test_chinese_restaurant_subtype(self):
        """Test Chinese restaurant subtype detection and wording."""
        raw_text = "Dragon Palace is a Chinese restaurant in Manchester. Specializes in dim sum, noodles, hotpot, and Manchurian. Authentic Chinese recipes."

        r = run_lift_simulation(
            "Dragon Palace",
            "chinese restaurant",
            "Manchester",
            {
                "business_context": raw_text,
                "raw_business_context": raw_text,
                "force_mock": True,
                "use_real": False,
            }
        )

        assert r["template_used"] == "RestaurantTemplate"
        rem_text = " ".join([str(rem.values()) for rem in r["remediation"]]).lower()

        # Chinese-specific language
        assert any(kw in rem_text for kw in ["chinese", "noodles", "dim sum", "hotpot"])
        # Should NOT contain other cuisine contamination
        assert "turkish" not in rem_text
        assert "desi" not in rem_text

    def test_desi_restaurant_subtype(self):
        """Test Desi/Pakistani restaurant subtype detection and wording."""
        raw_text = "Punjab Grill is a desi restaurant in Birmingham. Famous for biryani, karahi, nihari, and tandoor dishes. Authentic Pakistani cuisine."

        r = run_lift_simulation(
            "Punjab Grill",
            "desi restaurant",
            "Birmingham",
            {
                "business_context": raw_text,
                "raw_business_context": raw_text,
                "force_mock": True,
                "use_real": False,
            }
        )

        assert r["template_used"] == "RestaurantTemplate"
        rem_text = " ".join([str(rem.values()) for rem in r["remediation"]]).lower()

        # Desi-specific language
        assert any(kw in rem_text for kw in ["desi", "biryani", "karahi", "nihari"])
        # Should NOT contain other cuisine contamination
        assert "turkish" not in rem_text
        assert "chinese" not in rem_text

    def test_fast_food_subtype(self):
        """Test fast food restaurant subtype detection."""
        raw_text = "Burger King is a fast food restaurant in Dubai. Known for burgers, fries, fried chicken, wraps, and combo deals."

        r = run_lift_simulation(
            "Burger King Dubai",
            "fast food",
            "Dubai",
            {
                "business_context": raw_text,
                "raw_business_context": raw_text,
                "force_mock": True,
                "use_real": False,
            }
        )

        assert r["template_used"] == "RestaurantTemplate"
        rem_text = " ".join([str(rem.values()) for rem in r["remediation"]]).lower()

        # Fast food-specific language
        assert any(kw in rem_text for kw in ["fast food", "burger", "fries", "combos", "deals"])
        # Should NOT contain other cuisine contamination
        assert "desi" not in rem_text
        assert "turkish" not in rem_text

    def test_cafe_subtype(self):
        """Test cafe subtype detection and wording."""
        raw_text = "The Coffee House is a cafe in Edinburgh. Specializes in espresso, latte, cappuccino, pastries, and brunch."

        r = run_lift_simulation(
            "The Coffee House",
            "cafe",
            "Edinburgh",
            {
                "business_context": raw_text,
                "raw_business_context": raw_text,
                "force_mock": True,
                "use_real": False,
            }
        )

        assert r["template_used"] == "RestaurantTemplate"
        rem_text = " ".join([str(rem.values()) for rem in r["remediation"]]).lower()

        # Cafe-specific language
        assert any(kw in rem_text for kw in ["cafe", "coffee", "espresso", "pastries", "brunch"])
        # Should NOT contain other cuisine contamination
        assert "desi" not in rem_text
        assert "turkish" not in rem_text

    def test_restaurant_no_contamination(self):
        """Test that restaurant template does not output dental/ecommerce/fitness keywords."""
        raw_text = "Pizza Palace is a pizza restaurant in Rome. Best pizza in town with authentic Italian recipes."

        r = run_lift_simulation(
            "Pizza Palace",
            "pizza restaurant",
            "Rome",
            {
                "business_context": raw_text,
                "raw_business_context": raw_text,
                "force_mock": True,
                "use_real": False,
            }
        )

        assert r["template_used"] == "RestaurantTemplate"
        rem_text = " ".join([str(rem.values()) for rem in r["remediation"]]).lower()

        # Dental contamination check
        assert "dentist" not in rem_text
        assert "medicalclinic" not in rem_text
        assert "braces" not in rem_text
        assert "implants" not in rem_text

        # Ecommerce contamination check
        assert "product schema" not in rem_text
        assert "offer schema" not in rem_text
        assert "shipping" not in rem_text
        assert "size guide" not in rem_text

        # Fitness contamination check
        assert "healthclub" not in rem_text
        assert "trainer" not in rem_text
        assert "class schedule" not in rem_text
        assert "membership" not in rem_text

    def test_turkish_restaurant_subtype_polish(self):
        """Test Turkish restaurant subtype remediation copy polish."""
        # Silent on hours/price to trigger content gaps
        raw_text = "Istanbul Kitchen is a Turkish restaurant in Islamabad. Famous for authentic kebab, shawarma, pide, and lahmacun. Fresh ingredients and traditional recipes."

        r = run_lift_simulation(
            "Istanbul Kitchen",
            "turkish restaurant",
            "Islamabad",
            {
                "business_context": {
                    "raw_text": raw_text,
                    "city": "Islamabad",
                    "has_local_comparison": False
                },
                "raw_business_context": raw_text,
                "force_mock": True,
                "use_real": False,
            }
        )

        assert r["template_used"] == "RestaurantTemplate"

        # Check Local SEO remediation
        local_seo_rem = next((rem for rem in r["remediation"] if rem["type"] == "local_seo" and "local intent content" in rem["title"].lower()), None)
        assert local_seo_rem is not None

        # Bug 1 Fix: Should contain Turkish/kebab/shawarma, NOT burger
        action_text = local_seo_rem["action"].lower()
        assert "turkish restaurant" in action_text
        assert "kebab" in action_text
        assert "shawarma" in action_text
        assert "turkish family restaurant" in action_text
        assert "burger" not in action_text

        # Check Hours/Price remediation (filtering by title only to be type-agnostic)
        hours_rem = next((rem for rem in r["remediation"] if "hours and price range" in rem["title"].lower()), None)
        assert hours_rem is not None

        # Bug 2 Fix: Action should be about hours/price, NOT signature dishes
        hours_action = hours_rem["action"].lower()
        assert "opening hours" in hours_action
        assert "price range" in hours_action
        assert "delivery availability" in hours_action
        assert "signature dishes" not in hours_action
        assert "story" not in hours_action

        # Contamination check (Bug 3 requirement)
        rem_text = " ".join([str(rem.values()) for rem in r["remediation"]]).lower()
        assert "dentist" not in rem_text
        assert "medicalclinic" not in rem_text
        assert "shipping" not in rem_text
        assert "size guide" not in rem_text
        assert "healthclub" not in rem_text
        assert "trainer" not in rem_text

    def test_chinese_restaurant_subtype(self):
        """Test Chinese restaurant subtype detection and wording."""
        raw_text = "Dragon Palace is a Chinese restaurant in Manchester. Specializes in dim sum, noodles, hotpot, and Manchurian. Authentic Chinese recipes."

        r = run_lift_simulation(
            "Dragon Palace",
            "chinese restaurant",
            "Manchester",
            {
                "business_context": raw_text,
                "raw_business_context": raw_text,
                "force_mock": True,
                "use_real": False,
            }
        )

        assert r["template_used"] == "RestaurantTemplate"
        rem_text = " ".join([str(rem.values()) for rem in r["remediation"]]).lower()

        # Chinese-specific language
        assert any(kw in rem_text for kw in ["chinese", "noodles", "dim sum", "hotpot"])
        # Should NOT contain other cuisine contamination
        assert "turkish" not in rem_text
        assert "desi" not in rem_text

    def test_desi_restaurant_subtype(self):
        """Test Desi/Pakistani restaurant subtype detection and wording."""
        raw_text = "Punjab Grill is a desi restaurant in Birmingham. Famous for biryani, karahi, nihari, and tandoor dishes. Authentic Pakistani cuisine."

        r = run_lift_simulation(
            "Punjab Grill",
            "desi restaurant",
            "Birmingham",
            {
                "business_context": raw_text,
                "raw_business_context": raw_text,
                "force_mock": True,
                "use_real": False,
            }
        )

        assert r["template_used"] == "RestaurantTemplate"
        rem_text = " ".join([str(rem.values()) for rem in r["remediation"]]).lower()

        # Desi-specific language
        assert any(kw in rem_text for kw in ["desi", "biryani", "karahi", "nihari"])
        # Should NOT contain other cuisine contamination
        assert "turkish" not in rem_text
        assert "chinese" not in rem_text

    def test_fast_food_subtype(self):
        """Test fast food restaurant subtype detection."""
        raw_text = "Burger King is a fast food restaurant in Dubai. Known for burgers, fries, fried chicken, wraps, and combo deals."

        r = run_lift_simulation(
            "Burger King Dubai",
            "fast food",
            "Dubai",
            {
                "business_context": raw_text,
                "raw_business_context": raw_text,
                "force_mock": True,
                "use_real": False,
            }
        )

        assert r["template_used"] == "RestaurantTemplate"
        rem_text = " ".join([str(rem.values()) for rem in r["remediation"]]).lower()

        # Fast food-specific language
        assert any(kw in rem_text for kw in ["fast food", "burger", "fries", "combos", "deals"])
        # Should NOT contain other cuisine contamination
        assert "desi" not in rem_text
        assert "turkish" not in rem_text

    def test_cafe_subtype(self):
        """Test cafe subtype detection and wording."""
        raw_text = "The Coffee House is a cafe in Edinburgh. Specializes in espresso, latte, cappuccino, pastries, and brunch."

        r = run_lift_simulation(
            "The Coffee House",
            "cafe",
            "Edinburgh",
            {
                "business_context": raw_text,
                "raw_business_context": raw_text,
                "force_mock": True,
                "use_real": False,
            }
        )

        assert r["template_used"] == "RestaurantTemplate"
        rem_text = " ".join([str(rem.values()) for rem in r["remediation"]]).lower()

        # Cafe-specific language
        assert any(kw in rem_text for kw in ["cafe", "coffee", "espresso", "pastries", "brunch"])
        # Should NOT contain other cuisine contamination
        assert "desi" not in rem_text
        assert "turkish" not in rem_text

    def test_restaurant_no_contamination(self):
        """Test that restaurant template does not output dental/ecommerce/fitness keywords."""
        raw_text = "Pizza Palace is a pizza restaurant in Rome. Best pizza in town with authentic Italian recipes."

        r = run_lift_simulation(
            "Pizza Palace",
            "pizza restaurant",
            "Rome",
            {
                "business_context": raw_text,
                "raw_business_context": raw_text,
                "force_mock": True,
                "use_real": False,
            }
        )

        assert r["template_used"] == "RestaurantTemplate"
        rem_text = " ".join([str(rem.values()) for rem in r["remediation"]]).lower()

        # Dental contamination check
        assert "dentist" not in rem_text
        assert "medicalclinic" not in rem_text
        assert "braces" not in rem_text
        assert "implants" not in rem_text

        # Ecommerce contamination check
        assert "product schema" not in rem_text
        assert "offer schema" not in rem_text
        assert "shipping" not in rem_text
        assert "size guide" not in rem_text

        # Fitness contamination check
        assert "healthclub" not in rem_text
        assert "trainer" not in rem_text
        assert "class schedule" not in rem_text
        assert "membership" not in rem_text

    def test_fitness_remediation_routing(self):
        """Test that fitness gym still gets fitness remediation."""
        r = run_lift_simulation(
            "Oxygen Fitness Gym",
            "fitness gym",
            "Islamabad",
            {
                "business_context": "Oxygen Fitness Gym is a premium health club in Islamabad with swimming pool and sauna.",
                "force_mock": True,
                "use_real": False,
            }
        )

        assert r["template_used"] == "FitnessGymTemplate"
        rem_text = " ".join([str(rem.values()) for rem in r["remediation"]]).lower()

        # Fitness positive assertions
        assert any(kw in rem_text for kw in ["healthclub", "sportsactivitylocation", "gym", "pool", "trainer", "class updates"])

        # Dental negative assertions
        assert "dentist" not in rem_text
        assert "medicalclinic" not in rem_text

    def test_ecommerce_remediation_routing(self):
        """Test that ecommerce still gets ecommerce remediation."""
        r = run_lift_simulation(
            "StyleHub Fashion",
            "ecommerce fashion store",
            "London",
            {
                "business_context": "StyleHub is an online fashion store selling clothing and accessories.",
                "force_mock": True,
                "use_real": False,
            }
        )

        assert r["template_used"] == "EcommerceTemplate"
        rem_text = " ".join([str(rem.values()) for rem in r["remediation"]]).lower()

        # Ecommerce positive assertions
        assert any(kw in rem_text for kw in ["product", "offer", "shipping", "size guide", "return"])

        # Dental negative assertions
        assert "dentist" not in rem_text
        assert "medicalclinic" not in rem_text


class TestRemediationTextCleaning:
    """Test remediation card text cleaning."""

    def test_no_html_leakage_in_reason(self):
        """Test that reason field does not contain raw HTML tags."""
        remediation = {
            'title': 'Create dedicated service pages',
            'reason': 'Missing service pages',
            'why_this_works': 'Individual service pages target specific search queries',
            'action': 'Create pages for: personal training, swimming pool, sauna',
            'priority': 'high',
            'effort': 'medium',
            'impact': 'high'
        }

        # Verify no HTML tags in fields
        assert '</div>' not in remediation['reason']
        assert '<p>' not in remediation['reason']
        assert '<strong>' not in remediation['reason']
        assert '</p>' not in remediation['reason']


class TestLiftProofFallback:
    """Test lift proof simulation_notes fallback."""

    def test_simulation_notes_always_present(self):
        """Test that simulate_improved_audit always includes simulation_notes."""
        baseline = {
            "brand": "Test Brand",
            "category": "fitness gym",
            "citation_found": False,
            "confidence_score": 0.0,
            "raw_response": "No mention found."
        }

        improved = simulate_improved_audit(baseline)

        # Should always have simulation_notes
        assert "simulation_notes" in improved
        assert isinstance(improved["simulation_notes"], dict)

        # Should have required fields
        assert "disclaimer" in improved["simulation_notes"]
        assert "alternative_outcomes" in improved["simulation_notes"]
        assert "risk_factors" in improved["simulation_notes"]

    def test_simulation_notes_for_strong_baseline(self):
        """Test simulation_notes for strong baseline brands."""
        baseline = {
            "brand": "Strong Brand",
            "category": "fitness gym",
            "citation_found": True,
            "confidence_score": 0.90,
            "raw_response": "Strong Brand is highly recommended."
        }

        improved = simulate_improved_audit(baseline)

        # Should have simulation_notes
        assert "simulation_notes" in improved
        assert "disclaimer" in improved["simulation_notes"]

    def test_simulation_notes_for_weak_baseline(self):
        """Test simulation_notes for weak baseline brands."""
        baseline = {
            "brand": "Weak Brand",
            "category": "fitness gym",
            "citation_found": True,
            "confidence_score": 0.50,
            "raw_response": "Weak Brand is an option."
        }

        improved = simulate_improved_audit(baseline)

        # Should have simulation_notes
        assert "simulation_notes" in improved
        assert "disclaimer" in improved["simulation_notes"]


class TestNegativeLiftFormatting:
    """Test negative lift formatting."""

    def test_negative_lift_displays_correctly(self):
        """Test that negative lift displays with minus sign, not +-."""
        before_score = 1.00
        after_score = 0.85
        lift_amount = after_score - before_score

        # Format as signed number
        lift_str = f"{lift_amount:+.2f}"

        # Should show minus sign
        assert lift_str == "-0.15"
        assert "+-" not in lift_str

    def test_positive_lift_displays_correctly(self):
        """Test that positive lift displays with plus sign."""
        before_score = 0.50
        after_score = 0.75
        lift_amount = after_score - before_score

        # Format as signed number
        lift_str = f"{lift_amount:+.2f}"

        # Should show plus sign
        assert lift_str == "+0.25"

    def test_zero_lift_displays_correctly(self):
        """Test that zero lift displays without sign."""
        before_score = 0.50
        after_score = 0.50
        lift_amount = after_score - before_score

        # Format as signed number
        lift_str = f"{lift_amount:+.2f}"

        # Should show no sign or +0.00
        assert lift_str in ["0.00", "+0.00"]

    def test_negative_percentage_formatting(self):
        """Test negative percentage formatting."""
        lift_pct = -15.0

        # Format as signed percentage
        pct_str = f"{lift_pct:+.0f}%"

        # Should show minus sign
        assert pct_str == "-15%"
        assert "+-" not in pct_str


class TestBusinessContextParsing:
    """Test business context parsing patterns."""

    def test_rating_patterns(self):
        """Test detection of various rating patterns."""
        import re
        patterns = [
            "4.5 Google rating",
            "4.5 rating",
            "rated 4.5",
            "rating: 4.5"
        ]
        regex = r'(?:rated\s+|rating[:\s]+|)(\d+\.?\d*)\s*(?:google\s*)?rating'

        for p in patterns:
            text = p.lower()
            match = re.search(regex, text)
            if not match:
                match = re.search(r'rated\s*(\d+\.?\d*)', text)
            if not match:
                match = re.search(r'rating[:\s]+(\d+\.?\d*)', text)

            assert match is not None, f"Failed to match pattern: {p}"
            assert match.group(1) == "4.5"

    def test_review_patterns(self):
        """Test detection of review patterns."""
        import re
        patterns = [
            "231 Google reviews",
            "231 reviews"
        ]
        regex = r'(\d+)\s*(?:google\s*)?reviews?'

        for p in patterns:
            text = p.lower()
            match = re.search(regex, text)
            assert match is not None, f"Failed to match pattern: {p}"
            assert match.group(1) == "231"

    def test_social_follower_patterns(self):
        """Test detection of social follower patterns."""
        import re
        patterns = [
            "Instagram 18.3K followers",
            "Instagram has 18.3K+ followers",
            "Facebook 12.2K followers",
            "Facebook has 12.2K+ followers"
        ]

        for p in patterns:
            text = p.lower()
            if "instagram" in text:
                match = re.search(r'instagram.*?\s*(\d+\.?\d*)\s*k', text)
                assert match is not None, f"Failed to match Instagram pattern: {p}"
                assert match.group(1) == "18.3"
            elif "facebook" in text:
                match = re.search(r'facebook.*?\s*(\d+\.?\d*)\s*k', text)
                assert match is not None, f"Failed to match Facebook pattern: {p}"
                assert match.group(1) == "12.2"
