import os

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.metrics import kpis


@pytest.mark.integration
def test_metrics_and_admin_authorization():
    if not os.getenv("TEST_DATABASE_URL"):
        pytest.skip("PostgreSQL integration disabled")
    client = TestClient(app)
    assert client.get("/api/datasets").status_code == 200
    assert client.get("/api/pipelines/missing").status_code == 404
    assert client.post("/api/pipelines/commerce/run", json={"volume": 1000}).status_code in (
        401,
        503,
    )
    assert client.post(
        "/api/pipelines/commerce/run", headers={"X-API-Key": "invalid"}, json={"volume": 1000}
    ).status_code in (401, 503)
    data = kpis()
    assert data["executions"] >= data["successes"]
    if data["processed_records"]:
        assert 0 <= data["data_quality_score"] <= 100
