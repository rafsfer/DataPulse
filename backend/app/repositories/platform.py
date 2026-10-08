from typing import Any

from sqlalchemy import text

from app.db.session import get_engine


def query(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    with get_engine().connect() as connection:
        return [dict(row) for row in connection.execute(text(sql), params or {}).mappings()]
