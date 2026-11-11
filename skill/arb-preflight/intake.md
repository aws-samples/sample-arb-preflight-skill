# Intake Gate

Run this before any review. Its purpose is to stop a thin submission from consuming a
full seven-domain review and producing seven domains of "not stated".

## Metadata to capture

Record these in the report header. Ask the user for anything absent; do not infer.

| Field | Why it matters | If missing |
|---|---|---|
| Application / solution name | Report path, re-review continuity | Ask |
| Business owner and technical owner | Findings need owners | `NOT STATED`, raise `OPS-GOV-001` |
| Criticality tier | Drives RTO/RPO/HA expectations for the whole review | Ask; else tier `UNKNOWN` + `RES-TIER-001` Blocker |
| Data classes handled | Drives the data and regulatory domains | Ask; else `DAT-CLS-001` Blocker |
| Regulatory footprint (entities, jurisdictions) | Selects obligations from the register | Ask; else review `REG` domain as unassessable |
| Change type | New build / material change / migration / uplift | Ask |
| Target go-live date and ARB date | Sequencing of remediation | `NOT STATED` |
| Prior ARB history | Conditions carried from a previous review | Check `reviews/<app>/` |
| Submission version / date | Re-review diffing | Ask |

## Mandatory artefacts

Absent any of these, the outcome is `Insufficient information` and the review stops
at the gate.

1. **Solution overview** — business purpose, scope, in/out of scope.
2. **Logical architecture diagram** — components and their relationships.
3. **AWS deployment view** — accounts, regions, VPCs, subnets, ingress and egress
   paths, and where the workload sits relative to the landing zone.
4. **Data view** — what data, what classification, where it rests, where it moves,
   including cross-border movement.
5. **Integration list** — every counterparty system, direction, protocol, and whether
   it is in-domain, another internal domain, or a third party.
6. **Non-functional requirements** — at minimum availability target, RTO, RPO, and
   expected volumes with peak.

## Expected, and usually missing

Not gate-blocking on their own, but each absence is a finding. This list is where most
board pushback originates.

- Criticality tier assessment with the RTO/RPO derived from it, not asserted.
- Threat model or security design section naming trust boundaries.
- Identity model: human access, machine-to-machine auth, privileged access.
- Segregation of duties statement: who deploys, who approves, who can reach prod data.
- DR strategy with a stated pattern (backup-restore / pilot light / warm standby /
  active-active) and evidence of a test, including failback.
- Dependency map with criticality of each upstream and downstream.
- Observability: SLIs, SLOs, alert routing, log retention.
- Third-party / supplier classification, plus an exit / substitutability plan.
- Reconciliation and audit-trail design where payments, orders, balances, or customer
  records move.
- Decommissioning plan for whatever this replaces.
- Cost estimate with the run-rate owner.

## Thin-submission heuristics

From `extracted/manifest.json`:

- Fewer than 10 slides, or under 800 words, for a tier 1 or 2 solution → almost
  certainly cannot be assessed. Check the mandatory artefact list explicitly and
  expect to fail the gate.
- No viewable diagram → fail the gate. Raise `LZ-DOC-001`. A topology described only
  in prose cannot be reviewed for network conformance, and the board will not accept
  it either.
- Diagrams present only as EMF/WMF/SVG → request PNG re-export, raise `LZ-DOC-002`.
  Do not guess at a topology you could not see.

## Gate output when it fails

Keep it short and actionable. The submitting team should be able to act on it the same
day.

```markdown
## Intake — Insufficient information

**Submission:** {name} v{version}, {n} slides / {m} words, {k} viewable diagrams
**Assessed against:** intake.md mandatory artefact list

### Missing mandatory artefacts
| # | Artefact | Consequence for the board |
|---|---|---|
| 1 | AWS deployment view | Landing-zone conformance cannot be assessed at all |

### Missing metadata
{list, with who to ask}

### Recommendation
Return to the submitting team before booking board time. Re-submit with the items above;
re-review turnaround is same-day.
```
