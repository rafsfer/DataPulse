"""Exercise actual HTTP -> API -> PostgreSQL, including failure and safe retry."""

import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app.core.config import get_settings

BASE = "http://localhost:5173/api"


def call(path, body=None, authenticated=False, expected=200):
    headers = {"Content-Type": "application/json"}
    if authenticated:
        headers["X-API-Key"] = get_settings().admin_api_key
    request = Request(
        BASE + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers=headers,
    )
    try:
        with urlopen(request, timeout=300) as response:
            assert response.status == expected
            return json.load(response)
    except HTTPError as error:
        if error.code != expected:
            raise
        return json.load(error)


def smoke():
    assert call("/health")["database"] == "up"
    call("/pipelines/commerce/run", {"volume": 1000}, expected=401)
    first = call("/pipelines/commerce/run", {"volume": 1000}, True)
    assert first["valid"] == 900
    second = call("/pipelines/commerce/run", {"volume": 1000}, True)
    assert second["batch_id"] == first["batch_id"]
    call(
        "/pipelines/commerce/run", {"volume": 1000, "fail_at": "validation"}, True, 500
    )
    incident = next(
        row
        for row in call("/incidents")
        if row["status"] == "open" and row["cause"].startswith("Intentional")
    )
    assert call(f"/incidents/{incident['id']}/retry", {}, True)["status"] == "success"
    call(f"/incidents/{incident['id']}/retry", {}, True, 409)
    assert call("/quality/issues")
    assert call("/quality/quarantine", authenticated=True)
    assert call("/analytics")
    assert call("/kpis")["data_quality_score"] == 90
    print(
        "HTTP smoke passed: real pipeline, idempotency, failure, retry, auth and KPIs"
    )


if __name__ == "__main__":
    smoke()
