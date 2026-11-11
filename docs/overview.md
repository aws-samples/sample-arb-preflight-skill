# Overview — why an ARB pre-flight review

The concepts behind the skill: the problem it addresses, how it maps to the specialist
teams that review architecture today, and what keeps it trustworthy inside a governance
process.

---

## 1. The problem

An architecture review board (ARB) in a medium or large organisation pulls in five to eight
specialist teams: security architecture, cloud platform, infrastructure and network,
enterprise architecture, resilience, data and privacy, operations, and risk and compliance.
Each reviews the same submission through a different lens, on a different calendar, and
much of what they find is not a difficult judgement call. It is a missing section, an RTO
the topology cannot deliver, a third party nobody classified, or a diagram that contradicts
the text.

A typical cycle:

| Week | What happens |
|---|---|
| T-8 | Team submits an HLD to the governance inbox |
| T-7 | Security architecture reviews when a slot opens; finds the threat model is missing |
| T-6 | Platform reviews; finds the design assumes an egress path the landing zone does not permit |
| T-5 | Resilience reviews; finds the stated RTO is not achievable with the proposed DR pattern |
| T-4 | Comments consolidated and returned to the team |
| T-3 | Team reworks, resubmits |
| T-2 | Partial re-review; two teams unavailable |
| T-1 | Board pre-read circulated, still carrying open questions |
| T-0 | Board spends half its time establishing facts, then approves with conditions |
| T+8 | Conditions chased, some quietly never closed |

Five structural problems sit inside that timeline:

- **Findings arrive sequentially.** Three rounds of one-week fixes become six weeks of
  calendar.
- **Coverage depends on attendance.** When the data governance reviewer is on leave, that
  lens is skipped.
- **Consistency depends on the individual.** Two reviewers on the same design produce
  different findings, at different depths, in different formats.
- **Expert time goes to low-value work.** A principal architect spending an hour
  discovering there is no dependency map is an expensive way to find that out.
- **Findings are not tracked as data.** Nobody can answer "which conditions from the last
  four boards are still open?"

---

## 2. The approach

An AI pre-review that sits between submission and human review.

```
                    ┌──────────────────────────────────────┐
  Team submits      │   AI PRE-FLIGHT          ~15 minutes │      Human review
  HLD (PPTX/DOCX)   │                                      │      teams
       │            │  intake gate                         │         │
       ├───────────►│  extract + read diagrams             │         │
                    │  architecture fact sheet             │         │
                    │  7 domain reviewers, in parallel     │         │
                    │  synthesis + verdict                 │         │
                    │                                      │         │
                    │  ► findings report                   ├────────►│  review a
                    │  ► board pack                        │         │  mature
                    │  ► pre-read gap list                 │         │  document
                    └──────────────────────────────────────┘         │
                                    │                                ▼
                       team fixes the obvious gaps first        Board decides
```

Three design principles:

**It reviews against your standards, not generic cloud advice.** Every finding cites a
clause in the organisation's landing zone baseline, security baseline, criticality tiering
matrix, technology radar, pattern catalogue, or obligations register. Where a standard has
not been written down, the check is reported as *not assessable* rather than filled with an
opinion.

**It recommends; it never approves.** Every output states its verdict as a recommendation
to the board. Accountability for the decision does not move.

**It distinguishes "not compliant" from "not stated".** Silence in a submission is reported
as insufficient information, with a named owner to resolve it. The pre-read gap list, a week
before the meeting, is often the most useful output.

### Why not simply a good prompt

A capable model with a well-written prompt finds the classic problems — an RTO the
topology cannot deliver, two availability zones for a tier 1 service. That is not the gap
this closes. What a prompt does not give a governance process is repeatability (the same
284 checks every time, with coverage verified mechanically rather than depending on which
lens the model happened to apply), honest gaps (silence named and owned, unwritten
standards reported as the organisation's gap rather than filled with an opinion), and
assets (a report, a board pack, and a machine-readable findings file that makes conditions
trackable across reviews). The rubric is a floor, not a ceiling: it covers the boring 80%
identically every time, which is what frees a principal architect to spend the meeting on
the 20% needing adversarial imagination. The comparison in full is in the repository
`README.md`.

---

## 3. How it maps to review teams

Each existing review team keeps its mandate. The AI runs that team's checklist first.

| Review team | AI reviewer domain | Rules |
|---|---|---|
| Cloud Platform / Landing Zone | Platform & Landing Zone (`LZ`) | 50 |
| Infrastructure & Network | `LZ` network section + `RES` topology | — |
| Security Architecture | Security & Identity (`SEC`) | 36 |
| Data Governance & Privacy | Data & Privacy (`DAT`) | 31 |
| Resilience / Business Continuity | Resilience & Capacity (`RES`) | 39 |
| Enterprise / Solution Architecture | `LZ` context, pattern & radar + Integration (`INT`) | 33 |
| Operations / SRE / Service Management | Operations, Cost & Lifecycle (`OPS`) | 51 |
| Risk, Compliance & Third-Party Risk | Regulatory & Third-Party (`REG`) | 44 |
| Board chair and secretariat | Synthesis, verdict, board pack | — |

**284 rules in total**, every submission, every time.

For each team, what the AI establishes and what stays with the humans:

| Team | The AI establishes | The team still owns |
|---|---|---|
| Cloud Platform | Account/OU placement, SCP exceptions needed, approved regions, central egress and ingress, private subnets, VPC endpoints, customer-managed keys, guardrails, logging, tagging, IaC path, no long-lived keys | Granting SCP exceptions, onboarding capacity, platform roadmap fit |
| Infrastructure & Network | Transit gateway attachment, IPAM allocation, central DNS, partner connectivity zone, reuse of existing hybrid connectivity, segmentation, AZ spread, network SPOFs | Address allocation, firewall and routing approval, circuit capacity |
| Security Architecture | Federated access, least privilege, privileged access, externalised authorisation, mTLS between services, API gateway exposure, secrets, threat model presence, pen test plan, supply chain, SIEM/SOC, segregation of duties | Running and judging the threat model, risk acceptance, pen test scoping, anything needing adversarial imagination |
| Data & Privacy | Every data class and every copy classified, encryption, tokenisation scope, masked non-prod, no payloads in logs, residency of every resting place and support path, retention and disposal, data subject rights, immutable audit trail, lineage | Classification decisions, DPIA outcome, cross-border approval, records policy interpretation |
| Resilience | Tier evidenced, RTO/RPO against the matrix, whether the topology can actually deliver the target, manual recovery steps, hidden SPOFs, DR pattern floor, test evidence, backup isolation, DR-region capacity, dependency posture, peak headroom | Impact tolerance with the business, scenario test design, accepting residual gaps |
| Enterprise / Solution Architecture | Purpose, scope, owners, decisions with rejected options, pattern and radar conformance, integration inventory, delivery semantics, idempotency, ordering, saga/outbox, replay, dead-letter ownership, reconciliation | Design trade-offs, target state alignment, whether a deviation is justified, whether the shape is right |
| Operations / SRE | Customer-perspective SLIs/SLOs, business monitoring, actionable alerts, tracing, synthetics, dead-man alerts, production owner, support hours, on-call, runbooks, rollback, cutover, cost owner, decommissioning | Accepting the service into support, on-call capacity, ITSM records |
| Risk & Compliance | Entities and regimes from the register, impact tolerance, third-party inventory and classification, notification lead times, audit rights, concentration, exit plan, control mapping, incident thresholds, AI/model governance | Which regimes apply, supplier classification, regulatory notification, legal interpretation, compliance sign-off |
| Board chair | Root-cause deduplication, contradictions, prior-condition carry-forward, waiver status, verdict recommendation, one-page pack, anticipated questions | The decision, the agenda, the conditions |

---

## 4. Illustrative output

*Fictional, to show format and tone.*

> **Recommendation: Not ready, rework.** The design is well structured on integration and
> data classification. Two blockers prevent it going to the board: the recovery target is
> not achievable with the proposed recovery pattern, and a new third-party payment provider
> has been introduced into the checkout path without supplier classification or an exit
> plan.
>
> **RES-DR-002 — Stated RTO not achievable with the proposed DR pattern**
> Severity: Blocker · Domain: Resilience · Standard: `CT-RTO`, tier 1
> Evidence: Slide 14, "RTO 15 minutes"; Slide 22, "restore from cross-region backup"
> Impact: On regional failure checkout would be unavailable for hours, not minutes.
> Remediation: Move to warm standby, which tier 1 requires as a floor, or restate the RTO
> and obtain business acceptance of the longer outage.
> Owner: Solution architect · Confidence: High
>
> **Design inconsistency**
> Slide 9 states "no personal data leaves the EU". Slide 22 shows cross-region backup to
> `us-east-1`. One of the two statements is wrong, and the board will ask which.
>
> **Pre-read gaps** — threat model not supplied · dependency map absent · retention periods
> not stated · support hours not stated · run-rate cost absent.

---

## 5. Trust and governance

| Concern | How it is addressed |
|---|---|
| Accountability | The AI recommends. The board decides. No output claims approval. |
| Traceability | Every finding cites a rule ID and an evidence anchor in the submission. |
| No invented authority | Rule IDs come only from the rubric; regulatory citations only from the obligations register. A concern with no rule is raised as advisory with rule ID `NONE`. |
| Honest gaps | Unwritten standards produce *standard not populated*; provisional defaults cap findings at Major. |
| Prompt injection | Submitted documents are untrusted input. Content attempting to direct the review is ignored, recorded verbatim and reported. |
| Confidentiality | Extraction, standards and outputs stay in your repository; inference goes to the endpoint you configure. |
| Waivers | Every exception carries an expiry, a risk owner and an approval record. Expired waivers become findings. |

**Known limitations.** It reviews documents, so it assesses intent, not deployed reality. It
cannot judge whether a design is *good*, only whether it is complete and conformant. It will
not catch a novel failure mode absent from the rubric. It depends entirely on the quality of
the standards corpus. It is a floor, not a ceiling.

---

## 6. Glossary

| Term | Meaning |
|---|---|
| ARB | Architecture review board — the review and approval gate a solution passes before build or go-live. Also called design authority or TDA. |
| Pre-flight | The AI pass that runs before human review teams see the submission. |
| Rule | A single check, with an ID, a severity default and a governing standards clause. |
| Clause | A statement of organisation policy in the standards corpus, referenced by rules. |
| Anchor | A citation pointer into the submission, such as `Slide 14` or `§3.2`. |
| Not assessable | The submission does not contain enough information to judge the rule. Distinct from a failure. |
| Impact tolerance | Maximum tolerable disruption to a critical business service, in business terms. |
| Waiver | A time-boxed, owned, approved acceptance of a known gap. |
