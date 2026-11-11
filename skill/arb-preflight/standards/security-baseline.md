# Security Architecture Baseline

Status: `[DEFAULT — CONFIRM]` — owned by Security Architecture.

Encryption, key management and network controls live in `landing-zone-baseline.md`. This
file covers what the workload owns above the platform.

## Identity and access

| ID | Clause | Default |
|---|---|---|
| `SB-IAM-01` | Human access to AWS is federated through the organisation's IdP. No IAM users for people. | `[DEFAULT — CONFIRM]` |
| `SB-IAM-02` | No long-lived access keys. Workload identity uses IAM roles; external systems use OIDC federation or IAM Roles Anywhere. | `[DEFAULT — CONFIRM]` |
| `SB-IAM-03` | Least privilege, scoped by resource and condition. Wildcard actions on wildcard resources are prohibited in production. | `[DEFAULT — CONFIRM]` |
| `SB-IAM-04` | Permission boundaries applied to any role that can create roles or policies. | `[DEFAULT — CONFIRM]` |
| `SB-IAM-05` | Privileged and emergency access is time-bound, approved, session-recorded, and reviewed. | `[DEFAULT — CONFIRM]` |
| `SB-IAM-06` | Access is recertified at least `[TBD]` and on role change. Joiner/mover/leaver is automated from HR source. | `[DEFAULT — CONFIRM]` |
| `SB-IAM-07` | Application authorisation is role- or attribute-based, externalised from code, and auditable. Entitlements are owned by the business, not by engineering. | `[DEFAULT — CONFIRM]` |
| `SB-IAM-08` | Customer-facing authentication requires MFA and meets `[TBD]` assurance level. | `[TBD]` |

## Segregation of duties

The control auditors probe first, and the one architecture documents most often omit.

| ID | Clause | Default |
|---|---|---|
| `SB-SOD-01` | The identity that writes code cannot be the identity that approves its release to production. | `[DEFAULT — CONFIRM]` |
| `SB-SOD-02` | No single human can initiate and authorise a high-value transaction (payment, refund, credit, order override), configuration change, or entitlement grant. | `[DEFAULT — CONFIRM]` |
| `SB-SOD-03` | Engineers have no standing read access to production customer or transaction data. Access is broken-glass, justified, logged, and time-bound. | `[DEFAULT — CONFIRM]` |
| `SB-SOD-04` | Whoever administers the audit log cannot be whoever the log is auditing. Log archive is a separate account with separate administration. | `[DEFAULT — CONFIRM]` |
| `SB-SOD-05` | KMS key administration is separated from key use. | `[DEFAULT — CONFIRM]` |

## Service-to-service and boundaries

| ID | Clause | Default |
|---|---|---|
| `SB-SVC-01` | Internal service calls are mutually authenticated. Network position is not an authorisation decision. | `[DEFAULT — CONFIRM]` |
| `SB-SVC-02` | Tokens are short-lived, audience-scoped, and validated at every hop including signature and issuer. | `[DEFAULT — CONFIRM]` |
| `SB-SVC-03` | External API exposure goes through the central API gateway with authentication, authorisation, rate limiting and schema validation. | `[DEFAULT — CONFIRM]` |
| `SB-SVC-04` | Input validation and output encoding at every trust boundary. Deny by default. | `[DEFAULT — CONFIRM]` |
| `SB-SVC-05` | Trust boundaries are drawn explicitly on the architecture diagram. An unlabelled boundary is an unreviewed boundary. | `[DEFAULT — CONFIRM]` |

## Secrets

| ID | Clause | Default |
|---|---|---|
| `SB-SEC-01` | Secrets live in the approved secrets manager. Never in code, config files, environment variables baked into images, pipeline variables, or documents. | `[DEFAULT — CONFIRM]` |
| `SB-SEC-02` | Automated rotation, maximum age `[TBD]`. Rotation must not require an outage. | `[DEFAULT — CONFIRM]` |
| `SB-SEC-03` | Prefer no secret at all: IAM roles, IRSA, PrivateLink and mTLS over shared credentials. | `[DEFAULT — CONFIRM]` |

## Threat modelling and assurance

| ID | Clause | Default |
|---|---|---|
| `SB-THR-01` | A threat model exists for tier 1 and 2, covering trust boundaries, spoofing, tampering, repudiation, disclosure, denial of service and elevation, with mitigations mapped to controls. | `[DEFAULT — CONFIRM]` |
| `SB-THR-02` | Abuse cases relevant to the business are considered: account takeover, payment or refund fraud, promotion and loyalty abuse, insider misuse, mass data extraction, scraping, replay. | `[DEFAULT — CONFIRM]` |
| `SB-THR-03` | Independent penetration test before production for internet-facing or tier 1 systems; high findings closed or formally risk-accepted before go-live. | `[DEFAULT — CONFIRM]` |
| `SB-THR-04` | Software supply chain: dependency scanning, SBOM produced, image provenance verified, build artefacts immutable. | `[DEFAULT — CONFIRM]` |
| `SB-THR-05` | Vulnerability remediation SLAs: critical `[TBD]`, high `[TBD]`. Named owner for patching, including for managed and third-party components. | `[TBD]` |
| `SB-THR-06` | Internet-facing services have WAF, DDoS protection, and bot controls proportionate to exposure. | `[DEFAULT — CONFIRM]` |

## Detection and response

| ID | Clause | Default |
|---|---|---|
| `SB-DET-01` | Security-relevant events are logged and forwarded to the SIEM: authentication, authorisation failures, privileged actions, data export, configuration change. | `[DEFAULT — CONFIRM]` |
| `SB-DET-02` | Detection use cases for this workload are agreed with the SOC before go-live. | `[DEFAULT — CONFIRM]` |
| `SB-DET-03` | The workload is in scope of the incident response plan, with an on-call path and a named accountable owner. | `[DEFAULT — CONFIRM]` |
| `SB-DET-04` | Data exfiltration monitoring proportionate to the sensitivity of the data held. | `[DEFAULT — CONFIRM]` |

## Reviewer notes

- Zero trust means the design cannot rely on "it is in the private subnet" as its
  authorisation story. Look specifically for that reasoning; it is common and it is a
  finding under `SB-SVC-01`.
- Where the design includes a machine-learning or generative-AI component, treat the
  model endpoint and its prompt/data path as a trust boundary, and check prompt injection
  and data leakage explicitly against `SB-SVC-04`. Regulatory expectations sit in
  `obligations-register.md` under `OBL-MDL-*`.
