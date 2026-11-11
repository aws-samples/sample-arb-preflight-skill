# Rubric — Integration & Transaction Integrity (`INT`)

Standards: `standards/pattern-catalog.md`, `standards/obligations-register.md`
(`OBL-AUD-01`, `OBL-TIM-01`, `OBL-DAT-05`).

## How to review this domain

This is the domain that distinguishes a business-critical systems review from a general
cloud review. Availability failures are visible and get fixed. Integrity failures are
silent: a duplicated payment, a lost order, an inventory count out by one, a balance that
no longer reconciles. They are discovered by a customer, an auditor, or a regulator, and
they are the findings an ARB exists to catch.

For every asynchronous hop where something of value moves, ask four questions:

- What happens if this message is delivered twice?
- What happens if it arrives out of order?
- What happens if it is lost?
- How would we know that any of the above happened, and how long would it take?

"The queue guarantees delivery" is not an answer to the first two. At-least-once delivery
plus a non-idempotent consumer is a duplicate-payment defect waiting for a retry storm.
If the design's answer to detection is "the overnight reconciliation", that is acceptable
only if the business can tolerate discovering the break the next day, and the design should
say so explicitly.

## Integration inventory

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `INT-INV-001` | Every integration is listed with counterparty, direction, protocol, payload, volume and criticality | intake | Blocker | Integration table |
| `INT-INV-002` | Each integration is classified as in-domain, cross-domain internal, or third party | `OBL-TPR-01` | Major | Integration table |
| `INT-INV-003` | Synchronous and asynchronous interactions are distinguished on the diagram | — | Major | Sequence or flow diagram |
| `INT-INV-004` | Integration goes through the central integration or API layer where one exists; point-to-point is justified | pattern-catalog | Major | Rationale |
| `INT-INV-005` | Contracts are versioned with a compatibility and deprecation approach | — | Major | Interface governance |
| `INT-INV-006` | Schema ownership is clear, and consumers cannot be broken by an unannounced producer change | — | Major | Contract management |

## Transaction integrity

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `INT-TXN-001` | Delivery semantics stated per flow: at-most-once, at-least-once, or effectively-once | — | Blocker | Messaging design |
| `INT-TXN-002` | Idempotency designed wherever delivery is at-least-once and the action has an effect: idempotency key, its source, its scope, and how long it is retained | — | Blocker | Idempotency design |
| `INT-TXN-003` | Ordering requirements stated, and the mechanism that guarantees them where required, including how ordering survives partitioning and retry | — | Blocker | Ordering design |
| `INT-TXN-004` | Exactly-once is not claimed across a system boundary without a compensating control; distributed transactions are not assumed | — | Blocker | Integrity design |
| `INT-TXN-005` | State transitions across services use an explicit consistency approach: saga, outbox, two-phase business confirmation, with compensation defined for each step | pattern-catalog | Blocker | Consistency design |
| `INT-TXN-006` | Partial failure is designed for: what state the system is left in, and how it converges | — | Blocker | Failure handling |
| `INT-TXN-007` | Payments, orders, balances or customer records are never derived from a message alone without a durable authoritative record | `OBL-AUD-01` | Blocker | Ledger or record design |
| `INT-TXN-008` | Double-entry or equivalent balancing control where a ledger, wallet or stored-value balance is in scope | `OBL-AUD-01` | Major | Ledger design |
| `INT-TXN-009` | Replay is supported and safe: a message stream can be replayed without duplicating effects | — | Major | Replay design |
| `INT-TXN-010` | Poison messages and dead-letter handling defined, with who inspects the dead-letter queue and within what time | — | Major | Error handling |

## Reconciliation and break management

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `INT-REC-001` | Reconciliation exists between every pair of systems that hold the same business truth (payments, orders, stock, balances) | `OBL-DAT-05` | Blocker | Reconciliation design |
| `INT-REC-002` | Reconciliation frequency is proportionate to the value at risk and the tolerance for a late discovery | `OBL-DAT-05` | Major | Frequency and rationale |
| `INT-REC-003` | Breaks route to a named team with an investigation and resolution process, not to a dashboard nobody owns | — | Major | Break management process |
| `INT-REC-004` | Reconciliation is independent of the process it checks; it does not read the same single source | — | Major | Reconciliation sources |
| `INT-REC-005` | Completeness controls, not only accuracy: totals, counts, sequence gaps, expected-file-not-arrived | `OBL-DAT-05` | Major | Control design |
| `INT-REC-006` | Unmatched items age out into an escalation path with a materiality threshold | — | Minor | Escalation |

## Third-party and file interfaces

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `INT-3P-001` | Third-party endpoints are authenticated in both directions, with credential ownership and rotation stated | `SB-SEC-02` | Major | Interface security |
| `INT-3P-002` | Third-party unavailability has a defined behaviour: queue, degrade, or reject, with a stated business decision | `CT-DEP` | Major | Failure behaviour |
| `INT-3P-003` | File exchanges validate structure, completeness and authenticity before processing; malware scanning on inbound | `SB-SVC-04` | Major | File handling design |
| `INT-3P-004` | Duplicate file submission is detected and rejected | — | Major | File controls |
| `INT-3P-005` | Non-repudiation where a counterparty could dispute an instruction: signing, sequencing, or an evidential record | `OBL-AUD-01` | Major | Non-repudiation design |
| `INT-3P-006` | Cut-off times, timezones and business-day calendars are explicit | — | Major | Scheduling design |
| `INT-3P-007` | Late or missing inbound files are detected and escalated, not silently skipped | — | Major | Monitoring of expected inputs |

## Time and sequencing

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `INT-TIM-001` | Event timestamps come from a synchronised source with stated granularity; business time and system time are distinguished | `OBL-TIM-01` | Major | Timestamp design |
| `INT-TIM-002` | Clock synchronisation and maximum divergence stated where reportable events are timestamped | `OBL-TIM-01` | Blocker (if in scope) | Clock sync statement |
| `INT-TIM-003` | Sequence numbering or event versioning allows gap detection | — | Major | Sequencing design |
| `INT-TIM-004` | Timezone handling and daylight-saving transitions are explicit for scheduled and cut-off-sensitive processing | — | Minor | Scheduling design |

## Contradiction checks

- At-least-once delivery stated, with no idempotency anywhere in the consumer design.
- Ordering described as guaranteed, with multiple partitions or consumers and no partition
  key stated.
- Event-driven architecture with no dead-letter handling or replay story.
- A ledger described as the golden source, while a downstream cache serves customer-facing
  balances with no staleness bound.
- Real-time payment or order processing whose only integrity control is an overnight reconciliation,
  with no stated business acceptance of overnight discovery.
- Retries with backoff described alongside a non-idempotent downstream API.
- A third-party dependency in the critical path with no stated behaviour for its outage.

## Questions the board will ask

- If this message arrives twice, does the customer get charged twice?
- How do you know nothing was lost between these two systems, and how quickly?
- Who looks at the dead-letter queue, and by when?
- What reconciles against what, how often, and who works the breaks?
- If the third party is down for two hours at cut-off, what happens to in-flight instructions?
- Can you prove to a counterparty that we received their instruction at the time we say?
- Which of these flows can be replayed safely?

## Do not raise

- Message broker product preference, unless the radar rules on it.
- API style debates, REST versus events, unless a pattern or anti-pattern applies.
- Network-level integration controls; those belong to `LZ`.
