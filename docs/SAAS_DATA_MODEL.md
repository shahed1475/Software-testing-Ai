# SaaS Data Model and APIs (Draft)

This defines core entities and the first-pass API surface for the SaaS.

## 1) Core entities

Org
- id, name, plan, created_at, billing_status

User
- id, org_id, email, role, status, mfa_enabled

Project
- id, org_id, name, description, created_at

Target
- id, project_id, name, type (web/api/network)
- scope (domains, IP ranges, ports)
- verification_status, verification_method
- auth_record_id

AuthorizationRecord
- id, target_id, verified_by, verified_at, expires_at
- proof_type (dns/http), proof_value

Suite
- id, name, type (functional/security/pentest), version

Run
- id, project_id, target_id, suite_id
- status, created_by, started_at, finished_at
- config (json), safe_mode, rate_limit

Finding
- id, run_id, severity, type, location, evidence_ref
- status (open/triaged/false_positive/fixed)

Report
- id, run_id, format (pdf/html/json), url, created_at

AuditEvent
- id, org_id, actor_id, action, metadata, created_at

## 2) API surface (REST v1)

Auth
- POST /auth/login
- POST /auth/logout
- POST /auth/mfa/verify

Orgs/Users
- GET /orgs/me
- GET /orgs/me/users
- POST /orgs/me/users
- PATCH /orgs/me/users/{userId}

Projects
- GET /projects
- POST /projects
- GET /projects/{projectId}
- PATCH /projects/{projectId}

Targets
- GET /projects/{projectId}/targets
- POST /projects/{projectId}/targets
- POST /targets/{targetId}/verify
- GET /targets/{targetId}
- PATCH /targets/{targetId}

Suites
- GET /suites

Runs
- POST /runs
- GET /runs/{runId}
- POST /runs/{runId}/cancel
- GET /runs/{runId}/logs (stream)

Findings
- GET /runs/{runId}/findings
- PATCH /findings/{findingId}

Reports
- GET /runs/{runId}/reports
- POST /runs/{runId}/reports

Audit
- GET /audit/events

Webhooks
- POST /webhooks
- GET /webhooks

## 3) Event schema (example)

event_type: run.completed
payload:
- org_id, project_id, run_id
- status, duration, findings_summary

## 4) Versioning

- Base path: /api/v1
- Backwards compatible changes only within v1
