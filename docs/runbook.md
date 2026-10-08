# Local operations

1. Copy .env.example to .env and replace the local password and admin key.
   For Compose URL interpolation use letters, numbers, underscores and hyphens;
   URL-encode special characters for local connection URLs.
2. Start Docker Desktop with Linux containers.
3. Run `docker compose up --build -d postgres api`.
4. Check `docker compose ps` and http://localhost:8000/api/health.
5. Inspect `docker compose logs api` if readiness returns 503.
6. Stop with `docker compose down`; the named volume is preserved.

Run `docker compose --profile test run --build --rm tests` for PostgreSQL integration.
The SQL bootstrap only runs on a new volume. Apply future migrations explicitly;
do not delete persistent data to apply a schema change.

A missing daemon, occupied port or unavailable registry blocks startup verification.
The admin key is reserved for Phase 3; no administrative routes exist yet.

## Windows prerequisite identified during verification

This machine reports that WSL is not installed. Configure WSL 2 and the Windows
virtualization prerequisites required by Docker Desktop, restart Windows if
requested, and confirm Docker Desktop can run Linux containers. Then repeat the
Compose startup and integration checks above. Changing Windows optional features
is a machine administration step outside this repository's setup.

Python 3.12.9 was installed through uv and the repository .venv now uses it.
The README's Python launcher command assumes a launcher-registered installation;
you may also create an environment with uv: `uv venv --python 3.12 .venv`.
