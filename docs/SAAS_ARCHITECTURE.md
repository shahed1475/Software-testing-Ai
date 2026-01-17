# SaaS Architecture (Draft)

This architecture targets a multi-tenant SaaS for testing and authorized penetration testing.
It prioritizes isolation, auditability, and safe execution.

## 1) High-level components

- API Gateway
- Auth service (SSO/OAuth/MFA)
- Tenant service (orgs, users, roles, billing)
- Project/Target service (scope + authorization records)
- Run orchestration service
- Worker pool (scan runners)
- Findings/Report service
- Notification service (email/Slack)
- Object storage (artifacts)
- Data store (metadata + results)
- Observability (logs/metrics/traces)

## 2) Core flows

### a) Onboarding and target verification
1. User creates org, adds project.
2. Adds target + scope (domains, IP ranges).
3. Chooses verification method (DNS/HTTP file).
4. System validates proof and creates authorization record.

### b) Run execution
1. User configures run (suite + toggles).
2. Orchestrator creates a run, enqueues jobs.
3. Workers pull jobs, execute scans in isolated containers.
4. Artifacts + logs stored in object storage.
5. Findings processed and persisted.
6. UI streams logs and final report is generated.

## 3) Isolation and safety model

- Per-run sandbox container (least privilege)
- Network egress allowed only to in-scope targets
- CPU/memory limits per worker
- Rate limiting per target (global + per run)
- Passive scan mode default for low tiers
- Signed config payloads passed to workers

## 4) Data stores

- Primary DB: Postgres (orgs, targets, runs, findings, reports)
- Cache: Redis (queues, rate limits, sessions)
- Object storage: S3-compatible (artifacts, reports)

## 5) Job orchestration

- Queue: Redis/RabbitMQ
- Worker autoscaling via queue depth
- Run state machine: created → running → processing → completed/failed/cancelled
- Idempotent retry on worker failures

## 6) Deployment topology (cloud agnostic)

- Public tier: API gateway, auth, UI
- Private tier: job workers and scanners
- Data tier: DB, cache, object storage
- Network segmentation with strict egress rules

## 7) Observability and audit

- Structured logs (tenant_id, run_id, target_id)
- Audit events for all sensitive actions
- Metrics: run duration, failure rate, findings by severity

## 8) MVP technology choices (suggested)

- Backend: Python (FastAPI) or Node (NestJS)
- Queue: Redis + RQ/Celery or RabbitMQ
- Workers: Docker containers on a cluster (K8s or ECS)
- UI: Next.js or React
- Storage: Postgres + S3

## 9) Open questions

- Single-tenant option for enterprise?
- Data residency requirements?
- Do we require a separate private runner agent?
