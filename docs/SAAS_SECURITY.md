# SaaS Security and Compliance Controls (Draft)

This document defines the security model and compliance controls for the SaaS.

## 1) Identity and access

- SSO (SAML/OIDC) for enterprise
- MFA for all roles
- RBAC with least privilege defaults
- Session timeouts and device management

## 2) Authorization and scope

- Every target requires a verified authorization record
- Scope enforced at run creation and at worker runtime
- Strict allowlist of domains/IPs per target
- Runs blocked if scope or authorization is missing or expired

## 3) Safe scanning defaults

- Passive scan by default on Trial
- Rate limits enforced globally and per target
- No destructive tests (data modification, DoS)
- Aggressive mode requires org admin approval

## 4) Secrets handling

- Secrets stored in a vault (KMS-backed)
- Short-lived worker tokens
- Masking in logs and reports
- Rotate tokens on schedule

## 5) Audit and compliance

- Immutable audit logs for:
  - Target creation and verification
  - Run creation, start, cancellation
  - Role changes and billing events
- Exportable audit log for compliance reviews

## 6) Data protection

- Encryption at rest (DB + object storage)
- TLS everywhere
- Data retention policy per plan
- Support data deletion requests

## 7) Legal and consent

- Terms acceptance before first scan
- Explicit consent and scope attestation
- Disclosure policy for findings

## 8) Abuse prevention

- Rate limits and quotas
- Anomaly detection for scans outside normal behavior
- Automatic run termination on violations

## 9) Security testing

- Regular internal pen tests
- Automated dependency scanning
- SAST and secrets scanning in CI
