# ADR 001: Modular application and incremental delivery

Status: accepted.

Use one Python backend and shared pipeline modules, with PostgreSQL for serving
and execution metadata. Keep data layers separate from database serving tables.
This is practical for a single student to maintain.

Use PostgreSQL in integration tests rather than claiming SQLite proves compatibility.
Python 3.12 is required in package metadata and containers. Direct dependencies
are pinned; a complete transitive lockfile remains pending.

Add Airflow, PySpark and Scala after the local data MVP is validated.
Do not create empty directories or label missing modules as complete.
