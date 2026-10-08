from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.main import app

client = TestClient(app)


def test_health_checks_database() -> None:
    engine = MagicMock()
    with patch("app.api.health.get_engine", return_value=engine):
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up"}
    engine.connect.return_value.__enter__.return_value.execute.assert_called_once()


def test_unavailable_database_returns_503() -> None:
    engine = MagicMock()
    engine.connect.side_effect = OperationalError("SELECT 1", {}, Exception("offline"))
    with patch("app.api.health.get_engine", return_value=engine):
        response = client.get("/api/health")
    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "down"}
    assert "offline" not in response.text


def test_openapi_documents_health() -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "503" in response.json()["paths"]["/api/health"]["get"]["responses"]
