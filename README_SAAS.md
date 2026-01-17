# SaaS MVP Quickstart

This repo contains a FastAPI backend and a Next.js frontend for the SaaS MVP.

## Backend

Run the API (avoid importing the legacy `src` package):

```bash
python -m uvicorn saas_api.main:app --app-dir src --reload --port 8000
```

Key endpoints:
- `GET /api/v1/projects`
- `POST /api/v1/projects`
- `POST /api/v1/projects/{projectId}/targets`
- `POST /api/v1/targets/{targetId}/verify`
- `POST /api/v1/runs`
- `GET /api/v1/runs/{runId}/logs`
- `GET /api/v1/runs/{runId}/findings`
- `GET /api/v1/billing/usage`
- `GET /api/v1/audit/events`

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

If your API runs on a different host/port:

```bash
set NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
npm run dev
```

## Validation

```bash
python -m pytest tests/saas_api/test_mvp_flow.py
```
