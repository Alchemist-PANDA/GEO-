from unittest.mock import Mock, patch

import pytest

from geo_audit_agent.services.public_evidence import crawl_public_evidence, validate_public_url


def test_public_url_rejects_private_hosts():
    with patch("geo_audit_agent.services.public_evidence._public_host", return_value=False):
        with pytest.raises(ValueError, match="public host"):
            validate_public_url("http://localhost")


def test_public_crawl_extracts_schema_and_contact_signals():
    response = Mock(status_code=200, headers={"content-type": "text/html"})
    response.iter_content.return_value = [
        b'<html><head><title>Dental Art</title><meta name="description" content="Lahore dentist"></head>'
        b'<body><h1>Dental clinic Lahore</h1><a href="https://facebook.com/dentalart">Social</a>'
        b'<script type="application/ld+json">{"@type":"Dentist"}</script><p>Call us at +92 Lahore Pakistan</p></body></html>'
    ]
    with patch("geo_audit_agent.services.public_evidence._public_host", return_value=True), patch(
        "geo_audit_agent.services.public_evidence.requests.get", return_value=response
    ):
        result = crawl_public_evidence("https://dentalart.example/")
    assert result["title"] == "Dental Art"
    assert "Dentist" in result["schema_types"]
    assert result["contact_signals"]["phone"] is True
