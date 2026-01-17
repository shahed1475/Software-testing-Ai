# SaaS Validation and Rollout (Draft)

This defines validation steps before GA.

## 1) Internal validation

- Unit and integration tests
- Run orchestration tests (happy path + failure path)
- Security checks (dependency scan, secrets scan)

## 2) Security review

- Threat model review
- Internal pen test
- Fix critical findings before beta

## 3) Beta program

- Invite limited cohort
- Monitor usage, run reliability, and findings quality
- Weekly feedback sessions

## 4) Metrics to track

- Run success rate
- Mean time to results
- Findings false-positive rate
- Customer activation rate

## 5) GA readiness

- SLA/SLO finalized
- Incident response runbooks tested
- Support workflow ready
