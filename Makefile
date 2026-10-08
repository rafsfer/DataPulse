.PHONY: up down test lint
up:
	docker compose up --build -d postgres api
down:
	docker compose down
test:
	docker compose --profile test run --build --rm tests
lint:
	.venv/bin/ruff check backend
	.venv/bin/ruff format --check backend
