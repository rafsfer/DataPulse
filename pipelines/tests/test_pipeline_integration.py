import os
from datetime import UTC, datetime

import pytest
from sqlalchemy import text

from app.db.session import get_engine
from pipelines.ingestion.generator import generate
from pipelines.runner import PipelineBusy, run


@pytest.mark.integration
def test_real_execution_idempotency_failure_and_lock(tmp_path):
    if not os.getenv("TEST_DATABASE_URL"):
        pytest.skip("PostgreSQL integration disabled")
    generate(tmp_path / "source", 1000, seed=77)
    now = datetime(2026, 10, 7, 12, tzinfo=UTC)
    first = run(tmp_path / "source", now)
    second = run(tmp_path / "source", now)
    assert first["valid"] == second["valid"] == 900
    with get_engine().connect() as connection:
        assert (
            connection.execute(
                text("SELECT count(*) FROM sales WHERE batch_id=:batch"),
                {"batch": first["batch_id"]},
            ).scalar_one()
            == 900
        )
        assert (
            connection.execute(
                text("SELECT count(*) FROM quarantine WHERE run_id=:run"),
                {"run": first["id"]},
            ).scalar_one()
            == 100
        )
        assert (
            connection.execute(
                text("SELECT sum(orders) FROM regional_sales WHERE batch_id=:batch"),
                {"batch": first["batch_id"]},
            ).scalar_one()
            == 900
        )
        assert (
            connection.execute(
                text("SELECT validation_as_of FROM pipeline_runs WHERE id=:run"),
                {"run": second["id"]},
            ).scalar_one()
            == now
        )
        connection.execute(text("SELECT pg_advisory_lock(734922)"))
        try:
            with pytest.raises(PipelineBusy):
                run(tmp_path / "source", now)
        finally:
            connection.execute(text("SELECT pg_advisory_unlock(734922)"))
            connection.commit()
    with pytest.raises(RuntimeError, match="Intentional"):
        run(tmp_path / "source", now, "validation")
    with get_engine().connect() as connection:
        assert (
            connection.execute(
                text(
                    "SELECT count(*) FROM incidents i JOIN pipeline_runs r "
                    "ON i.run_id=r.id WHERE r.source=:source AND r.status='failed'"
                ),
                {"source": str((tmp_path / "source").resolve())},
            ).scalar_one()
            == 1
        )
