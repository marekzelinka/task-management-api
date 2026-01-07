start:
    uv run uvicorn main:app

dev:
    uv run uvicorn main:app --reload

typecheck:
    uv run ty check

lint:
    uv run ruff check --fix

format:
    uv run ruff format
