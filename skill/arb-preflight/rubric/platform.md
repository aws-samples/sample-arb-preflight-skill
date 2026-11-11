# Rubric — Platform & Landing Zone (`LZ`)

Standards: `standards/landing-zone-baseline.md`, `standards/tech-radar.md`,
`standards/pattern-catalog.md`.

## How to review this domain

Start from the deployment view diagram, not the prose. Trace one request end to end:
internet or on-premises source → edge → workload → data store → and back. Then trace one
egress call outbound. Most landing-zone breaches are visible as a line on a diagram that
should not exist, or a line that should exist and does not.

Then trace the data at rest: which store, which account, which region, whose key.

Silence about a platform control usually means inheritance, which is fine. What matters
is whether the design *depends on an exception* to a control. That is the thing that
surfaces during deployment, weeks after the board approved it.

## Submission quality

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `LZ-DOC-001` | A viewable deployment diagram exists showing accounts, VPCs, subnets and traffic paths | intake | Blocker | Diagram in a viewable raster format |
| `LZ-DOC-002` | All diagrams are viewable; none supplied only as EMF/WMF/SVG | intake | Major | `manifest.json` `unreadable` list empty |
| `LZ-DOC-003` | Diagram and prose agree with each other | — | Major | No contradiction found |
| `LZ-DOC-004` | Submission is versioned and dated | intake | Minor | Version on the document |

## Solution context

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `LZ-CTX-001` | Business purpose and the capability served are stated | intake | Major | Overview section |
| `LZ-CTX-002` | Scope boundaries stated, including what is explicitly out of scope | intake | Major | Scope section |
| `LZ-CTX-003` | Named business owner and technical owner | intake | Major | Owner section |
| `LZ-CTX-004` | Key architecture decisions recorded with the options rejected and why | — | Minor | Decision log or ADR references |
| `LZ-CTX-005` | Whatever this replaces or extends is identified, with the interim coexistence state | — | Major | Migration or transition section |
| `LZ-CTX-006` | Assumptions and dependencies on other programmes are stated | — | Minor | Assumptions section |

## Accounts and organisation

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `LZ-ACC-001` | Dedicated accounts per environment; prod isolated from non-prod | `LZB-ACC-01` | Blocker | Account list or deployment view |
| `LZ-ACC-002` | Correct OU placement for classification and environment | `LZB-ACC-02` | Major | Account/OU statement |
| `LZ-ACC-003` | Accounts vended through account factory with tier, classification, owner, cost centre | `LZB-ACC-03` | Minor | Provisioning statement |
| `LZ-ACC-004` | Design does not require an SCP exception; if it does, platform sign-off is already obtained | `LZB-ACC-04` | Blocker | Explicit statement or approved exception reference |
| `LZ-ACC-005` | No shared-services sprawl: the design does not introduce a new shared account where an existing platform account serves | — | Minor | Account rationale |

## Region and residency

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `LZ-RGN-001` | All primary and secondary regions are on the approved list | `LZB-REG-01` | Blocker | Named regions |
| `LZ-RGN-002` | No data, including backups, logs, telemetry and support access, leaves the jurisdiction without a stated transfer basis | `LZB-REG-02` | Blocker | Data flow and log destination statement |
| `LZ-RGN-003` | Global or out-of-region control planes are identified and assessed | `LZB-REG-03` | Major | Service list with region notes |
| `LZ-RGN-004` | Replication and DR targets are in approved regions and the same jurisdiction | `LZB-REG-04` | Major | DR section |
| `LZ-RGN-005` | AZ selection is explicit, not left to defaults, where AZ affinity affects latency or resilience | — | Minor | Subnet/AZ layout |

## Network

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `LZ-NET-001` | VPC attaches to the transit gateway; no ad-hoc peering | `LZB-NET-01` | Major | Deployment view |
| `LZ-NET-002` | No internet gateway or NAT in the workload VPC; egress via central inspection | `LZB-NET-02` | Blocker | Egress path on the diagram |
| `LZ-NET-003` | Internet ingress terminates at the central edge with WAF and DDoS before the workload | `LZB-NET-03` | Blocker | Ingress path on the diagram |
| `LZ-NET-004` | Compute and data in private subnets, no public IPs | `LZB-NET-04` | Blocker | Subnet layout |
| `LZ-NET-005` | AWS service access via VPC endpoints or PrivateLink | `LZB-NET-05` | Major | Endpoint list or diagram |
| `LZ-NET-006` | Third-party connectivity terminates in the partner zone, not the workload VPC | `LZB-NET-06` | Blocker | Partner connectivity path |
| `LZ-NET-007` | CIDRs allocated by central IPAM, no overlap | `LZB-NET-07` | Major | CIDR statement |
| `LZ-NET-008` | DNS via central resolver; zones registered | `LZB-NET-08` | Minor | DNS statement |
| `LZ-NET-009` | No `0.0.0.0/0` inbound; security groups reference groups or prefix lists | `LZB-NET-09` | Major | Security group approach |
| `LZ-NET-010` | On-premises connectivity reuses the existing Direct Connect / VPN hub | `LZB-NET-10` | Major | Connectivity section |
| `LZ-NET-011` | East-west segmentation between tiers and between this workload and others | `LZB-NET-09` | Major | Segmentation on the diagram |

## Encryption, keys and guardrails

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `LZ-KMS-001` | Every data store encrypted at rest with a customer-managed key | `LZB-KMS-01` | Blocker | Per-store encryption statement |
| `LZ-KMS-002` | Key administration separated from key use | `LZB-KMS-02` | Major | Key ownership statement |
| `LZ-KMS-003` | Key rotation enabled | `LZB-KMS-03` | Minor | Key management section |
| `LZ-KMS-004` | TLS 1.2 minimum everywhere, including internal hops | `LZB-KMS-04` | Major | Transport statement |
| `LZ-KMS-005` | Certificates from the organisation's PKI or ACM with automated renewal | `LZB-KMS-05` | Major | Certificate section |
| `LZ-GRD-001` | No platform guardrail is disabled or bypassed | `LZB-GRD-01` | Blocker | Explicit statement or absence of any bypass |
| `LZ-GRD-002` | Logs ship to the central archive with the required retention; workload cannot delete them | `LZB-GRD-02` | Major | Logging destination and retention |
| `LZ-GRD-003` | Mandatory tags applied | `LZB-GRD-04` | Minor | Tagging statement |

## Provisioning and change path

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `LZ-PRV-001` | Infrastructure as code through the approved pipeline; no console changes in prod | `LZB-PRV-01` | Major | Deployment approach |
| `LZ-PRV-002` | No standing human access to production | `LZB-PRV-02` | Blocker | Access model |
| `LZ-PRV-003` | Pipeline assumes a role; no long-lived keys, including for third-party tooling | `LZB-PRV-03` | Blocker | Pipeline identity statement |
| `LZ-PRV-004` | Break-glass path defined, alerting, reviewed | `LZB-PRV-04` | Major | Emergency access section |
| `LZ-PRV-005` | Container images from the central registry, scanned before promotion | `LZB-PRV-05` | Major | Image supply statement |

## Technology and pattern conformance

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `LZ-TEC-001` | Every technology in the design is `Adopt` or `Trial` on the radar | tech-radar | Major; Blocker if any technology is on Hold | Technology list |
| `LZ-TEC-002` | `Trial` technologies have a named architect sponsor and production support model | tech-radar | Minor | Support statement |
| `LZ-TEC-003` | No service in preview, or without an SLA, in a tier 1 or 2 path | tech-radar | Blocker | Service list |
| `LZ-TEC-004` | Managed services preferred over self-managed where an approved managed option exists | tech-radar | Minor | Rationale for self-managed |
| `LZ-PAT-001` | Where an approved pattern applies, the design conforms, or the deviation is stated with a reason | pattern-catalog | Major | Pattern reference |
| `LZ-PAT-002` | No catalogued anti-pattern present | pattern-catalog | Major | — |

## Contradiction checks

- An availability target of 99.99% with a single-AZ component on the diagram.
- A claim of "no internet exposure" alongside a public ALB or public S3 endpoint.
- A residency claim alongside a global service, a cross-region backup, or an offshore
  support model.
- "Standard landing zone" in the prose while the diagram shows a workload internet
  gateway or a direct partner VPN.
- A managed-service claim in the text with EC2 instances doing the same job on the diagram.

## Questions the board will ask

- Which accounts and OUs, and were they vended through the factory?
- Draw me the egress path. Where is it inspected?
- What is public, and what sits in front of it?
- Whose KMS key, and who can administer it?
- Does anything here need an SCP exception, and who has agreed it?
- Which of these services have you run in production before?

## Do not raise

- Cost or instance sizing. That belongs to `OPS`.
- IaC quality, module structure, or repository layout. Out of scope; there is no code.
- Generic "consider using X" recommendations with no clause behind them. If it matters
  and no clause covers it, raise it as `Advisory` with rule ID `NONE` and propose the
  clause.
