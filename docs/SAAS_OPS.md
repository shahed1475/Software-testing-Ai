# SaaS Operations Foundation (Draft)

This covers CI/CD, infrastructure, monitoring, and reliability basics.

## 1) CI/CD

- Build and test on every PR
- Security scans (SAST, dependency audit)
- Automated deploy to staging
- Manual promotion to production

## 2) Infrastructure as code

- Terraform for cloud resources
- Environment separation (dev/stage/prod)
- Secrets in managed vault

## 3) Monitoring and logging

- Centralized logs with trace IDs
- Metrics: run duration, queue depth, failure rate, findings by severity
- Alerts for worker failures and queue backlogs

## 4) Backups and DR

- Daily DB backups with retention policy
- Object storage lifecycle rules
- DR runbook with RTO/RPO targets

## 5) SLO/SLAs

- API uptime SLO (e.g., 99.9%)
- Run processing time targets
- Support response time targets

## 6) Incident response

- On-call rotation
- Incident severity rubric
- Post-incident reviews
