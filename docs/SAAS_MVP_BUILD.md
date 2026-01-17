# SaaS MVP Build Plan (Draft)

This breaks the MVP into buildable milestones.

## 1) Backend foundation

- Auth (email/password + MFA baseline)
- Org, user, project, target CRUD
- Target verification flow (DNS/HTTP)
- Run creation API and basic queue

## 2) Worker and scanning

- Worker container with strict egress rules
- Scan adapter interface
- Integrate one passive scanner (e.g., OWASP ZAP baseline)
- Capture artifacts and logs to object storage

## 3) Findings pipeline

- Normalize findings schema
- Severity mapping
- Findings API + basic triage states

## 4) Frontend MVP

- Onboarding wizard
- Target setup + verification
- Run configuration + live log view
- Findings dashboard with export

## 5) Billing

- Stripe integration (trial + Team)
- Usage counters and plan limits

## 6) Hardening

- Rate limits
- Audit logs
- Safe-scan guards
