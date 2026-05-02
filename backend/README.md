# Home Energy Advisor Backend

FastAPI backend for the Home Energy Advisor app.

## Commands

```text
uv run uvicorn app.main:app --reload
uv run pytest
uv run ruff check .
uv run ty check
```

## API

All routes are mounted under `/api/v1`.

The initial backend setup exposes:

```text
GET /api/v1/health
```

