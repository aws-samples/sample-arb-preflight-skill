# Rubric — Data & Privacy (`DAT`)

Standards: `standards/landing-zone-baseline.md` (encryption, residency),
`standards/obligations-register.md` (`OBL-DAT-*`, `OBL-AUD-01`).

## How to review this domain

Follow the data, not the components. For each data class the solution touches, establish
five things: where it originates, where it comes to rest, everywhere it is copied, who can
read it, and when it is destroyed. The copies are where the findings are. Backups,
replicas, caches, message payloads retained on a queue, event streams, data lake landings,
analytics extracts, log lines containing payloads, non-production test data, files sent to
a third party, and screenshots in support tickets are all copies, and each inherits the
classification of its source.

A design that lists its primary database and nothing else has not described its data
estate. Say so rather than reviewing only the part that was described.

## Classification and inventory

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `DAT-CLS-001` | Every data class handled is enumerated and classified | intake | Blocker | Data inventory or classification table |
| `DAT-CLS-002` | Special categories called out where present: personal, special-category personal (health, biometric), children's data, cardholder, authentication secrets, commercially confidential, employee | `OBL-DAT-01`, `OBL-DAT-04` | Blocker | Classification table |
| `DAT-CLS-003` | Every store, stream, queue, cache, log target and file exchange in the design carries a classification | `LZB-GRD-04` | Major | Per-store classification |
| `DAT-CLS-004` | Golden source identified for each entity; the design does not create a second authoritative copy | `OBL-DAT-05` | Major | Data ownership statement |
| `DAT-CLS-005` | Data minimisation considered: the design collects and retains only what it needs | `OBL-DAT-01` | Major | Justification for sensitive fields |

## Protection

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `DAT-PRO-001` | Encryption at rest with a customer-managed key for every store holding classified data | `LZB-KMS-01` | Blocker | Per-store statement |
| `DAT-PRO-002` | Encryption in transit on every hop, internal ones included | `LZB-KMS-04` | Major | Transport statement |
| `DAT-PRO-003` | Tokenisation, masking or field-level encryption for the most sensitive fields, with the scope of what it removes stated | `OBL-DAT-04` | Major | Tokenisation design |
| `DAT-PRO-004` | Non-production environments hold masked, synthetic or subsetted data; production data in non-prod requires an approved exception | `OBL-DAT-01` | Blocker | Test data strategy |
| `DAT-PRO-005` | Logs, traces, error messages and monitoring do not carry classified payloads | `SB-DET-01` | Major | Logging content statement |
| `DAT-PRO-006` | Data loss prevention or egress control where bulk extraction is possible | `SB-DET-04` | Major | Egress control statement |
| `DAT-PRO-007` | Access to data is role-based, least privilege, and logged at the record level where required | `SB-IAM-07` | Major | Data access model |

## Residency and movement

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `DAT-RES-001` | Every resting location is in the permitted jurisdiction, backups and DR copies included | `LZB-REG-02` | Blocker | Data flow with locations |
| `DAT-RES-002` | Cross-border movement has a stated legal transfer basis | `OBL-DAT-02` | Blocker | Transfer basis statement |
| `DAT-RES-003` | Support, operations and vendor access paths are assessed for residency, including follow-the-sun support and offshore teams | `OBL-DAT-02` | Blocker | Support model with locations |
| `DAT-RES-004` | Telemetry, logs and metrics do not leave the jurisdiction unless assessed | `LZB-REG-02` | Major | Observability destinations |
| `DAT-RES-005` | Where an AI or ML service is used, the location of inference, prompt logging and any model training on this data is stated | `OBL-DAT-02`, `OBL-MDL-01` | Blocker | AI data path statement |

## Retention, records and disposal

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `DAT-RET-001` | Retention period stated per data class, tied to a records policy rather than chosen by the team | `OBL-DAT-03` | Major | Retention table |
| `DAT-RET-002` | Immutable retention where records rules require it, with the retention lock mechanism named | `OBL-DAT-03` | Blocker (if in scope) | Retention lock design |
| `DAT-RET-003` | Defensible disposal at end of retention, including from backups and derived copies | `OBL-DAT-03` | Major | Disposal process |
| `DAT-RET-004` | Legal hold and its interaction with disposal considered | `OBL-DAT-03` | Minor | Legal hold statement |
| `DAT-RET-005` | Data subject rights are deliverable: access, rectification, erasure, portability, and objection where applicable | `OBL-DAT-01` | Major | Privacy operations statement |

## Audit trail and lineage

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `DAT-AUD-001` | Business- or legally significant events produce an immutable audit record: who, what, when, before and after | `OBL-AUD-01` | Blocker | Audit design |
| `DAT-AUD-002` | Nobody who can perform an audited action can alter or delete its audit record | `SB-SOD-04` | Blocker | Audit store ownership |
| `DAT-AUD-003` | Audit retention matches the regulatory period, not the application's operational needs | `OBL-DAT-03` | Major | Retention statement |
| `DAT-AUD-004` | Lineage traceable from a reported figure back to source where the data feeds financial, statutory or regulatory reporting | `OBL-DAT-05` | Major | Lineage approach |
| `DAT-AUD-005` | Data quality controls at ingestion, with a break process for failures | `OBL-DAT-05` | Major | Quality controls |

## Privacy

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `DAT-PRV-001` | Lawful basis and purpose stated for personal data processing | `OBL-DAT-01` | Major | Privacy section |
| `DAT-PRV-002` | DPIA completed or scheduled where processing is high risk, including profiling or automated decisions | `OBL-DAT-01` | Blocker (if in scope) | DPIA reference |
| `DAT-PRV-003` | Consent or preference state is honoured across every downstream copy | `OBL-DAT-01` | Major | Consent propagation |
| `DAT-PRV-004` | Automated decision-making affecting customers is identified, with the explanation and appeal path | `OBL-MDL-01` | Major | Decisioning statement |

## Contradiction checks

- Cardholder data declared out of scope, with the payload transiting a component that is
  not tokenised at the boundary.
- Residency asserted, with a cross-region backup, a global CDN, or a support team offshore.
- Erasure rights claimed, with an immutable event stream and a WORM archive holding the
  same records and no reconciliation of the two obligations.
- Masked non-production claimed, with a stated need for production-like volumes and no
  masking mechanism named.
- An audit trail described as immutable while sitting in a database the application's own
  role can write to.

## Questions the board will ask

- What is the most sensitive field here, and everywhere it ends up?
- Can anyone outside the jurisdiction see this data, including in support?
- How long do we keep it, and who says so?
- If a customer asks us to delete their data, what happens?
- Can someone with production access delete the evidence that they did?
- If a reported number is challenged, can you trace it to source?

## Do not raise

- Schema or data-model design quality.
- Storage engine preferences, unless the radar rules on them.
- Encryption clauses already raised under `LZ-KMS-*`. Cite the `LZ` finding instead of
  duplicating it.
