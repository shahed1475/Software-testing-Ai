# MVP Validation Execution

This checklist validates the MVP backend and frontend wiring.

## 1) Backend smoke test

- Start API: `python -m uvicorn src.saas_api.main:app --reload --port 8000`
- Run tests: `python -m pytest tests/saas_api/test_mvp_flow.py`

Expected:
- Project, target, and run create successfully.
- Run completes and returns findings.

## 2) Frontend smoke test

- Start UI: `cd frontend && npm install && npm run dev`
- Open `http://localhost:3000`
- Create project and target, verify target, start run.

Expected:
- Status updates to running then completed.
- Logs show worker steps.
- Findings table populates.

## 3) Billing and audit

- Confirm billing usage in the UI updates after run.
- Check audit events: `GET http://localhost:8000/api/v1/audit/events`

## 4) Notes

- Runs are limited by `runs_used/max_runs` in `src/saas_api/store.py`.
- Targets must be verified before runs can start.
