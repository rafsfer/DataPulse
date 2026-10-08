import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import get_engine
from app.repositories.platform import query
from app.schemas.commands import RunRequest
from app.services.metrics import kpis

router = APIRouter(prefix="/api", tags=["Platform"])
Limit = Annotated[int, Query(ge=1, le=500)]


def admin(x_api_key: Annotated[str | None, Header()] = None) -> None:
    configured = get_settings().admin_api_key
    if not configured or configured == "replace-with-a-random-local-secret":
        raise HTTPException(503, "Administrative authentication is not configured")
    if x_api_key is None or not secrets.compare_digest(x_api_key.encode(), configured.encode()):
        raise HTTPException(401, "Administrative API key required")


@router.get("/datasets")
def datasets() -> list[dict[str, Any]]:
    return query("SELECT * FROM dataset_catalog ORDER BY name")


@router.get("/pipelines")
def pipelines() -> list[dict[str, Any]]:
    return [
        {
            "id": "commerce",
            "description": "Atlas Commerce quality and analytics",
            "executions": query("SELECT * FROM pipeline_runs ORDER BY started_at DESC LIMIT 10"),
        }
    ]


@router.get("/pipelines/{pipeline_id}")
def pipeline(pipeline_id: str) -> dict[str, Any]:
    if pipeline_id != "commerce":
        raise HTTPException(404, "Pipeline not found")
    return pipelines()[0]


@router.get("/pipelines/{pipeline_id}/executions")
def executions(pipeline_id: str, limit: Limit = 100) -> list[dict[str, Any]]:
    pipeline(pipeline_id)
    return query(
        "SELECT * FROM pipeline_runs ORDER BY started_at DESC LIMIT :limit", {"limit": limit}
    )


@router.post("/pipelines/{pipeline_id}/run", dependencies=[Depends(admin)])
def execute(pipeline_id: str, command: RunRequest) -> dict[str, Any]:
    from pipelines.ingestion.generator import generate
    from pipelines.runner import PipelineBusy, run

    pipeline(pipeline_id)
    source = (
        Path(get_settings().data_root)
        / "generated"
        / f"demo-{command.volume}-{command.seed}-{uuid4()}"
    )
    # Generation is reproducible and published before execution. Runs serialize in PostgreSQL.
    reference = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    generate(source, command.volume, command.seed, reference_time=reference)
    try:
        return dict(run(source, fail_at=command.fail_at))
    except PipelineBusy as error:
        raise HTTPException(409, str(error)) from error
    except Exception as error:
        raise HTTPException(500, "Pipeline failed; consult incident history") from error


@router.get("/quality/overview")
@router.get("/kpis")
def metrics() -> dict[str, Any]:
    return kpis()


@router.get("/quality/issues")
def issues(limit: Limit = 100) -> list[dict[str, Any]]:
    return query(
        "SELECT * FROM quality_issues WHERE affected>0 ORDER BY checked_at DESC LIMIT :limit",
        {"limit": limit},
    )


@router.get("/quality/quarantine", dependencies=[Depends(admin)])
def quarantine(limit: Limit = 100) -> list[dict[str, Any]]:
    return query(
        "SELECT * FROM quarantine ORDER BY run_id,row_number LIMIT :limit", {"limit": limit}
    )


@router.get("/incidents")
def incidents(limit: Limit = 100) -> list[dict[str, Any]]:
    return query(
        "SELECT i.*,r.pipeline,r.source,r.batch_id FROM incidents i JOIN pipeline_runs r "
        "ON r.id=i.run_id ORDER BY i.created_at DESC LIMIT :limit",
        {"limit": limit},
    )


@router.post("/incidents/{incident_id}/retry", dependencies=[Depends(admin)])
def retry(incident_id: UUID) -> dict[str, Any]:
    from pipelines.runner import run

    with get_engine().begin() as connection:
        incident = (
            connection.execute(
                text(
                    "SELECT i.status,r.source,r.validation_as_of FROM incidents i "
                    "JOIN pipeline_runs r ON r.id=i.run_id "
                    "WHERE i.id=:id FOR UPDATE OF i"
                ),
                {"id": str(incident_id)},
            )
            .mappings()
            .first()
        )
        if incident is None:
            raise HTTPException(404, "Incident not found")
        if incident["status"] != "open":
            raise HTTPException(409, "Incident is already being retried or resolved")
        connection.execute(
            text("UPDATE incidents SET status='retrying' WHERE id=:id"), {"id": str(incident_id)}
        )
        source = Path(incident["source"])
        as_of = incident["validation_as_of"]
    try:
        result = dict(run(source, as_of=as_of))
    except Exception as error:
        with get_engine().begin() as connection:
            connection.execute(
                text("UPDATE incidents SET status='open' WHERE id=:id"), {"id": str(incident_id)}
            )
        raise HTTPException(500, "Retry failed; incident remains open") from error
    with get_engine().begin() as connection:
        connection.execute(
            text(
                "UPDATE incidents SET status='resolved',resolved_at=now(),"
                "retry_run_id=:run WHERE id=:id"
            ),
            {"id": str(incident_id), "run": result["id"]},
        )
    return result


@router.get("/analytics")
def analytics() -> list[dict[str, Any]]:
    return query(
        "SELECT region,category,sum(orders) AS orders,sum(units) AS units,"
        "sum(revenue) AS revenue FROM regional_sales "
        "GROUP BY region,category ORDER BY region,category"
    )


@router.get("/demo/{dataset}")
def demo(
    dataset: str, volume: Annotated[int, Query(ge=100, le=10000)] = 1000
) -> list[dict[str, str]]:
    import csv
    import tempfile

    from pipelines.ingestion.generator import COLUMNS, generate

    if dataset not in COLUMNS:
        raise HTTPException(404, "Dataset not found")
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        reference = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        generate(root, volume, reference_time=reference)
        with (root / f"{dataset}.csv").open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
