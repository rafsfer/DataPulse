"""Deterministic commerce fixtures; never generate real personal information."""

import argparse
import csv
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

COLUMNS = {
    "customers": ["customer_id", "region"],
    "products": ["product_id", "category"],
    "orders": [
        "order_id",
        "customer_id",
        "product_id",
        "quantity",
        "amount",
        "ordered_at",
    ],
}


def generate(
    destination: Path,
    volume: int = 1000,
    seed: int = 42,
    reference_time: datetime | None = None,
) -> None:
    if volume < 1 or volume > 1000000:
        raise ValueError("Volume must be between 1 and 1000000")
    rng = random.Random(seed)
    destination.mkdir(parents=True, exist_ok=True)
    customers = [
        {
            "customer_id": f"C{i:05d}",
            "region": ["North", "South", "East", "West"][i % 4],
        }
        for i in range(max(10, volume // 10))
    ]
    products = [
        {"product_id": f"P{i:05d}", "category": ["Home", "Tech", "Books"][i % 3]}
        for i in range(30)
    ]
    anchor = reference_time or datetime(2026, 10, 7, 12, tzinfo=UTC)
    orders = []
    for i in range(volume):
        row = {
            "order_id": f"O{i:08d}",
            "customer_id": rng.choice(customers)["customer_id"],
            "product_id": rng.choice(products)["product_id"],
            "quantity": str(rng.randint(1, 5)),
            "amount": f"{rng.randint(100, 50000) / 100:.2f}",
            "ordered_at": (anchor - timedelta(hours=rng.randint(0, 24))).isoformat(),
        }
        case = i % 100
        if case == 1:
            row["customer_id"] = ""
        elif case == 2:
            row["amount"] = "-12.50"
        elif case == 3:
            row["ordered_at"] = "not-a-date"
        elif case == 4:
            row["customer_id"] = "C99999"
        elif case == 5:
            row["product_id"] = "P99999"
        elif case == 6:
            row["quantity"] = "0"
        elif case == 7:
            row["order_id"] = f"invalid-id-{i}"
        elif case == 8:
            row["ordered_at"] = (anchor - timedelta(days=10)).isoformat()
        elif case == 9:
            row["order_id"] = orders[-1]["order_id"]
        elif case == 10:
            row["amount"] = "NaN"
        orders.append(row)
    for name, rows in [
        ("customers", customers),
        ("products", products),
        ("orders", orders),
    ]:
        with (destination / f"{name}.csv").open(
            "w", newline="", encoding="utf-8"
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=COLUMNS[name])
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--volume", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("data/generated/demo"))
    args = parser.parse_args()
    generate(args.output, args.volume, args.seed)
