import os
from datetime import UTC, datetime
import csv

import pytest

from pipelines.ingestion.generator import generate
from pipelines.validation.rules import validate_orders


@pytest.mark.skipif(
    os.getenv("RUN_SPARK_TESTS") != "1", reason="Enable Spark container profile"
)
def test_real_spark_joins_and_aggregation(tmp_path):
    from pipelines.spark.commerce import transform

    generate(tmp_path, 1000)

    def read(name):
        with (tmp_path / f"{name}.csv").open() as handle:
            return list(csv.DictReader(handle))

    customers, products, orders = read("customers"), read("products"), read("orders")
    valid, _, _ = validate_orders(
        orders,
        {r["customer_id"] for r in customers},
        {r["product_id"] for r in products},
        datetime(2026, 10, 7, 12, tzinfo=UTC),
    )
    silver, gold = transform(valid, customers, products)
    assert len(silver) == 900
    assert int(gold["orders"].sum()) == 900
    assert gold["revenue"].sum() == silver["amount"].sum()
