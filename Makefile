.PHONY: install dev migrate revision admin test lint format check

install:
	uv sync

dev:
	uv run fastapi dev src/yas_api/main.py

migrate:
	uv run alembic upgrade head

revision:
	uv run alembic revision --autogenerate -m "$(m)"

admin:
	uv run yas-create-admin

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

check: lint test

