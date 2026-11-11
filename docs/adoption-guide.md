# Adoption Guide — taking the pre-flight review live in your organisation

The sequencing, who does what, and how to prove it works. The mechanics of writing clauses
and rules are in `skill/arb-preflight/AUTHORING.md`; this document is the programme
around them.

---

## 1. What adoption actually means

Not "install the skill". The skill is already complete. Adoption means three things:

1. **Your own policy is in the standards corpus and confirmed by the people who own it.**
   Until then the review cites provisional defaults, and findings are capped.
2. **The review teams recognise their own checklist in the rubric.** Until then it is a tool
   done to them rather than one they use.
3. **Findings are tracked as data, not as meeting minutes.** Until then nobody can answer
   which conditions from the last four boards are still open.

Everything below serves those three.

---

## 2. Confirm before you author

The instinct is to write new rules. The higher-leverage move is to confirm the clauses that
already exist.

Every clause in `standards/` carries one of three states, and the reviewer behaves
differently in each:

| State | Reviewer behaviour |
|---|---|
| `[CONFIRMED yyyy-mm-dd by <role>]` | Assessed normally, full severity available including Blocker |
| `[DEFAULT — CONFIRM]` | Assessed, **severity capped at Major**, findings labelled `provisional standard` |
| `[TBD]` | Not assessed. Dependent rules report `Insufficient information — standard not populated` |

Run the skill once against a real submission with the starter defaults and look at which
Majors are labelled `provisional standard`. Typical examples: a disaster RTO the topology
cannot achieve, an RPO looser than the tier permits, a single-AZ data store, backups inside
the workload account, no data classification, no threat model. Confirming the baselines
**as already written** turns those into Blockers.

That is a signature, not an authoring exercise, and it roughly doubles the review's teeth.

### Compliance's minimum useful contribution

Smaller than they will expect. In `standards/obligations-register.md`:

1. Set `Applies` per legal entity for the regimes that bind the entity in question.
2. Populate the `Internal control` column for the obligations the designs actually touch.

Typically that is a handful of rows, and it converts most of the regulatory domain from
unassessable to assessable. Without it the `REG` domain returns almost nothing graded.

This file is also the only place in the skill where the name of a regulation may appear. The
reviewer is constrained from citing any regime not marked `yes` and from naming any
regulation not reproduced there. Preserve that discipline: it is why the regulatory findings
are defensible rather than a model's recollection of regulation.

---

## 3. Getting existing policy in

Your policy probably lives in Word, a wiki and slide decks, not in clause form. Do not
hand-transcribe.

**The workflow:**

1. Drop the source policy documents into a folder.
2. Convert one source document into one standards file at a time:

   ```
   Read <policy-document> and convert its architecturally-relevant requirements into
   clauses for standards/landing-zone-baseline.md. Use the existing ID scheme and section
   structure. One clause per testable requirement. Mark every clause [TBD] — I will confirm
   them individually. Quote the source section for each clause so I can verify it. Do not
   invent requirements the document does not state, and do not merge two requirements into
   one clause.
   ```

3. **The owning function reviews every clause and moves it from `[TBD]` to `[CONFIRMED]`
   individually.** This step cannot be delegated to the agent, and it is where the authority
   comes from. A clause nobody read is worse than no clause, because it produces confident
   findings with nothing behind them.
4. Only then add rules citing the confirmed clauses.

Two guardrails to state up front: requirements that cannot be tested from a design document
do not become clauses — they belong in build or operate controls. And requirements the source
states as guidance rather than mandate must be marked as such, because a rule citing guidance
as mandatory will be rejected the first time it fires.

---

## 4. Calibration, the loop that makes the rubric good

Rules written in a room are guesses. Rules calibrated against real submissions are assets.
Run this for the first three or four reviews.

1. Run the review against a submission that **already went through the board**.
2. Put the tool's findings beside the findings the board actually raised.
3. Work three lists:

| Gap | Action |
|---|---|
| Board raised it, tool missed it | Add a rule, or fix the evidence requirement on the rule that should have caught it |
| Tool raised it, board would not have | Lower the severity, or add it to the rubric's `Do not raise` list |
| Tool raised it, board missed it | Keep it. This is the value. Tell the review team |

4. Ask each review team to read **its own rubric file** once, annotate it, and hand it back.
   Thirty minutes each. It converts them from audience into co-authors, which is the
   difference between adoption and shelfware.

Track `unassessable per submission` over time. If it is not falling, either the standards are
not being populated or the intake gate is not being enforced.

---

## 5. Who does what

| Activity | Accountable | Consulted | Cadence |
|---|---|---|---|
| `criticality-tiering.md` content | Operational Resilience / Business Continuity | Business owners | Annually |
| `landing-zone-baseline.md` content | Cloud Platform Engineering | Security, Network | Quarterly |
| `security-baseline.md` content | Security Architecture | Platform | Quarterly |
| `obligations-register.md` and applicability | Compliance / Risk | Legal | On regulatory change |
| `tech-radar.md`, `pattern-catalog.md` | Enterprise Architecture | All | Quarterly |
| Rubric maintenance | Governance function | The review teams | Continuous |
| Running reviews | Delivery teams (self-service) or governance (gate) | — | Per submission |
| Decisions and conditions | The board | — | Per board |
| Condition tracking from `findings.json` | Board secretariat | — | Continuous |
| Reviewing the tool itself | Security function | — | Once, before real designs |

**The single most important commitment: each standards file has a named owner who keeps it
current.** An out-of-date baseline produces confident wrong findings, which is worse than no
tool at all.

---

## 6. First four weeks

| Week | Who | What | Done when |
|---|---|---|---|
| 1 | Operational Resilience | Confirm `criticality-tiering.md` | Tier matrix signed and dated |
| 1 | Governance | Calibrate against three past submissions | Three gap lists produced |
| 1 | Security | Review the tool itself and the model endpoint | Written sign-off to use it on real designs |
| 2 | Cloud Platform, Security Architecture | Bulk-import their baselines, confirm clause by clause | Clauses moved off `[TBD]` |
| 2 | Compliance | Set `Applies` per entity; populate internal control IDs for the obligations in play | Relevant rows populated |
| 3 | Each review team | Read and annotate its own rubric file | Seven annotated files returned |
| 3 | Governance | Merge annotations; adjust severities | Rubric v1.1 |
| 4 | Governance | Re-run the three calibration submissions | Verdict changes explained |
| 4 | Governance + board chair | Agree the operating model (below) and the baseline metrics | Model chosen, baseline captured |

Weeks 1 and 2 need one table, three old submissions and a security review. That is the whole
entry cost, and it is worth doing before committing to anything larger.

---

## 7. Operating model, chosen in week 4

**Gate model.** The governance function runs the pre-review and a submission does not reach
human reviewers until it clears the intake gate. Stronger control, and it positions the tool
as an inspection.

**Self-service model.** Delivery teams run it themselves, as often as they like, while
writing the HLD. Weaker control, considerably better outcomes, because teams fix findings
before anyone else sees them.

**Recommendation: start self-service, add the gate once the standards corpus is confirmed.**
Most of the value is in authoring-time use. A gate on a provisional standards corpus produces
arguments about the tool rather than fixes to the design.

---

## 8. Measuring it

Capture the first three **before** the pilot. Without a baseline the improvement is an
anecdote.

| Measure | Why | Source |
|---|---|---|
| First-pass board approval rate | The headline outcome | Board records |
| Review rounds per submission | Where the calendar goes | Governance records |
| Elapsed time submission to board decision | What the business feels | Governance records |
| Specialist reviewer hours per submission | Where expert time goes | Estimate from the teams |
| Blockers found pre-review vs at the board | Whether findings are moving earlier | `findings.json` |
| Unassessable rules per submission | Submission quality and standards coverage | `findings.json` |
| Conditions still open after 90 days | Governance hygiene, historically invisible | `findings.json` |
| Recurring findings across the portfolio | Points at a standards or enablement gap, not a team problem | `findings.json` |

The last one is the sleeper. Once several reviews exist, the findings data tells you where
to fix your standards and where to fix your engineering enablement, which is worth more than
any single review.

---

## 9. Harvest from the first reviews

A useful by-product: when a reviewer finds a genuine concern with no matching rule, it comes
out as `Advisory` with rule ID `NONE` plus a proposal for the clause that should exist. That
is the mechanism telling you where your policy has gaps.

Examples of the kind of proposals that typically come out of early reviews:

| Proposed clause | Gap it covers | Owner |
|---|---|---|
| `SB-IAM-09` | Non-human worker identity governance: every bot, automation or AI agent has a named accountable human owner, entitlements recertified on the human cycle, and attributable actions | Security Architecture |
| `SB-THR-07` | A legacy path retained for rollback must meet the target's control baseline, be monitored, and carry a dated decommission commitment | Security Architecture |
| `LZB-PRV-06` | Transient migration stores holding production data must use the source key class, restrict access to the migration role, and be deleted on cutover with evidence | Cloud Platform Engineering |
| `RES-CHG-001` | For a migration of a live service: the rollback point, the maximum live period before rollback becomes unsafe, and the treatment of data written after cutover must be stated | Operational Resilience |

Raise these in week 3 alongside the rubric annotations. They land well because they came out
of your own submissions rather than from a template.

---

## 10. Pitfalls

| Pitfall | Why it happens | Counter |
|---|---|---|
| Reviewers treat findings as authoritative and stop thinking | The report is confident and well formatted | Position it as the checklist pass, not the review. Outputs state confidence and never claim approval |
| The standards corpus goes stale | No named owner, no cadence | Owner and review cadence per file; provisional clauses labelled in every finding |
| Teams write to the rubric rather than designing well | The rubric is published | Deliberate. A team writing a threat model to satisfy `SEC-THR-001` has written a threat model. Quality is still judged by humans |
| False positives erode trust | Rubric not yet calibrated | Run §4 for the first three reviews. Every finding carries evidence and a confidence level |
| Someone renames a rule or clause ID | Tidying instinct | Never rename or reuse. `findings.json` records IDs; renaming breaks re-review diffing and orphans history. Supersede instead |
| The tool is adopted before your security function has reviewed it | Enthusiasm | Make that review a week 1 deliverable |
| Findings pile up with no owner | No named business or production owner on the submission | The intake gate raises it; hold the line |

---

## 11. Adoption is done when

- Every standards file has a named owner and no `[TBD]` in the sections your designs
  actually touch.
- `criticality-tiering.md` and the obligations register applicability are confirmed.
- Each of the seven review teams has read and annotated its rubric.
- Three calibration reviews have been run and severities adjusted.
- The three baseline metrics are captured.
- Your security function has signed off the tool and the model endpoint.
- One real submission has gone through pre-review, remediation, re-review and the board,
  with conditions tracked from `findings.json`.

That last line is the real test. Everything before it is preparation.
