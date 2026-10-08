"""Real CSV -> Parquet -> PostgreSQL execution with serialized publication."""

import argparse
import csv
import hashlib
import json
import os
import subprocess
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import get_engine
from pipelines.ingestion.generator import COLUMNS
from pipelines.transformations.commerce import transform
from pipelines.validation.rules import RULES, validate_orders


class PipelineBusy(Exception):
    pass


def run(source: Path, as_of: datetime | None = None, fail_at: str | None = None):
    as_of = as_of or datetime.now(UTC)
    engine = get_engine()
    execution_id = str(uuid.uuid4())
    started = time.monotonic()
    source = source.resolve()
    digest = hashlib.sha256()
    batch_id = digest.hexdigest()
    data_root = Path(get_settings().data_root)
    with engine.connect() as lock:
        if not lock.execute(text("SELECT pg_try_advisory_lock(734922)")).scalar():
            raise PipelineBusy("Commerce pipeline already running")
        lock.commit()
        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO pipeline_runs(id,batch_id,status,source,validation_as_of) "
                        "VALUES (:id,:batch,'running',:source,:as_of)"
                    ),
                    {
                        "id": execution_id,
                        "batch": batch_id,
                        "source": str(source),
                        "as_of": as_of,
                    },
                )
            try:
                for name in COLUMNS:
                    digest.update((source / f"{name}.csv").read_bytes())
                batch_id = digest.hexdigest()
                with engine.begin() as connection:
                    connection.execute(
                        text("UPDATE pipeline_runs SET batch_id=:batch WHERE id=:id"),
                        {"batch": batch_id, "id": execution_id},
                    )
                origin_path = source / "origin.json"
                origin = (
                    json.loads(origin_path.read_text(encoding="utf-8"))["source"]
                    if origin_path.exists()
                    else str(source)
                )
                datasets = {}
                for name, columns in COLUMNS.items():
                    with (source / f"{name}.csv").open(
                        encoding="utf-8", newline=""
                    ) as handle:
                        reader = csv.DictReader(handle)
                        if reader.fieldnames != columns:
                            raise ValueError(f"Unexpected {name} schema")
                        datasets[name] = list(reader)
                    folder = data_root / "bronze" / execution_id
                    folder.mkdir(parents=True, exist_ok=True)
                    frame = pd.DataFrame(datasets[name], columns=columns)
                    frame["_origin"] = origin
                    frame["_run_id"] = execution_id
                    frame["_source"] = str(source / f"{name}.csv")
                    frame["_ingested_at"] = datetime.now(UTC).isoformat()
                    frame.to_parquet(folder / f"{name}.parquet", index=False)
                if fail_at == "validation":
                    raise RuntimeError(
                        "Intentional validation failure for incident drill"
                    )
                customers, products = datasets["customers"], datasets["products"]
                for name, rows, key in [
                    ("customers", customers, "customer_id"),
                    ("products", products, "product_id"),
                ]:
                    keys = [row[key] for row in rows]
                    if len(keys) != len(set(keys)) or any(not value for value in keys):
                        raise ValueError(f"Invalid {name} dimension keys")
                valid, rejected, counts = validate_orders(
                    datasets["orders"],
                    {r["customer_id"] for r in customers},
                    {r["product_id"] for r in products},
                    as_of,
                )
                if os.getenv("PIPELINE_ENGINE") == "spark":
                    from pipelines.spark.commerce import transform as spark_transform

                    silver, gold = spark_transform(valid, customers, products)
                else:
                    silver, gold = transform(valid, customers, products)
                for layer, frame in [("silver", silver), ("gold", gold)]:
                    folder = data_root / layer / execution_id
                    folder.mkdir(parents=True, exist_ok=True)
                    frame.to_parquet(folder / "sales.parquet", index=False)
                if os.getenv("SCALA_JAR"):
                    subprocess.run(
                        [
                            "spark-submit",
                            "--driver-memory",
                            "512m",
                            "--master",
                            "local[2]",
                            "--class",
                            "SalesAggregation",
                            os.environ["SCALA_JAR"],
                            str(data_root / "silver" / execution_id / "sales.parquet"),
                            str(data_root / "gold" / execution_id / "scala_sales"),
                        ],
                        check=True,
                        timeout=180,
                    )
                    gold = pd.read_parquet(
                        data_root / "gold" / execution_id / "scala_sales"
                    )
                folder = data_root / "quarantine" / execution_id
                folder.mkdir(parents=True, exist_ok=True)
                (folder / "orders.json").write_text(
                    json.dumps(rejected), encoding="utf-8"
                )
                with engine.begin() as connection:
                    connection.execute(
                        text("DELETE FROM sales WHERE batch_id=:batch"),
                        {"batch": batch_id},
                    )
                    connection.execute(
                        text("DELETE FROM regional_sales WHERE batch_id=:batch"),
                        {"batch": batch_id},
                    )
                    aggregates = gold.to_dict(orient="records")
                    if aggregates:
                        connection.execute(
                            text(
                                "INSERT INTO regional_sales(batch_id,region,category,revenue,orders,units,run_id) "
                                "VALUES (:batch_id,:region,:category,:revenue,:orders,:units,:run_id)"
                            ),
                            [
                                {**r, "batch_id": batch_id, "run_id": execution_id}
                                for r in aggregates
                            ],
                        )
                    records = silver.to_dict(orient="records")
                    if records:
                        connection.execute(
                            text(
                                "INSERT INTO sales(batch_id,order_id,customer_id,product_id,region,category,"
                                "quantity,amount,ordered_at,run_id) VALUES (:batch_id,:order_id,:customer_id,"
                                ":product_id,:region,:category,:quantity,:amount,:ordered_at,:run_id)"
                            ),
                            [
                                {**r, "batch_id": batch_id, "run_id": execution_id}
                                for r in records
                            ],
                        )
                    connection.execute(
                        text(
                            "INSERT INTO quality_issues(run_id,dataset,rule_id,severity,affected,result) "
                            "VALUES (:run,'orders',:rule,:severity,:affected,:result)"
                        ),
                        [
                            {
                                "run": execution_id,
                                "rule": rule,
                                "severity": RULES[rule],
                                "affected": count,
                                "result": "failed" if count else "passed",
                            }
                            for rule, count in counts.items()
                        ],
                    )
                    if rejected:
                        connection.execute(
                            text(
                                "INSERT INTO quarantine(run_id,dataset,row_number,original,reasons) "
                                "VALUES (:run,'orders',:row_number,CAST(:original AS jsonb),CAST(:reasons AS jsonb))"
                            ),
                            [
                                {
                                    "run": execution_id,
                                    "row_number": r["row_number"],
                                    "original": json.dumps(r["original"]),
                                    "reasons": json.dumps(r["reasons"]),
                                }
                                for r in rejected
                            ],
                        )
                    connection.execute(
                        text(
                            "UPDATE pipeline_runs SET status='success',finished_at=now(),total=:total,"
                            "valid=:valid,duplicates=:duplicates,duration_seconds=:duration WHERE id=:id"
                        ),
                        {
                            "id": execution_id,
                            "total": len(datasets["orders"]),
                            "valid": len(valid),
                            "duplicates": counts["duplicate"],
                            "duration": time.monotonic() - started,
                        },
                    )
                    connection.execute(
                        text("UPDATE dataset_catalog SET updated_at=now()")
                    )
                return {
                    "id": execution_id,
                    "batch_id": batch_id,
                    "status": "success",
                    "total": len(datasets["orders"]),
                    "valid": len(valid),
                    "quarantined": len(rejected),
                }
            except Exception as error:
                with engine.begin() as connection:
                    connection.execute(
                        text(
                            "UPDATE pipeline_runs SET status='failed',finished_at=now(),error=:error,"
                            "duration_seconds=:duration WHERE id=:id"
                        ),
                        {
                            "id": execution_id,
                            "error": str(error),
                            "duration": time.monotonic() - started,
                        },
                    )
                    connection.execute(
                        text(
                            "INSERT INTO incidents(id,run_id,severity,cause) VALUES (:id,:run,'critical',:cause)"
                        ),
                        {
                            "id": str(uuid.uuid4()),
                            "run": execution_id,
                            "cause": str(error),
                        },
                    )
                raise
        finally:
            lock.execute(text("SELECT pg_advisory_unlock(734922)"))
            lock.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("data/generated/demo"))
    parser.add_argument("--as-of", default=None)
    parser.add_argument("--fail-at", choices=["validation"])
    args = parser.parse_args()
    print(
        json.dumps(
            run(
                args.source,
                datetime.fromisoformat(args.as_of) if args.as_of else None,
                args.fail_at,
            )
        )
    )
