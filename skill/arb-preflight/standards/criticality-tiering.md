# Criticality Tiering and Resilience Obligations

Status: `[DEFAULT — CONFIRM]` — owned by Operational Resilience / Business Continuity.

This is the highest-leverage file in `standards/`. Once the tier is known, the resilience
targets are not negotiable and not a matter of design opinion. Most board pushback is a
design asserting an RTO its tier does not permit, or claiming a tier its business impact
does not support.

## Tier definitions

| Tier | Definition | Typical examples |
|---|---|---|
| 1 | Supports a critical business service. Outage causes intolerable harm to customers, revenue, safety, or the organisation's legal or regulatory standing. Payments, orders or records of legal effect in the path. | Checkout and payments, order management, core transaction systems, customer-facing channels, identity provider |
| 2 | Material business disruption. Workarounds exist but degrade quickly. Statutory or contractual deadlines at risk. | Statutory reporting, fulfilment, customer onboarding, customer servicing |
| 3 | Internal disruption, absorbable for a working day. | Internal reporting, workflow tooling |
| 4 | Minimal impact. | Sandboxes, internal utilities, non-prod |

## Resilience matrix

| Requirement | Tier 1 | Tier 2 | Tier 3 | Tier 4 |
|---|---|---|---|---|
| `CT-AVL` Availability target | 99.99% | 99.9% | 99.5% | best effort |
| `CT-RTO` Recovery time objective | ≤ 15 min | ≤ 4 h | ≤ 24 h | ≤ 5 d |
| `CT-RPO` Recovery point objective | ≤ 1 min (zero for committed transactions) | ≤ 15 min | ≤ 4 h | ≤ 24 h |
| `CT-AZ` Availability zones | ≥ 3 AZ, active | ≥ 2 AZ, active | ≥ 2 AZ, active/passive | 1 AZ acceptable |
| `CT-REG` Multi-region | Required, warm standby minimum | Documented plan, pilot light minimum | Backup restore to second region | Not required |
| `CT-DR` DR pattern floor | Warm standby or active-active | Pilot light | Backup and restore | Backup only |
| `CT-TEST` DR test cadence, with evidence | Semi-annual, including failback and unannounced | Annual | Biennial | On change |
| `CT-BKP` Backup | Cross-region, immutable, restore-tested quarterly | Cross-region, restore-tested annually | Cross-region | In-region |
| `CT-DEP` Dependency tolerance | No single dependency may exceed the service's own impact tolerance | Degraded mode documented | Best effort | n/a |
| `CT-CAP` Capacity headroom at forecast peak | ≥ 100% | ≥ 50% | ≥ 25% | n/a |
| `CT-CHG` Change approval | Board plus resilience sign-off | Board | Domain architect | Team |
| `CT-EXIT` Cloud exit / substitutability plan | Required and tested | Required | Documented | Not required |

## Impact tolerance (`CT-IMP`)

Tier 1 and 2 solutions supporting a critical business service must state an **impact
tolerance**: the maximum tolerable duration and extent of disruption, expressed in
business terms, not technical ones. "15 minute RTO" is a technical target. "No more than
30 minutes during the peak sales window, and no lost or duplicated orders" is an impact
tolerance. The board expects the second, and the design must show it can be met including
under the failure of its largest single dependency.

`[TBD]` — link the organisation's critical business service register here so the reviewer
can check the claimed tier against the registered service.

## Rules for the reviewer

- Tier claimed but not evidenced against the definitions above → `RES-TIER-002`.
- RTO/RPO stated that is looser than the matrix requires for the claimed tier →
  `RES-TIER-003`, Blocker. Not a design trade-off; it is a policy breach.
- RTO/RPO stated that the topology cannot deliver, for example a 15 minute RTO with a
  manual multi-hour restore, or an RPO of 1 minute with nightly snapshots →
  `RES-DR-002`, Blocker. This is the single most common finding at an ARB.
- Tier 1 with no DR test evidence → `RES-DR-005`, Blocker.
- Tier inflation or deflation both matter. A design claiming tier 3 while sitting in a
  payment or order path is understating its obligations; say so.
