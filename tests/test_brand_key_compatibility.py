"""
Test brand/brand_name key compatibility to prevent KeyError in production.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from geo_audit_agent.agent import build_geo_audit_agent


def test_agent_accepts_brand_key():
    """Test that agent accepts 'brand' key."""
    agent = build_geo_audit_agent()

    result = agent.invoke({
        "brand": "Test Brand",
        "category": "test",
        "city": "Test City",
        "force_mock": True
    })

    assert "brand" in result
    assert "brand_name" in result
    assert result["brand"] == "Test Brand"
    assert result["brand_name"] == "Test Brand"


def test_agent_accepts_brand_name_key():
    """Test that agent accepts 'brand_name' key."""
    agent = build_geo_audit_agent()

    result = agent.invoke({
        "brand_name": "Test Brand",
        "category": "test",
        "city": "Test City",
        "force_mock": True
    })

    assert "brand" in result
    assert "brand_name" in result
    assert result["brand"] == "Test Brand"
    assert result["brand_name"] == "Test Brand"


def test_agent_accepts_both_keys():
    """Test that agent accepts both 'brand' and 'brand_name' keys."""
    agent = build_geo_audit_agent()

    result = agent.invoke({
        "brand": "Test Brand",
        "brand_name": "Test Brand",
        "category": "test",
        "city": "Test City",
        "force_mock": True
    })

    assert "brand" in result
    assert "brand_name" in result
    assert result["brand"] == "Test Brand"
    assert result["brand_name"] == "Test Brand"


def test_deployed_ui_call_exact_match():
    """Test exact call pattern from deployed UI."""
    agent = build_geo_audit_agent()

    # This is the exact call pattern from dashboard.py
    result = agent.invoke({
        "brand": "Capital Arena Fitness Club",
        "brand_name": "Capital Arena Fitness Club",
        "category": "fitness gym",
        "city": "Islamabad",
        "force_mock": False,
        "use_real": True
    })

    # Should not raise KeyError
    assert "brand" in result
    assert "brand_name" in result
    assert result["brand"] == "Capital Arena Fitness Club"
    assert result["brand_name"] == "Capital Arena Fitness Club"
    assert "mode" in result
    assert "citation_found" in result
    assert "confidence_score" in result


def test_missing_brand_raises_error():
    """Test that missing brand raises clear error."""
    agent = build_geo_audit_agent()

    with pytest.raises(ValueError, match="Brand name is required"):
        agent.invoke({
            "category": "test",
            "city": "Test City"
        })


def test_business_name_fallback():
    """Test that 'business_name' is accepted as fallback."""
    agent = build_geo_audit_agent()

    result = agent.invoke({
        "business_name": "Test Business",
        "category": "test",
        "city": "Test City",
        "force_mock": True
    })

    assert "brand" in result
    assert "brand_name" in result
    assert result["brand"] == "Test Business"
    assert result["brand_name"] == "Test Business"


def test_default_values_for_missing_fields():
    """Test that missing category/city get safe defaults."""
    agent = build_geo_audit_agent()

    result = agent.invoke({
        "brand": "Test Brand",
        "force_mock": True
    })

    # Should not crash, should use defaults
    assert "brand" in result
    assert result["brand"] == "Test Brand"
