"""Tests for the generate_json_ld tool."""
import json
import pytest
from geo_audit_agent.geo_remediation_tools import generate_json_ld


class TestGenerateJsonLd:
    """Test suite for JSON-LD generation."""

    def test_basic_local_business(self):
        info = {"name": "Test Burger", "description": "A great burger place"}
        result = generate_json_ld("Test Brand", info)
        data = json.loads(result)
        assert data["@context"] == "https://schema.org"
        assert data["@type"] == "LocalBusiness"
        assert data["name"] == "Test Burger"
        assert data["brand"]["name"] == "Test Brand"

    def test_product_with_price(self):
        info = {"name": "Test Product", "description": "A product", "price": "9.99", "currency": "EUR"}
        result = generate_json_ld("Brand", info)
        data = json.loads(result)
        assert "Product" in data["@type"]
        assert data["offers"]["price"] == "9.99"
        assert data["offers"]["priceCurrency"] == "EUR"

    def test_default_currency_is_usd(self):
        info = {"name": "Test", "description": "Test", "price": "5.00"}
        result = generate_json_ld("Brand", info)
        data = json.loads(result)
        assert data["offers"]["priceCurrency"] == "USD"

    def test_address_included(self):
        info = {"name": "Test", "description": "Test", "address": "123 Main St"}
        result = generate_json_ld("Brand", info)
        data = json.loads(result)
        assert data["address"]["streetAddress"] == "123 Main St"

    def test_output_is_valid_json(self):
        info = {"name": "Test", "description": "Test"}
        result = generate_json_ld("Brand", info)
        # Should not raise
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_empty_brand_raises(self):
        with pytest.raises(ValueError, match="non-empty string"):
            generate_json_ld("", {"name": "Test"})

    def test_invalid_product_info_raises(self):
        with pytest.raises(ValueError, match="dictionary"):
            generate_json_ld("Brand", "not a dict")

    def test_fallback_name_to_brand(self):
        """If product_info has no 'name', brand_name is used."""
        info = {"description": "Test"}
        result = generate_json_ld("FallbackBrand", info)
        data = json.loads(result)
        assert data["name"] == "FallbackBrand"
