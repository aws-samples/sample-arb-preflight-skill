# Rubric — Security & Identity (`SEC`)

Standards: `standards/security-baseline.md`. Encryption, keys and network controls belong
to `LZ`; do not duplicate them here.

## How to review this domain

Work from trust boundaries. On the diagram, mark every place where a request crosses from
one level of trust to another: internet to edge, edge to workload, workload to workload,
workload to data, human to production, third party to anything. For each boundary ask two
questions: who is authenticated, and what are they authorised to do. A boundary with an
answer of "it is inside the VPC" is a finding, not an answer.

Then look for the design's answer to a hostile insider, not just an external attacker.
That is the scenario the board and internal audit care about most, and the one
architecture documents almost always skip.

## Identity and access

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `SEC-IAM-001` | Human AWS access federated through the organisation's IdP; no IAM users for people | `SB-IAM-01` | Blocker | Access model section |
| `SEC-IAM-002` | No long-lived access keys anywhere, including for third-party or SaaS integrations | `SB-IAM-02` | Blocker | Machine identity statement |
| `SEC-IAM-003` | Least privilege with resource and condition scoping; no wildcard-on-wildcard in prod | `SB-IAM-03` | Major | IAM design section |
| `SEC-IAM-004` | Permission boundaries on any role able to create roles or policies | `SB-IAM-04` | Major | IAM design section |
| `SEC-IAM-005` | Privileged access time-bound, approved, session-recorded, reviewed | `SB-IAM-05` | Blocker | Privileged access section |
| `SEC-IAM-006` | Access recertification and automated joiner/mover/leaver | `SB-IAM-06` | Major | Identity lifecycle statement |
| `SEC-IAM-007` | Application authorisation externalised, auditable, business-owned entitlements | `SB-IAM-07` | Major | Authorisation model |
| `SEC-IAM-008` | End-user authentication strength appropriate to the transaction risk, MFA where required | `SB-IAM-08` | Blocker | Authentication section |
| `SEC-IAM-009` | Roles are enumerated with what each can do, not just named | `SB-IAM-07` | Minor | Role/permission matrix |

## Segregation of duties

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `SEC-SOD-001` | Author of a change cannot approve its release to production | `SB-SOD-01` | Blocker | Release process statement |
| `SEC-SOD-002` | No single human can both initiate and authorise a high-value action (payment, refund, credit, entitlement grant) | `SB-SOD-02` | Blocker | Maker-checker design |
| `SEC-SOD-003` | No standing engineer read access to production customer or transaction data | `SB-SOD-03` | Blocker | Data access model |
| `SEC-SOD-004` | Audit log administration separated from the population being audited | `SB-SOD-04` | Major | Log ownership statement |
| `SEC-SOD-005` | Key administration separated from key use | `SB-SOD-05` | Major | Key ownership statement |
| `SEC-SOD-006` | The design states, in one place, who can deploy, who can approve, and who can reach production data | `SB-SOD-*` | Major | Explicit SoD statement |

## Service-to-service and trust boundaries

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `SEC-SVC-001` | Internal service calls mutually authenticated; network position is not authorisation | `SB-SVC-01` | Blocker | Internal auth statement |
| `SEC-SVC-002` | Tokens short-lived, audience-scoped, fully validated at each hop | `SB-SVC-02` | Major | Token design |
| `SEC-SVC-003` | External APIs exposed via the central API gateway with auth, rate limiting, schema validation | `SB-SVC-03` | Blocker | API exposure section |
| `SEC-SVC-004` | Input validation and output encoding at every boundary, deny by default | `SB-SVC-04` | Major | Boundary controls |
| `SEC-SVC-005` | Trust boundaries drawn and labelled on the architecture diagram | `SB-SVC-05` | Major | Diagram with boundaries |
| `SEC-SVC-006` | Inbound third-party traffic is authenticated and its payloads validated before reaching business logic | `SB-SVC-03` | Blocker | Third-party interface design |

## Secrets

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `SEC-SCR-001` | Secrets in the approved secrets manager only | `SB-SEC-01` | Blocker | Secrets section |
| `SEC-SCR-002` | Automated rotation without an outage | `SB-SEC-02` | Major | Rotation statement |
| `SEC-SCR-003` | Credential-free options used where available: roles, IRSA, PrivateLink, mTLS | `SB-SEC-03` | Minor | Rationale for any shared credential |
| `SEC-SCR-004` | No credential, key, token, endpoint secret or connection string appears in the submitted document itself | `SB-SEC-01` | Blocker | Scan of the extracted text |

## Threat model and assurance

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `SEC-THR-001` | Threat model present for tier 1 and 2, mapped to mitigations | `SB-THR-01` | Blocker (T1/T2) | Threat model section or annex |
| `SEC-THR-002` | Business-relevant abuse cases considered: account takeover, payment or refund fraud, insider misuse, mass extraction, scraping, replay | `SB-THR-02` | Major | Abuse case coverage |
| `SEC-THR-003` | Independent penetration test planned before go-live, with a remediation gate | `SB-THR-03` | Blocker (internet-facing or T1) | Assurance plan |
| `SEC-THR-004` | Supply chain controls: dependency scanning, SBOM, image provenance | `SB-THR-04` | Major | Build and supply chain statement |
| `SEC-THR-005` | Patch and vulnerability SLAs with a named owner, covering third-party components | `SB-THR-05` | Major | Vulnerability management section |
| `SEC-THR-006` | WAF, DDoS and bot controls proportionate to internet exposure | `SB-THR-06` | Major | Edge controls |
| `SEC-THR-007` | Where ML or generative AI is present, prompt injection, data leakage and output handling are addressed | `SB-SVC-04` | Major | AI security section |

## Detection and response

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `SEC-DET-001` | Security events logged and forwarded to the SIEM | `SB-DET-01` | Major | Logging section |
| `SEC-DET-002` | Detection use cases agreed with the SOC before go-live | `SB-DET-02` | Major | SOC engagement statement |
| `SEC-DET-003` | Workload in scope of incident response, with on-call path and accountable owner | `SB-DET-03` | Major | IR statement |
| `SEC-DET-004` | Exfiltration monitoring proportionate to data sensitivity | `SB-DET-04` | Major | Monitoring section |

## Contradiction checks

- "Zero trust" stated as a principle, with no internal authentication anywhere in the design.
- MFA claimed for customers, with an API or legacy channel that bypasses it.
- No standing production access claimed, alongside a support model that requires engineers
  to query the production database to resolve tickets.
- Maker-checker claimed for the business process, with a single engineer able to change the
  configuration that governs it.
- Threat model referenced but not supplied. Treat as absent and say so.

## Questions the board will ask

- Who can issue a refund or change a price, and can one person do it alone?
- What can a developer see in production, and how would we know they looked?
- What happens if the third party at this boundary is compromised?
- Where are the secrets, and when do they rotate?
- Has this been pen tested, and who signs off the findings?
- What is the blast radius of the most privileged role in this design?

## Do not raise

- Coding-level issues. There is no code in scope.
- Encryption algorithm or key-length preferences already fixed in `landing-zone-baseline.md`.
- Speculative vulnerabilities in AWS managed services.
