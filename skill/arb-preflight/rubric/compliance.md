# Rubric — Regulatory & Third-Party (`REG`)

Standard: `standards/obligations-register.md`. **This domain depends entirely on that
file.** If a regime's `Applies` column is `TBC`, report the dependent rules as
`Insufficient information — standard not populated` and name Compliance as the owner of
resolving applicability. Do not guess which regulations apply, and do not cite regulation
text that is not reproduced in the register.

**Severity rule for this domain.** A rule whose `Standard` column is an `OBL-*` clause, and
whose governing regimes are all `TBC` or `no`, is never a finding of any severity. Report
it only under `Not assessable` with reason `standard not populated`, even when the design
evidence is plainly missing. Put the missing design evidence in the `What is missing`
column so the row is ready once Compliance sets applicability. The only rules in this
domain that may be raised as findings while the register is unpopulated are those whose
`Standard` column is `intake`, `—`, or a clause outside `obligations-register.md` (for
example `CT-EXIT` in `criticality-tiering.md`), and those follow the normal clause-state
rules.

## How to review this domain

You are not determining compliance. You are checking that the design has an answer to
questions the board's risk and compliance members will ask, and that the answer is written
down before the meeting rather than improvised during it.

Three areas produce almost all the findings, and all three are usually absent from an HLD
because engineers do not think of them as architecture:

1. **Third-party classification.** Introducing a SaaS provider or a new AWS service into a
   critical path may make it a critical supplier, which can carry due-diligence, contractual,
   notification and exit obligations with lead times measured in months. A design that
   discovers this at the board has already lost its go-live date.
2. **Exit and substitutability.** Regulators, auditors and customers increasingly expect
   the organisation to be able to leave a critical provider without disorderly disruption. Almost no HLD addresses it.
3. **Evidence.** Not whether the control exists, but whether it produces evidence an
   auditor can review two years later.

## Applicability

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `REG-APP-001` | Legal entities and jurisdictions in scope are stated | intake | Major | Entity and jurisdiction statement |
| `REG-APP-002` | Applicable regimes identified from the register, with the strictest governing where entities differ | register | Major | Regulatory footprint section |
| `REG-APP-003` | Regulated activity or critical business service supported is named where relevant | `OBL-RES-01` | Major | Business context |
| `REG-APP-004` | Compliance or risk function has been engaged, with evidence, not merely mentioned | — | Major | Engagement record |

## Operational resilience obligations

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `REG-RES-001` | Impact tolerance defined for the critical business service, and the design shown able to stay within it | `OBL-RES-01` | Blocker | Impact tolerance mapping |
| `REG-RES-002` | Severe-but-plausible scenario testing planned or evidenced | `OBL-RES-02` | Major | Scenario test plan |
| `REG-RES-003` | Service mapped to its supporting resources: technology, third parties, facilities, people | `OBL-RES-03` | Major | Resource mapping |
| `REG-RES-004` | The resilience posture the architecture delivers is reconciled against the regulatory obligation, and any gap is named with an owner | `OBL-RES-01` | Blocker | Gap statement |

## Third-party and supplier risk

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `REG-TPR-001` | Every third party is identified, including subcontractors and fourth parties in the data path | `OBL-TPR-01` | Blocker | Third-party inventory |
| `REG-TPR-002` | Each is classified: critical, important, or neither, with who classified it | `OBL-TPR-01` | Blocker | Classification record |
| `REG-TPR-003` | Registration and regulatory notification obligations identified with their lead times, and the plan accommodates them | `OBL-TPR-01` | Blocker | Notification plan |
| `REG-TPR-004` | Due diligence completed or scheduled before contract and before go-live | `OBL-TPR-01` | Major | Due diligence record |
| `REG-TPR-005` | Contractual audit and access rights secured, including flow-down to subcontractors | `OBL-TPR-04` | Major | Contract confirmation |
| `REG-TPR-006` | Provider's own resilience and security posture assessed against what this service needs | `OBL-TPR-01` | Major | Provider assessment |
| `REG-TPR-007` | Provider incident notification obligations align with the organisation's own regulatory deadlines | `OBL-SEC-02` | Major | Notification terms |
| `REG-TPR-008` | Data processed or accessed by the third party is stated, with location and lawful basis | `OBL-DAT-02` | Blocker | Third-party data statement |
| `REG-TPR-009` | New AWS services in a critical path are assessed against the existing cloud agreement and supplier assessment, not assumed covered | `OBL-TPR-01` | Major | Service coverage confirmation |

## Concentration and exit

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `REG-CON-001` | Concentration risk assessed: provider, region, and shared-component concentration across the organisation's critical services | `OBL-TPR-03` | Major | Concentration assessment |
| `REG-CON-002` | Exit plan for each critical provider: trigger, target state, data extraction, timeline, cost | `CT-EXIT`, `OBL-TPR-02` | Major; Blocker for critical providers | Exit plan |
| `REG-CON-003` | Exit is credible, not theoretical: data is extractable in a usable form, and a substitute exists or could be built | `OBL-TPR-02` | Major | Substitutability analysis |
| `REG-CON-004` | Stressed-exit scenario considered, where the provider fails rather than the organisation choosing to leave | `OBL-TPR-02` | Major | Stressed exit statement |
| `REG-CON-005` | Lock-in introduced by proprietary services in the critical path is identified and accepted knowingly | `OBL-TPR-02` | Minor | Lock-in assessment |

## Audit, evidence and control

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `REG-AUD-001` | Controls in the design map to the internal control library, with IDs | `OBL-AUD-*` | Major | Control mapping |
| `REG-AUD-002` | Each control produces reviewable evidence, retained for the required period | `OBL-AUD-01` | Major | Evidence approach |
| `REG-AUD-003` | Segregation of duties is evidenced technically, not asserted procedurally | `OBL-AUD-02` | Blocker | SoD evidence (assessed in detail under `SEC`) |
| `REG-AUD-004` | Change approval evidence is retained and auditable | `OBL-AUD-03` | Major | Change evidence |
| `REG-AUD-005` | Where the design is in scope of a financial-reporting or certification control set (e.g. SOX ITGC, SOC 2, ISO/IEC 27001), the in-scope controls are identified | `OBL-AUD-*` | Major | Scope statement |
| `REG-AUD-006` | Regulatory reporting outputs, if any, have accuracy and completeness controls with lineage | `OBL-DAT-05` | Major | Reporting controls |

## Incident and notification

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `REG-INC-001` | Incident classification maps to regulatory notification thresholds and deadlines | `OBL-SEC-02` | Major | Incident mapping |
| `REG-INC-002` | Who declares a reportable incident, and what starts the clock, is defined | `OBL-SEC-02` | Major | Declaration process |
| `REG-INC-003` | The design can produce the facts a notification requires: scope, timing, affected customers, data involved | `OBL-SEC-02` | Major | Forensic readiness |
| `REG-INC-004` | Independent security testing completed before go-live where required | `OBL-SEC-03` | Major | Test plan |

## Model and AI governance

Applies only where the design contains a model, a scoring engine, or a generative-AI
component.

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `REG-MDL-001` | Model registered in the model inventory, with an owner | `OBL-MDL-01` | Blocker | Inventory reference |
| `REG-MDL-002` | Independent validation before use, proportionate to model risk | `OBL-MDL-01` | Blocker | Validation record |
| `REG-MDL-003` | Ongoing monitoring for drift and performance degradation | `OBL-MDL-01` | Major | Monitoring plan |
| `REG-MDL-004` | Human oversight and override for decisions affecting customers | `OBL-MDL-01` | Blocker | Oversight design |
| `REG-MDL-005` | Explainability sufficient for the decision's consequence and for customer challenge | `OBL-MDL-01` | Major | Explainability approach |
| `REG-MDL-006` | Fairness and bias assessment where outcomes affect customer access, pricing or treatment | `OBL-MDL-02` | Major | Fairness assessment |
| `REG-MDL-007` | AI risk classification and transparency obligations addressed | `OBL-MDL-02` | Major | Classification record |
| `REG-MDL-008` | Training and inference data provenance, rights to use, and whether organisation data trains a shared model | `OBL-DAT-01` | Blocker | Data provenance statement |

## Time and records

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `REG-REC-001` | Records retention obligations identified per record type | `OBL-DAT-03` | Major | Retention mapping |
| `REG-REC-002` | Immutability where records rules require it | `OBL-DAT-03` | Blocker (if in scope) | Immutability design |
| `REG-REC-003` | Communications or customer instructions captured where required | `OBL-DAT-03` | Major | Capture statement |
| `REG-REC-004` | Timestamp granularity and clock divergence meet the obligation | `OBL-TIM-01` | Blocker (if in scope) | Clock sync evidence |

## Contradiction checks

- A new SaaS provider in the critical path, described as a technical decision, with no
  supplier classification and a go-live date sooner than the notification lead time.
- A cloud exit plan asserted as "we could redeploy elsewhere", while the design uses several
  proprietary managed services with no extraction path for the data.
- An impact tolerance stated in minutes, with a dependency whose contractual restoration
  commitment is longer.
- Personal data processed by a third party, with the data protection agreement listed as an
  action after go-live.
- A model making customer-affecting decisions, described as a rules engine to avoid model
  governance.

## Questions the board will ask

- Is this a critical supplier, and who has classified it?
- If this provider failed tomorrow, what would we do, and how long would it take?
- Which of our other critical services depend on the same thing?
- Can we evidence this control to an auditor in two years?
- Who declares a reportable incident, and can we meet the notification deadline?
- Has Compliance seen this, and what did they say?

## Do not raise

- Any regime whose `Applies` value is not `yes`.
- Legal interpretation, contract drafting, or advice on regulatory intent.
- Technical control detail already covered by `SEC`, `DAT` or `RES`. Reference the finding
  and add only the obligation and evidence angle.
