from datetime import UTC, datetime
from pathlib import Path
import csv

from pipelines.ingestion.generator import generate
from pipelines.validation.rules import RULES, validate_orders


def test_deterministic_generator_and_all_rules(tmp_path: Path):
    generate(tmp_path / "a", 1000)
    generate(tmp_path / "b", 1000)
    assert (tmp_path / "a/orders.csv").read_bytes() == (
        tmp_path / "b/orders.csv"
    ).read_bytes()
    rows = list(csv.DictReader((tmp_path / "a/orders.csv").open()))
    customers = {
        r["customer_id"] for r in csv.DictReader((tmp_path / "a/customers.csv").open())
    }
    products = {
        r["product_id"] for r in csv.DictReader((tmp_path / "a/products.csv").open())
    }
    valid, quarantine, counts = validate_orders(
        rows, customers, products, datetime(2026, 10, 7, 12, tzinfo=UTC)
    )
    assert len(valid) + len(quarantine) == 1000
    assert len(valid) == 900
    assert counts["duplicate"] == 10
    assert all(counts[rule] > 0 for rule in RULES)
    assert quarantine[0]["original"] == rows[1]
