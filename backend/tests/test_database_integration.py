import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.db.session import get_engine
from app.main import app


@pytest.mark.integration
def test_postgres_and_api() -> None:
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL for PostgreSQL integration")
    if url == "auto":
        url = get_settings().database_url
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url
    get_settings.cache_clear()
    get_engine.cache_clear()
    engine = create_engine(url, connect_args={"connect_timeout": 3})
    try:
        with engine.connect() as connection:
            assert connection.execute(text("SELECT 1")).scalar_one() == 1
            assert (
                connection.execute(
                    text("SELECT count(*) FROM schema_migrations WHERE version='001_foundation'")
                ).scalar_one()
                == 1
            )
        response = TestClient(app).get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "database": "up"}
    finally:
        engine.dispose()
        get_engine().dispose()
        get_engine.cache_clear()
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous
        get_settings.cache_clear()
