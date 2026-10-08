"""Real scheduled API orchestration; processing stages execute atomically in backend."""

import json
import os
from datetime import datetime, timedelta
from urllib.request import Request, urlopen

from airflow import DAG
from airflow.operators.python import PythonOperator


def call(path, body=None):
    request = Request(
        os.getenv("DATAPULSE_API_URL", "http://api:8000").rstrip("/") + "/api" + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Content-Type": "application/json",
            "X-API-Key": os.environ["ADMIN_API_KEY"],
        },
    )
    with urlopen(request, timeout=300) as response:
        return json.load(response)


def ready():
    assert call("/health")["status"] == "ok"


def execute():
    return call("/pipelines/commerce/run", {"volume": 10000, "seed": 42})


def verify():
    result = call("/kpis")
    if result["processed_records"] == 0:
        raise RuntimeError("No persisted records after pipeline")
    return result


with DAG(
    "datapulse_commerce",
    start_date=datetime(2026, 1, 1),
    schedule="0 12 * * *",
    catchup=False,
    max_active_runs=1,
    default_args={
        "retries": 2,
        "retry_delay": timedelta(seconds=30),
        "execution_timeout": timedelta(minutes=10),
    },
    tags=["datapulse"],
) as dag:
    health = PythonOperator(task_id="check_integrity", python_callable=ready)
    processing = PythonOperator(
        task_id="ingest_validate_silver_gold_persist", python_callable=execute
    )
    metrics = PythonOperator(task_id="verify_persisted_kpis", python_callable=verify)
    health >> processing >> metrics
