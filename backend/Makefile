.PHONY: dev lint typecheck test

dev:
	docker compose up --build

lint:
	ruff check .

typecheck:
	mypy apps libs tests

test:
	pytest tests/
