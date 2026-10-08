# DataPulse — Data Reliability & Intelligence Platform

Data reliability and commercial analytics for the fictional Atlas Commerce business.
The system processes real synthetic source files, preserves original records,
quarantines invalid orders and publishes validated analytical results to PostgreSQL.
The React dashboard reads the API; indicators are never generated in the browser.

![Real dashboard capture](docs/screenshots/overview.png)

## Delivery status

Core ingestion, quality validation, Parquet layers, PostgreSQL serving, administrative
API, incident retry and dashboard are implemented. Optional PySpark, Scala and Airflow
modules are implemented and have separate verification requirements. Check the
[executed delivery ledger](docs/delivery-status.md) for actual results and remaining
limitations; source availability does not mean its tests have passed.

## Business problem and solution

Duplicate orders, invalid money values, inconsistent identifiers, missing customer
and product references, and stale records distort commerce reporting. DataPulse
retains evidence of each validation rule, isolates rejected rows, and serves quality
and operational metrics alongside validated regional/category sales aggregates.

## Architecture and stack

CSV/demo API → Bronze → validation/quarantine → Silver → Gold → PostgreSQL →
FastAPI → React. See the [architecture diagram](docs/architecture/overview.md),
[decisions](docs/decisions/001-modular-architecture.md), and
[Portuguese explanation](docs/architecture/arquitetura-pt.md).

Python 3.12, FastAPI, Pydantic, SQLAlchemy, Pandas, Parquet/PyArrow, PostgreSQL 16.6;
React, TypeScript, Vite, Tailwind, Recharts and TanStack Query. Optional profiles:
PySpark 3.5.4, Java 17, Scala and Apache Airflow. Docker Compose and GitHub Actions
provide local execution and automated checks. No paid cloud account is required.

## Setup and startup

Requirements: Docker Desktop with working WSL 2/Linux containers on Windows, or
Docker Engine with Compose on Linux/macOS. Install Python 3.12 for local tools.
Node 22.12+ is required only when running frontend development outside Docker.

Windows:

```powershell
Copy-Item .env.example .env
# Configure PostgreSQL credentials and a random ADMIN_API_KEY in .env.
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e "./backend[dev]"
docker compose up -d postgres
python scripts/migrate.py
docker compose up --build -d api frontend
```

Linux/macOS: use `cp .env.example .env`, `python3.12 -m venv .venv` and
`source .venv/bin/activate`, then the same pip, migration and Compose commands.
If uv manages your interpreter: `uv venv --python 3.12 .venv`.
Preserve an existing .venv rather than recreating it on each run.

- Dashboard: http://localhost:5173
- API / OpenAPI: http://localhost:8000/docs
- Readiness: http://localhost:8000/api/health (real PostgreSQL query)

Compose constructs connection URLs safely from POSTGRES_* fields. Local Python
uses DATABASE_URL; URL-encode special characters in its password. Do not publish
.env. The example administrative key must be replaced. Enter your local key in the
Pipelines or Incidents page; it is kept only in browser memory.

For live backend source updates, use the development override:
`docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d api frontend`.
The override mounts application code read-only and is intended for local development.

## Run a real data pipeline

From the repository root with the environment activated:

```bash
python -m pipelines.ingestion.generator --volume 1000 --output data/generated/demo
python -m pipelines.runner --source data/generated/demo --as-of 2026-10-07T12:00:00+00:00
```

Repeat with 10000 or 100000. The CLI fixture uses a fixed historical reference date
for reproducibility. HTTP demonstrations use UTC midnight of the current day, so
identical requests within the day generate identical source batches.

API ingestion:

```bash
python -m pipelines.ingestion.api --url http://localhost:8000 --output data/generated/api
python -m pipelines.runner --source data/generated/api
```

Run the same batch twice: its content hash is unchanged, serving facts and Gold
aggregates are replaced transactionally, and execution history retains both attempts.
A PostgreSQL advisory lock rejects overlapping commerce runs.

## Requests and incident demonstration

```bash
curl http://localhost:8000/api/datasets
curl http://localhost:8000/api/kpis
curl http://localhost:8000/api/analytics
curl -X POST http://localhost:8000/api/pipelines/commerce/run \
  -H "Content-Type: application/json" -H "X-API-Key: YOUR_LOCAL_KEY" \
  -d '{"volume":1000,"seed":42}'
```

Select “Inject validation failure” on Pipelines to produce a real HTTP failure,
failed execution and incident. On Incidents, enter your key and retry the incident.
The retry reuses its source and validation reference. Resolved or already claimed
incidents reject a second retry. No failed operation is reported as success.

## Checks

Windows integration tests:

```powershell
$env:TEST_DATABASE_URL='auto'
python -m pytest -q -c backend/pyproject.toml backend/tests pipelines/tests
```

Linux/macOS: prefix the pytest command with `TEST_DATABASE_URL=auto`.
This selects the configured real PostgreSQL database. Prefer a dedicated test DB;
integration and smoke checks persist synthetic execution history and intentional
incidents. Tests can explicitly skip integration when that variable is absent.

```bash
ruff check backend pipelines scripts airflow
ruff format --check backend pipelines scripts airflow
mypy --config-file backend/pyproject.toml -p app
python -m scripts.smoke
python -m scripts.benchmark
```

Frontend: `cd frontend`, `npm ci`, `npm test`, `npm run build`. Dependencies are
recorded in package-lock.json. The Docker test profile can execute backend checks:
`docker compose --profile test run --build --rm tests`.
GitHub Actions checks Python, PostgreSQL integration, TypeScript/frontend build,
and Docker configuration. A configured workflow is not a claimed remote CI pass.

## Quality, KPIs and governance

See [rule definitions and dictionary](docs/data-dictionary.md),
[KPI formulas and denominators](docs/kpi-definitions.md),
[governance and retention](docs/governance.md), and [operations](docs/runbook.md).
A default 1000-row fixture contains 900 valid orders and 100 rejected rows. Each
rejected row preserves original values and all violated rule IDs. Rule outcomes
include run, dataset, severity, timestamp, affected count and result.

[Measured benchmark results](docs/benchmarks.json) reflect this local session:
1000 rows in 11.125s; 10000 in 16.000s; 100000 in 110.735s. Builds were active
and resources were constrained; these are not production throughput claims.

## Advanced profiles and limitations

See [Spark, Scala and Airflow instructions](docs/advanced-processing.md).
Run optional profiles sequentially on constrained machines. The Airflow DAG groups
processing into an atomic backend task; independently resumable stage tasks remain
pending. Airflow standalone metadata is local SQLite; all application data is PostgreSQL.

Remaining hardening: full stage-level Airflow recovery, automatic retention,
reconciliation of runs interrupted by process termination, a complete Python
transitive lock, broader dataset-domain validation, and expanded browser interaction
tests. Payments and inventory are not yet modeled; current analytics covers orders,
customers and products. Do not describe this local portfolio setup as production-ready.

## GitHub presentation

Description: Data reliability platform for reproducible commerce pipelines,
auditable quality validation and operational analytics.
Topics: data-engineering, data-quality, python, fastapi, postgresql, pyspark,
airflow, scala, react, portfolio.

Use real Conventional Commits as changes are reviewed. Suggested sequence:
`chore: initialize repository structure`, `feat: implement data ingestion`,
`feat: add data quality validation`, `feat: implement pyspark transformations`,
`feat: add airflow orchestration`, `feat: build monitoring dashboard`,
`test: add pipeline integration tests`, `docs: document architecture and setup`.
No artificial historical commits are created.

## About the Developer

"Developed as a portfolio project by a 5th-semester Software Engineering student, with a focus on Data Engineering, Data Quality, Pipeline Orchestration, and Data Governance."

## License

MIT. See [LICENSE](LICENSE).
