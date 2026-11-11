# Rubric — Resilience & Capacity (`RES`)

Standards: `standards/criticality-tiering.md` (primary),
`standards/obligations-register.md` (`OBL-RES-*`).

## How to review this domain

This domain generates more board rework than any other, for one reason: teams state a
recovery target and then draw an architecture that cannot deliver it. Review in this order.

1. Establish the tier. Everything downstream depends on it, and a tier claimed without
   assessment is worthless.
2. Read the RTO/RPO the design claims.
3. Read the matrix in `criticality-tiering.md` and check the claim is permitted.
4. Then, and this is the part that matters, check the topology can actually deliver it.
   Count the recovery steps. If any of them is manual, ask how long it takes at 3am on a
   Sunday with the primary region unavailable and the person who wrote the runbook on
   leave. Compare that to the stated RTO.
5. Find the single points of failure the diagram hides: one NAT, one database writer with
   a manual promote, one Direct Connect, one third party, one region, one shared component
   that other tier 1 systems also depend on, one person.

An untested DR plan is not a DR capability. Treat evidence of a test as the control, and
the document as a claim about it.

## Tiering

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `RES-TIER-001` | Criticality tier is stated | intake | Blocker | Tier in the submission or from intake |
| `RES-TIER-002` | Tier is evidenced against the tier definitions, not asserted | `CT-*` | Major | Impact assessment |
| `RES-TIER-003` | Stated RTO/RPO/availability meet or beat the matrix for the claimed tier | `CT-RTO`, `CT-RPO`, `CT-AVL` | Blocker | NFR section |
| `RES-TIER-004` | Tier is consistent with the business function; no understatement to avoid obligations | `CT-*` | Blocker | Business context vs tier |
| `RES-TIER-005` | Impact tolerance stated in business terms for tier 1 and 2 | `CT-IMP`, `OBL-RES-01` | Blocker (T1/T2) | Impact tolerance statement |

## High availability

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `RES-HA-001` | AZ spread meets the matrix for the tier | `CT-AZ` | Blocker | Deployment view |
| `RES-HA-002` | No single point of failure in the critical path, or each is named with its justification | `CT-DEP` | Blocker | Topology and SPOF analysis |
| `RES-HA-003` | Database failover mechanism named, automatic where the RTO requires it, with the failover time stated | `CT-RTO` | Blocker | Data tier design |
| `RES-HA-004` | Stateless compute, or session state externalised so instance loss is survivable | — | Major | Compute design |
| `RES-HA-005` | Health checks and automatic replacement of unhealthy instances | — | Minor | Operational design |
| `RES-HA-006` | Deployment can proceed without downtime, or the maintenance window is agreed with the business | — | Major | Release approach |

## Disaster recovery

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `RES-DR-001` | DR pattern named explicitly: backup-restore, pilot light, warm standby, or active-active | `CT-DR` | Blocker | DR section |
| `RES-DR-002` | The topology can actually deliver the stated RTO and RPO; recovery steps are counted and timed | `CT-RTO`, `CT-RPO` | Blocker | Recovery sequence with timings |
| `RES-DR-003` | Multi-region posture meets the matrix for the tier | `CT-REG` | Blocker | Region strategy |
| `RES-DR-004` | Failback is designed, not just failover, including data reconciliation after divergence | `OBL-RES-02` | Major | Failback procedure |
| `RES-DR-005` | Evidence of DR testing at the required cadence, including the date of the last test and its outcome | `CT-TEST`, `OBL-RES-02` | Blocker (T1) | Test evidence |
| `RES-DR-006` | Recovery does not depend on a component that shares the failure domain it recovers from | `CT-DEP` | Blocker | Dependency analysis |
| `RES-DR-007` | The decision to invoke DR has a named owner and a defined trigger | `OBL-RES-01` | Major | Invocation criteria |
| `RES-DR-008` | Quotas, limits and capacity reservations exist in the DR region; capacity is not assumed available | `CT-REG` | Major | DR capacity statement |

## Backup

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `RES-BKP-001` | Backup scope, frequency and retention stated per data store, aligned to the RPO | `CT-BKP` | Major | Backup section |
| `RES-BKP-002` | Backups are cross-region and immutable where the tier requires it | `CT-BKP` | Major | Backup design |
| `RES-BKP-003` | Restore has been tested, with the measured restore time recorded | `CT-BKP` | Blocker (T1/T2) | Restore test evidence |
| `RES-BKP-004` | Backups survive compromise of the workload account: separate account, separate credentials, no delete permission from the workload | `LZB-GRD-02` | Blocker | Backup isolation |
| `RES-BKP-005` | Ransomware and logical-corruption recovery considered, not only infrastructure loss | `CT-BKP` | Major | Recovery scenarios |

## Dependencies and concentration

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `RES-DEP-001` | Every upstream and downstream dependency is listed with its own criticality and availability | `OBL-RES-03` | Major | Dependency map |
| `RES-DEP-002` | No dependency has a weaker resilience posture than the service that relies on it, or the gap is accepted explicitly | `CT-DEP` | Blocker | Dependency comparison |
| `RES-DEP-003` | Degraded mode defined for each dependency failure: what the service still does when it is down | `CT-DEP` | Major | Degradation design |
| `RES-DEP-004` | Timeouts, retries with backoff and jitter, circuit breakers, and bulkheads at each integration | — | Major | Resilience patterns |
| `RES-DEP-005` | Retry design cannot amplify an outage into a self-inflicted denial of service, or duplicate a payment, order or other side-effecting action | — | Major | Retry and idempotency statement |
| `RES-DEP-006` | Concentration risk assessed: shared components, shared region, shared provider across other critical services | `OBL-TPR-03` | Major | Concentration statement |
| `RES-DEP-007` | Key-person and key-team dependencies in recovery are identified | `OBL-RES-03` | Minor | Support model |

## Capacity and performance

| ID | Check | Standard | Severity | Evidence needed |
|---|---|---|---|---|
| `RES-CAP-001` | Expected volumes stated: average, peak, and the business event that drives peak | intake | Major | Volumetrics |
| `RES-CAP-002` | Business peaks named where relevant: seasonal sales events, product launches, marketing campaigns, month and quarter end, batch and billing runs, statutory reporting deadlines | `CT-CAP` | Major | Peak analysis |
| `RES-CAP-003` | Headroom at forecast peak meets the matrix | `CT-CAP` | Major | Capacity plan |
| `RES-CAP-004` | Latency and throughput targets stated where the business depends on them | intake | Major | NFR section |
| `RES-CAP-005` | Performance and load testing planned at realistic peak before go-live | intake | Major | Test plan |
| `RES-CAP-006` | Scaling mechanism stated, with its lag; scaling must be faster than the load ramp it serves | — | Major | Scaling design |
| `RES-CAP-007` | Throttling, queueing and backpressure protect downstream systems, especially slower legacy ones | — | Major | Flow control design |
| `RES-CAP-008` | Growth horizon stated, with what breaks first beyond it | — | Minor | Capacity outlook |

## Contradiction checks

The strongest findings in the whole review usually come from this list.

- Tier 1 with a single-AZ or single-region component in the critical path.
- A 15 minute RTO with a restore-from-backup DR pattern.
- An RPO near zero with asynchronous cross-region replication and no reconciliation.
- 99.99% availability claimed while depending on an internal system with a 99.5% SLA.
- Active-active claimed, with a single writer database.
- A DR region named, with quotas, capacity or third-party connectivity that exists only in
  primary.
- DR test evidence described as "planned" for a service already in production.
- Automatic failover claimed, with a runbook that begins "raise an incident and page the
  DBA".

## Questions the board will ask

- What tier, and who assessed it?
- When did you last fail over, and did you fail back?
- Which single component, if it fails, takes the whole service down?
- Your RTO is 15 minutes. Walk me through the 15 minutes.
- If your largest dependency is unavailable for four hours, what does the customer see?
- Do you have capacity reserved in the DR region, or are you hoping?
- What happens on your biggest sales day when volume triples?

## Do not raise

- Cost of the DR posture; that belongs to `OPS`.
- Transaction-level integrity, ordering and reconciliation; that belongs to `INT`.
- Regulatory framing of resilience obligations; that belongs to `REG`. Findings here are
  about whether the architecture works, not about which rule requires it.
