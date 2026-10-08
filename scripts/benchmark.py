"""Measured local workloads, not production throughput claims."""

import json
import time
from datetime import UTC, datetime
from pathlib import Path

from pipelines.ingestion.generator import generate
from pipelines.runner import run

results = []
for volume in (1000, 10000, 100000):
    source = Path("data/generated") / f"benchmark-{volume}"
    generate(source, volume)
    started = time.monotonic()
    result = run(source, datetime(2026, 10, 7, 12, tzinfo=UTC))
    assert result["valid"] == int(volume * 0.9)
    results.append(
        {"volume": volume, "seconds": round(time.monotonic() - started, 3), **result}
    )
    print(json.dumps(results[-1]), flush=True)
Path("docs/benchmarks.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
