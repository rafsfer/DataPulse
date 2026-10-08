"""Apply ordered SQL migrations transactionally without resetting database volumes."""

from pathlib import Path

from sqlalchemy import text

from app.db.session import get_engine


def migrate() -> None:
    root = Path(__file__).resolve().parents[1] / "database" / "migrations"
    with get_engine().begin() as connection:
        connection.execute(text("SELECT pg_advisory_xact_lock(734921)"))
        connection.execute(
            text(
                "CREATE TABLE IF NOT EXISTS schema_migrations "
                "(version VARCHAR(32) PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
            )
        )
        for path in sorted(root.glob("*.sql")):
            if connection.execute(
                text("SELECT 1 FROM schema_migrations WHERE version=:version"),
                {"version": path.stem},
            ).scalar():
                continue
            connection.exec_driver_sql(path.read_text(encoding="utf-8"))
            connection.execute(
                text(
                    "INSERT INTO schema_migrations(version) VALUES (:version) "
                    "ON CONFLICT DO NOTHING"
                ),
                {"version": path.stem},
            )
            print(f"Applied {path.stem}")
    print("Migrations up to date")


if __name__ == "__main__":
    migrate()
