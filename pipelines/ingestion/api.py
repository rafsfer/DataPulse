"""Fetch all three datasets from the demonstration API into a CSV source batch."""

import argparse
import csv
import json
from pathlib import Path
from urllib.request import urlopen

from pipelines.ingestion.generator import COLUMNS


def ingest(base_url: str, destination: Path, volume: int = 1000):
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "origin.json").write_text(
        json.dumps({"source": base_url}), encoding="utf-8"
    )
    for name, columns in COLUMNS.items():
        with urlopen(
            f"{base_url.rstrip('/')}/api/demo/{name}?volume={volume}", timeout=30
        ) as response:
            rows = json.load(response)
        with (destination / f"{name}.csv").open(
            "w", encoding="utf-8", newline=""
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--output", type=Path, default=Path("data/generated/api"))
    args = parser.parse_args()
    ingest(args.url, args.output)
