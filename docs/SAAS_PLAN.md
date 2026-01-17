# SaaS Product Plan (Draft)

This document captures the SaaS product scope, personas, pricing tiers, and compliance boundaries.
It is a living plan and will evolve as requirements are validated.

## 1) Product scope and value

Goal: Provide a single platform where teams can run software tests and authorized penetration testing
against their own applications and infrastructure, with clear safety controls and auditability.

Primary outcomes:
- Faster feedback on quality and security risk
- Unified results and reporting across test types
- Safe, authorized testing with auditable consent

In-scope capabilities (MVP):
- Project and target management
- Test suite selection (functional + pentest demo suites)
- Run orchestration with live logs
- Findings dashboard and exportable reports
- Role-based access control
 - Target verification workflow (domain/DNS or file-based proof)
 - Safe-scan presets with rate limiting and scope guards
 - Evidence capture (request/response snippets or headers only)

Out of scope (MVP):
- Unbounded internet-wide scanning
- Automatic exploitation workflows
- Any testing without explicit target authorization
 - Destructive testing (data modification, denial-of-service)
 - Credential stuffing or brute force by default

## 2) Target users (personas)

- QA Lead: needs fast regression and quality reporting across teams
- Security Engineer: needs actionable findings with severity and audit trails
- Engineering Manager: needs trend dashboards and compliance-ready reporting
- Dev Team Member: needs self-service tests before release

## 3) Pricing tiers (draft)

- Trial: limited runs, 1-2 targets, standard reports, basic retention
- Team: per-seat + usage-based runs, team management, scheduled runs, longer retention
- Enterprise: SSO/SAML, advanced audit logs, private runners, custom SLAs, data residency

Usage limits should be enforced per tier:
- Max targets per org
- Max concurrent runs
- Max monthly run minutes
 - Max data retention window

## 4) Compliance boundaries and authorization model

Mandatory controls:
- Target ownership attestation required before running any pentest suite
- Scope declaration per target (domains, IP ranges, environments)
- Safe-scan defaults enabled (rate limits, passive scanning)
- Audit logs for all configuration changes and scan execution
 - Restricted scan categories per tier (e.g., passive only on Trial)
 - Explicit acknowledgement of terms before first scan

Consent workflow (baseline):
1. Org admin verifies target ownership and scope.
2. System generates an authorization record tied to the target.
3. Runs are allowed only within defined scope and valid authorization.

Target verification options:
- DNS TXT record proof
- HTTP file upload proof
- Cloud account connector (enterprise)

Safe-scan baseline (MVP):
- Passive discovery only by default
- Hard rate limit per target
- Strict allowlist of paths and hosts

## 5) Key assumptions to validate

- Users prefer combined test and security workflows in one tool.
- Safe scanning defaults are acceptable for most teams.
- Reporting format aligns with compliance expectations (SOC2/ISO style).

## 6) Immediate next steps

- Confirm personas and tier model with stakeholders.
- Define initial list of allowed pentest checks for MVP.
- Capture compliance requirements (internal or customer driven).
