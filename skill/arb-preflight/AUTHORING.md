# Authoring Guide — adding and updating rules and policies

For the teams who own the content of this review. Read `standards/README.md` first for
ownership and the three clause states.

---

## 1. The two layers, and why they are separate

Everything in this skill sits in one of two layers. Putting content in the wrong layer is
the most common mistake and it is the one that erodes trust fastest.

| Layer | File | Contains | Owned by | Example |
|---|---|---|---|---|
| **Standard** | `standards/*.md` | A statement of *what the organisation requires*. Policy. | The function that owns the policy | `LZB-NET-02`: all egress routes through the central inspection VPC |
| **Rubric** | `rubric/*.md` | A statement of *how a reviewer checks it* against a document | The governance function running the review | `LZ-NET-002`: check the egress path on the deployment view; Blocker; evidence = egress path visible on a diagram |

**Policy never goes in the rubric.** If a reviewer cites a requirement that exists only in
`rubric/`, the submitting team can correctly say no such policy exists, and the finding
dies. Every rule must point at a clause someone with authority signed.

**Checking guidance never goes in the standards.** Cloud Platform Engineering should not
have to review prose about how to read a PowerPoint in order to approve a network policy.

---

## 2. Which one am I changing?

```
Something is missing from the review.
│
├─ Is the underlying requirement written down in standards/ ?
│  │
│  ├─ NO  → add a CLAUSE first (§3), then a RULE that cites it (§4)
│  │
│  └─ YES → is there a rule that checks it?
│           ├─ NO  → add a RULE only (§4)
│           └─ YES → the rule exists but did not fire. Fix the rule's
│                    evidence requirement or its wording (§7 calibration)
│
└─ Is it a judgement no checklist can make?
   → do NOT add a rule. Leave it to the human reviewer. See §8.
```

---

## 3. Adding or changing a clause in `standards/`

### 3.1 ID scheme

| File | Prefix | Format | Example |
|---|---|---|---|
| `landing-zone-baseline.md` | `LZB` | `LZB-<AREA>-<nn>` | `LZB-NET-11` |
| `security-baseline.md` | `SB` | `SB-<AREA>-<nn>` | `SB-IAM-09` |
| `criticality-tiering.md` | `CT` | `CT-<AREA>` | `CT-BKP` |
| `obligations-register.md` | `OBL` | `OBL-<AREA>-<nn>` | `OBL-TPR-05` |
| `pattern-catalog.md` | `PAT` | `PAT-<nnn>` | `PAT-004` |

Area codes are three letters. Reuse an existing area where one fits (`NET`, `IAM`, `KMS`,
`GRD`, `PRV`, `ACC`, `REG`, `SOD`, `SVC`, `SEC`, `THR`, `DET`, `DAT`, `RES`, `TPR`, `AUD`,
`INC`, `MDL`, `TIM`) rather than inventing a near-duplicate.

**Never reuse a retired ID and never renumber.** `findings.json` records clause IDs, so
renaming one silently breaks re-review diffing and makes historical findings untraceable.

### 3.2 Marking state

Every clause carries one of three states, and the reviewer behaves differently in each.

```markdown
| `LZB-NET-11` | Workload VPCs may not expose a database port to any on-premises range;
reporting access is served from a replica or an extract. | `[CONFIRMED 2026-03-14 by Head of Cloud Platform Engineering]` |
```

| Marker | Reviewer behaviour |
|---|---|
| `[CONFIRMED yyyy-mm-dd by <role>]` | Assessed normally. Findings cite it as mandatory. Full severity available, including Blocker. |
| `[DEFAULT — CONFIRM]` | Assessed, severity capped at Major, findings labelled `provisional standard`. |
| `[TBD]` | Not assessed. Dependent rules report `Insufficient information — standard not populated` with the standard's owner as the resolver. |

Confirming clauses is the single highest-leverage action available to an adopting
organisation. On a first review it is common to see a large share of the serious findings
held at Major purely because the governing clauses are still provisional. Confirming the
baselines as written turns those into Blockers.

### 3.3 Superseding rather than deleting

```markdown
| `LZB-NET-02` | ~~All egress routes through the central inspection VPC.~~ | `[SUPERSEDED BY LZB-NET-14 2026-06-01]` |
| `LZB-NET-14` | All egress routes through the regional inspection VPC for the account's home region. | `[CONFIRMED 2026-06-01 by Head of Cloud Platform Engineering]` |
```

Keep the old clause in place. Reviews written against it stay interpretable.

---

## 4. Adding or changing a rule in `rubric/`

### 4.1 ID scheme

`<DOMAIN>-<AREA>-<NNN>` — domain is **2 or 3 uppercase letters**, area is 2 to 4
alphanumerics, and the number is always three digits.

| Domain | Prefix | File |
|---|---|---|
| Platform & Landing Zone | `LZ` | `rubric/platform.md` |
| Security & Identity | `SEC` | `rubric/security.md` |
| Data & Privacy | `DAT` | `rubric/data.md` |
| Resilience & Capacity | `RES` | `rubric/resilience.md` |
| Integration & Transaction Integrity | `INT` | `rubric/integration.md` |
| Operations, Cost & Lifecycle | `OPS` | `rubric/operations.md` |
| Regulatory & Third-Party | `REG` | `rubric/compliance.md` |

Numbers are per area, sequential, and never reused. Take the next free number; do not
insert to keep a logical order.

The format is enforced by `templates/findings.schema.json`. A rule ID outside the pattern
`^([A-Z]{2,3}-[A-Z0-9]{2,4}-[0-9]{3}|NONE)$` will fail validation.

### 4.2 The row

Add one row to the appropriate table in the rubric file:

```markdown
| `LZ-NET-012` | No database port is reachable from an on-premises range; reporting reads from a replica or extract | `LZB-NET-11` | Blocker | Deployment view showing the reporting path, or an explicit statement |
```

Five columns, always: **ID · check · standard clause · severity default · evidence needed**.

The *evidence needed* column is the one people skip and it is the one that makes the
finding actionable. It answers: what would the submitting team have to show for this rule
to pass? If you cannot answer that in one line, the rule is not yet a rule.

### 4.3 Choosing the severity default

| Severity | Test |
|---|---|
| `Blocker` | Breaches a mandatory control, or is a failure mode with unbounded customer, financial or regulatory impact. Cannot go live. |
| `Major` | Material risk, or a mandatory control met only partially. Needs a committed owner and date. |
| `Minor` | Real but contained. Normal backlog. |
| `Advisory` | Improvement or forward-looking concern. |

Be sparing with Blockers. A rubric where a quarter of the rules are Blockers produces
reviews nobody can act on, and reviewers start quietly discounting them. Roughly one in
six is a healthy ratio.

### 4.3.1 Conditional severities

A severity may depend on the application. `synthesise.py` parses the cell, so the wording
has to stay inside this grammar:

```
<Severity>                                  Major
<Severity> (<condition>)                    Blocker (T1/T2)
<Severity> if|for|when <condition>          Blocker if any regressed
<Severity>; <Severity> if <condition>       Major; Blocker for critical providers
```

A condition is a disjunction of alternatives joined by `or`; each alternative is the
conjunction of every predicate recognised inside it, so
`Blocker if migrating a live system with no non-prod before cutover` requires all three.
Where the cell gives no plain severity, the unescalated case sits one level below the
conditional one: `Blocker (T1)` is Major for a tier 3 application.

These are the predicates the script recognises. Nothing else is understood, and an
unrecognised condition leaves the severity at its base and warns:

| Write | Resolved from |
|---|---|
| `T1`, `T2`, `T1/T2`, `tier 1` | the criticality tier in `review.json` |
| `in scope`, `applicable` | `application.regimes_in_scope` being non-empty |
| `migrating` | `submission.change_type` being `migration` |
| `any regressed`, `regressed` | the prior-review delta, so `--prior` is required for it to bite |
| `live system` | `change_type` being migration, material change or uplift |
| `internet-facing`, `public-facing` | `severity_context.internet_facing` |
| `critical provider`, `critical third party` | `severity_context.critical_providers` |
| `no non-prod before cutover` | `severity_context.no_non_prod_before_cutover` |
| `value-bearing`, `payment`, `regulated data` | `severity_context.value_bearing`, else the declared data classes |
| `on Hold`, `Hold ring` | `severity_context.radar_hold` |

To introduce a new predicate, add it to `CONDITION_PREDICATES` and to
`Context.predicate` in `scripts/synthesise.py`, then add a row above. The test
`TestRubricSpecsAreAllKnown` fails on any rubric condition no predicate recognises, so a
rule written outside this vocabulary will not reach a release.

Prefer a plain severity. A conditional one is worth it where the same rule genuinely means
something different at tier 1 and tier 4 — recovery testing, threat modelling, impact
tolerance — and is a liability anywhere else.

### 4.4 Also update the three prose sections

A rule row alone is half the work. Each rubric file ends with three sections and they carry
disproportionate value:

- **Contradiction checks** — add an entry if the new rule can conflict with a claim made
  elsewhere. These produce the strongest findings; in practice most headline findings come from
  here.
- **Questions the board will ask** — add the question this rule answers, phrased the way a
  board member would actually say it.
- **Do not raise** — add an entry if the new rule risks generating duplicate or generic
  findings. This section actively suppresses noise and is why the reviewers stayed in lane.

---

## 5. Worked example, end to end

A typical gap: a reporting server reads the production database directly over TCP:1433
from on-premises, and no clause prohibits it.

**Step 1 — Cloud Platform Engineering adds the clause** to
`standards/landing-zone-baseline.md`, Network section:

```markdown
| `LZB-NET-11` | Data-tier ports are not reachable from any on-premises or other-domain
range. Reporting and analytics read from a replica, an extract, or a governed interface,
never from the primary. | `[CONFIRMED 2026-03-14 by Head of Cloud Platform Engineering]` |
```

**Step 2 — the governance function adds the rule** to `rubric/platform.md`, Network table:

```markdown
| `LZ-NET-012` | No data-tier port reachable from on-premises or another domain; reporting reads from a replica or extract | `LZB-NET-11` | Blocker | Deployment view showing the reporting path, or an explicit statement |
```

**Step 3 — add the contradiction check** in the same file:

```markdown
- A claim that all traffic is inspected centrally, alongside a database protocol line
  drawn from an on-premises server straight into the data subnet.
```

**Step 4 — add the board question:**

```markdown
- What reads this database, and does any of it come from outside the workload?
```

**Step 5 — re-run against a past submission** and confirm the rule fires where you expect
and stays quiet where you don't.

Total effort: about twenty minutes, most of it Step 1 getting the wording agreed.

---

## 6. Bulk-importing existing policy

The realistic starting position: the organisation has policy in Word documents, Confluence
pages and PowerPoint standards packs, not in clause form. Do not hand-transcribe it.

**The workflow that works:**

1. Drop the source policy documents into a folder.
2. Ask the agent to convert, one source document at a time, one standards file at a time:

   ```
   Read <policy-document> and convert its architecturally-relevant requirements into
   clauses for standards/landing-zone-baseline.md. Use the existing ID scheme and section
   structure. One clause per testable requirement. Mark every clause [TBD] — I will
   confirm them individually. Quote the source section for each clause so I can verify it.
   Do not invent requirements the document does not state, and do not merge two
   requirements into one clause.
   ```

3. **The owning function reviews every clause and changes `[TBD]` to `[CONFIRMED]`
   individually.** This is the step that cannot be delegated to the agent, and it is where
   the authority comes from. A clause nobody read is worse than no clause.
4. Only then add rules that cite the confirmed clauses.

Two guardrails worth stating up front: requirements that are not testable from a
design document do not become clauses (they belong in build or operate controls), and
requirements the source document states as guidance rather than mandate should be marked
so, because a rule citing guidance as mandatory will be rejected the first time it fires.

### The obligations register is different

`standards/obligations-register.md` is **the only file in this skill where the name of a
regulation may appear**, and only Compliance populates it. The reviewer is constrained from
citing any regime whose `Applies` column is not `yes`, and from naming any regulation not
reproduced in that file. Keep that discipline: it is the reason the regulatory findings are
defensible.

Compliance's minimum useful contribution is small: set `Applies` per legal entity, and
populate the `Internal control` column for the obligations the design actually touches.
Typically that is a handful of rows, and it converts most of the `REG` domain from
unassessable to assessable.

Two mechanical constraints, because `triage.py` reads this file rather than just displaying
it:

- **It reads both tables by column heading, not by position.** Reorder or add columns
  freely; rename `Regime`, `Applies`, `ID` or `Regimes` and the run stops with an error.
  Failing is deliberate — the alternative is a silent change to which obligations are
  considered in scope, and nothing downstream would show it.
- **An obligation's `Regimes` column must name a regime exactly as the Applicability table
  spells it.** Alternatives separated by a spaced slash or dash are the same regime
  (`GDPR / UK GDPR` may be cited as `GDPR`), and a trailing version is optional
  (`PCI DSS 4.0` may be cited as `PCI DSS`). There is no fuzzy matching: it once let an
  applicable `EU AI Act` make an `EU Data Act` obligation assessable, which is precisely
  the class of error this file exists to prevent. Anything unmatched is reported by
  `triage.py` and `validate.py` as a note, so run one after editing.

---

## 7. Calibration — the loop that makes the rubric good

Rules written in a room are guesses. Rules calibrated against real submissions are assets.

**Run this every cycle for the first three or four reviews:**

1. Run the review on a submission that already went through the board.
2. Put the tool's findings beside the findings the board actually raised.
3. Then work three lists:

| Gap | Action |
|---|---|
| The board raised it, the tool missed it | Add a rule, or fix the evidence requirement on the rule that should have caught it |
| The tool raised it, the board would not have | Lower the severity, or add it to the rubric's `Do not raise` list |
| The tool raised it and the board missed it | Keep it. This is the value. Tell the review team. |

4. Ask each review team to read its own rubric file once, annotate it, and hand it back.
   Thirty minutes each. It converts them from audience into co-authors, which is the
   difference between adoption and shelfware.

Track `unassessable per submission` over time. If it is not falling, either the standards
are not being populated or the intake gate is not being enforced.

---

## 8. What not to add

**Judgements a checklist cannot make.** "Is this the right architecture?", "Is the threat
model imaginative enough?", "Is this trade-off wise?" These stay with the human reviewers,
and saying so out loud is what keeps those reviewers on side.

**More than about fifteen rules per area.** Beyond that the reviewer's attention thins and
findings get shallower. If an area needs more, it is probably two areas.

**Aspiration marked as mandatory.** A clause the organisation intends to adopt next year, marked
`[CONFIRMED]`, generates findings the submitting team cannot act on and teaches everyone to
discount the report.

**The same check in two domains.** Cite the other domain's rule instead. Each rubric's
`Do not raise` list exists to enforce this, and it is why the seven reviewers produced
complementary rather than overlapping findings.

**A rule with no clause behind it.** If it matters and no policy covers it, the reviewer
already handles this: it comes out as `Advisory` with rule ID `NONE` plus a proposal for
the clause that should exist. Harvest those proposals into real clauses rather than writing rules
without authority.

---

## 9. Adding a whole new domain

Occasionally justified. An organisation with heavy ERP or mainframe integration might want
an `ERP` domain rather than stretching `INT`, or a healthcare provider a `CLN` (clinical
safety) domain. Do it only when the new domain has its own reviewer
mandate and at least fifteen rules; otherwise extend an existing rubric.

Five files change, and missing any of them breaks the run:

1. `rubric/<domain>.md` — new file, following the existing structure including the three
   prose sections.
2. `standards/` — whichever file holds the clauses it cites.
3. `SKILL.md` — the Phase 3 domain table, and the reviewer count (currently seven).
4. `templates/findings.schema.json` — the `domain` enum appears in **three** places:
   `review.domains_reviewed`, `findings.items.domain`, and `not_assessable.items.domain`.
   Miss one and validation fails on the first review.
5. `templates/reviewer-dispatch.md` — nothing structural, but check the prompt still reads
   correctly for the new domain.

Domain prefixes must be 2 or 3 uppercase letters to satisfy the rule ID pattern.

---

## 10. Change control

| Change | Approval | Effect on existing reviews |
|---|---|---|
| New clause, `[TBD]` | Author alone | None; not assessed |
| `[TBD]` → `[CONFIRMED]` | The clause's owning function | Dependent rules become assessable; severity ceiling lifts |
| `[DEFAULT]` → `[CONFIRMED]` | The clause's owning function | Provisional findings become full severity, potentially Blockers |
| New rule | Governance function, with the clause owner informed | New findings appear on the next re-review; not retrospective |
| Severity change | Governance function | Changes verdicts. Note it in the next report so the delta is explained |
| Rule retired | Governance function | Mark retired in the rubric, keep the ID. Open findings against it close as `Superseded` |
| ID renamed | **Don't** | Breaks `findings.json` diffing and orphans historical findings |

Version the whole skill folder in your own repository and change it through pull
requests. The review teams reading each other's clause changes as diffs is a benefit in
itself, and it gives internal audit an evidence trail for how the review standard evolved.

**Regression check before merging any change:**

```bash
python3 - <<'EOF'
import json, re, pathlib
pat = re.compile(json.load(open('templates/findings.schema.json'))
                 ['properties']['findings']['items']['properties']['rule_id']['pattern'])
ids, dangling = [], []
defined = set()
for f in pathlib.Path('standards').glob('*.md'):
    defined |= set(re.findall(r'`((?:LZB|SB|CT|OBL|PAT)-[A-Z0-9]{3}(?:-\d+)?)`', f.read_text()))
for f in sorted(pathlib.Path('rubric').glob('*.md')):
    text = f.read_text()
    ids += re.findall(r'`([A-Z]{2,3}-[A-Z0-9]{2,4}-\d{3})`', text)
    dangling += [c for c in re.findall(r'`((?:LZB|SB|CT|OBL|PAT)-[A-Z0-9]{3}(?:-\d+)?)`', text)
                 if c not in defined]
print("rules:", len(ids))
print("pattern violations:", [i for i in ids if not pat.fullmatch(i)] or "none")
print("duplicate rule ids:", sorted({i for i in ids if ids.count(i) > 1}) or "none")
print("rules citing a clause that does not exist:", sorted(set(dangling)) or "none")
EOF
```

All four must come back clean. Then re-run the review against one past submission and
confirm the verdict has not moved for a reason you cannot explain.
