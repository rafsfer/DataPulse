from typing import Any

from app.repositories.platform import query


def kpis() -> dict[str, Any]:
    execution = query(
        "SELECT count(*) AS executions, count(*) FILTER(WHERE status='success') AS successes, "
        "avg(duration_seconds) FILTER(WHERE status<>'running') AS average_duration_seconds, "
        "count(*) FILTER(WHERE status='success' AND duration_seconds<=sla_seconds) AS within_sla "
        "FROM pipeline_runs"
    )[0]
    latest = query(
        "SELECT total,valid,duplicates FROM pipeline_runs WHERE status='success' "
        "ORDER BY finished_at DESC LIMIT 1"
    )
    row = latest[0] if latest else {"total": 0, "valid": 0, "duplicates": 0}
    total = row["total"]
    attempts = execution["executions"]
    return {
        **execution,
        "processed_records": total,
        "valid_percent": 100 * row["valid"] / total if total else None,
        "data_quality_score": 100 * row["valid"] / total if total else None,
        "duplicate_percent": 100 * row["duplicates"] / total if total else None,
        "pipeline_success_percent": 100 * execution["successes"] / attempts if attempts else None,
        "sla_percent": 100 * execution["within_sla"] / attempts if attempts else None,
        "incidents_by_severity": query(
            "SELECT severity,count(*) AS count FROM incidents "
            "WHERE status<>'resolved' GROUP BY severity"
        ),
        "freshness": query(
            "SELECT name,updated_at,EXTRACT(EPOCH FROM now()-updated_at) "
            "AS age_seconds FROM dataset_catalog ORDER BY name"
        ),
    }
