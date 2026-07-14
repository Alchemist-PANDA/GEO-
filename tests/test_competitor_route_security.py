import asyncio
import uuid

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from geo_audit_agent.api.routes.competitors import CompetitorScanRequest, scan_competitors
from geo_audit_agent.db.models import Brand


class _Session:
    def __init__(self, brand):
        self.brand = brand

    def get(self, model, object_id):
        return self.brand


def test_competitor_scan_hides_cross_tenant_brand():
    brand = Brand(id=uuid.uuid4(), user_id=uuid.uuid4(), name="Acme", category="coffee", city="Islamabad")
    request = CompetitorScanRequest(brand_id=brand.id, competitors=["Rival"])
    with pytest.raises(HTTPException) as error:
        asyncio.run(scan_competitors(request, user_id=str(uuid.uuid4()), session=_Session(brand)))
    assert error.value.status_code == 404


def test_competitor_scan_does_not_accept_caller_supplied_observations():
    brand = Brand(id=uuid.uuid4(), user_id=uuid.uuid4(), name="Acme", category="coffee", city="Islamabad")
    with pytest.raises(ValidationError):
        CompetitorScanRequest(
            brand_id=brand.id,
            competitors=["Rival"],
            observations=[{"entity": "Acme", "mentioned": True}],
        )
