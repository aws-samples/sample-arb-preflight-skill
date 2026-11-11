# Usage Guide

How to invoke the skill, what it produces, how to read it, and how to port it to another
agent host. For changing rules and policy, see `skill/arb-preflight/AUTHORING.md`. To install, see `installation.md`.

---

## 1. Prerequisites

| Requirement | Why | Check |
|---|---|---|
| Submission inside the workspace | The extractor resolves relative paths against the workspace root | Drop the `.pptx` / `.docx` anywhere under the workspace |
| Subagents available | Phase 3 dispatches seven isolated reviewers in parallel; hosts without fan-out run them sequentially | Your host's agent/subagent settings (Kiro: Autopilot mode) |
| Python 3.9+ | `scripts/extract_submission.py` — standard library only | `python3 --version` |
| Image reading | Diagrams carry the topology and most of the contradictions | Your model must accept image input |

The skill activates on intent. You do not need to name it.

If you want to see what the scripts produce before installing anything, the repository
ships a fictional submission with an answer key (`samples/northwind-payments/`).
`samples/README.md` has the commands.

---

## 2. The prompt to use

```
Run an ARB pre-flight review on "<file>.pptx".

Application: <name>
Criticality tier: <1-4, and the local label if any>
Legal entity / jurisdiction: <entity, country>
Data classes: <what it handles, or "to be confirmed">
Change type: <new build | material change | migration | uplift>
Target go-live: <date>
Board date: <date>
Business owner: <name>
Technical owner: <name>
```

Nine lines, and they change the output materially. Every one you omit becomes a finding or
an `UNKNOWN`: a missing tier pushes `RES-TIER-001` to a Blocker, a missing jurisdiction
makes the whole regulatory domain unassessable, and missing owners leave findings
`UNASSIGNED` so they cannot be tracked to closure.

Worked example (fictional):

```
Run an ARB pre-flight review on "checkout-replatform-v0.9.pptx".

Application: Checkout Replatform
Criticality tier: 1
Legal entity / jurisdiction: Example Retail Ltd, United Kingdom
Data classes: customer personal data, order history, payment tokens (no raw card data)
Change type: migration of a live production service to AWS
Target go-live: 2027-03-01
Board date: 2027-01-20
Business owner: Head of Digital Commerce
Technical owner: Principal Engineer, Checkout
```

### Shorter, when you do not have the metadata

```
Pre-flight review this architecture: <file>.pptx
```

Works. The skill reads `intake.md`, asks for tier and jurisdiction, and runs with `UNKNOWN`
if you decline, raising the consequences as findings. Fine for a first look, weaker for
anything you would show a board.

---

## 3. Variants

**Intake gate only** — two minutes, tells you whether a deck is worth a full review:

```
Run the ARB pre-flight intake gate only on <file>.pptx. Do not run the domain reviewers.
```

Returns the mandatory-artefact check and the pre-read gap list. The right first move on a
thin submission: a three-slide deck should get a gap list, not a seven-domain review.

**Single domain** — when one review team wants its lens early:

```
Run the ARB pre-flight security and identity domain only on <file>.pptx.
Tier 2, single jurisdiction.
```

Swap in: platform and landing zone · security and identity · data and privacy · resilience
and capacity · integration and transaction integrity · operations, cost and lifecycle ·
regulatory and third-party.

**Re-review** — where the tool gets cheap and most useful:

```
Re-review <file-v1.0>.pptx against the previous findings in
reviews/<app>/<date>/findings.json. Lead with the delta.
```

Diffs the findings and marks each `closed`, `open`, `partially addressed` or `regressed`.
Regressions are raised one severity level automatically.

**Record a waiver** so a knowingly accepted gap stops reappearing as an open finding:

```
Create a waiver from templates/waiver-request.md for <F-nnn> (<short description>),
accepted by <name>, expiring <date>, and re-run the review.
```

Waivers carry a mandatory expiry. An expired waiver becomes a Major finding in its own
right, which is the point.

**Multiple files** — deck plus Word HLD plus separately exported diagrams:

```
Pre-flight review the submission in ./submissions/checkout-v1.0/
```

Pass the folder. The extractor handles `.docx`, `.pptx` and loose images, keeping citation
anchors distinct per source document.

---

## 4. What not to put in the prompt

**Do not narrow the scope.** "Focus on the network design" or "check the DR posture" cuts
the fan-out, and you lose the contradictions, which come from comparing domains rather than
from any single lens. A database labelled one way in the prose and drawn another way on the
diagram surfaces because several reviewers read the same diagrams with different mandates.

**Do not ask for leniency on the date.** The skill is instructed to refuse and will say so.

**Do not ask it to approve.** It recommends; the board decides. Every output says so.

---

## 5. What it produces

Written to `reviews/<app>/<yyyy-mm-dd>/`:

| File | Audience | Contents |
|---|---|---|
| `preflight-report.md` | Submitting team | Every finding with rule ID, evidence anchor, business impact, remediation, owner |
| `board-pack.md` | The board | One page: recommendation, decisions requested, conditions, risks proposed for acceptance |
| `findings.json` | Governance function | Machine-readable, for re-review diffing, regression detection and portfolio reporting |
| `fact-sheet.md` | Everyone | Normalised, cited summary of what the design actually says, with `NOT STATED` where it is silent |
| `extracted/` | Traceability | `text.md` with citation anchors, `media/` diagrams, `manifest.json` inventory |

The fact sheet is the artefact the submitting team will argue with, which is useful: it is
strictly what is cited, so disagreements resolve fast.

### Who reads what

- **Submitting team** → `preflight-report.md`, starting at *Fix before the board*
- **Board** → `board-pack.md`, one page
- **Individual review teams** → the domain sections of `preflight-report.md`
- **Secretariat** → `findings.json` for condition tracking across reviews

---

## 6. The six phases, briefly

| Phase | What happens |
|---|---|
| 0 Intake | Captures metadata, checks the six mandatory artefacts. Fails fast on a thin deck |
| 1 Extract | PPTX/DOCX to text with stable anchors (`Slide 14`, `§3.2`), diagrams to `media/`, unreadable formats flagged |
| 2 Fact sheet | Normalised cited summary; `NOT STATED` recorded explicitly. Shared ground truth |
| 3 Triage + domain review | `triage.py` removes rules whose standard is not populated; seven reviewers then assess the rest in parallel, all reading every diagram |
| 4 Synthesis | The model groups root causes and lists contradictions in `review.json`; `synthesise.py` checks coverage, diffs prior findings, reconciles waivers, assigns the verdict and writes the artefacts |
| 5 Outputs | The three artefacts, then a short summary in chat |

Phase 4 matters more than it looks. Seven reviewers routinely produce well over a hundred
raw findings on a real deck; deduplicated by root cause they collapse to a handful of
Blockers and a dozen or so root causes. Presenting the raw list to a board would bury the
items that matter.

---

## 7. Verdicts and severities

| Verdict | Condition |
|---|---|
| Ready | No blockers, no majors |
| Ready with conditions | No blockers; every major has a named owner and a date |
| Not ready — rework | One or more blockers |
| Insufficient information | Mandatory artefacts missing; or more than a third of rules unassessable; or a major with no owner and date |

Two consequences worth knowing before you read a verdict:

**An uncommitted major holds the verdict.** Reviewers name the owning *role*, never a
date — so until you put an owner and a date on every live major in `review.json` under
`commitments` (keyed by rule ID or finding ID), the run reports `Insufficient information`
and names the uncommitted findings in both artefacts. This is deliberate: a condition
nobody owns by a stated date is not a condition.

```jsonc
"commitments": {
  "RES-DR-002": {"owner": "Principal Engineer, Checkout", "due": "2027-01-10"}
}
```

**A live waiver takes a finding out of the counts.** A waived blocker does not force
`Not ready` — the organisation has already accepted that risk for a fixed period. It
leaves "Blockers outstanding" and is named instead, with its waiver ID and expiry, in both
the report and the board pack. An expired waiver becomes a new major (`OPS-GOV-004`).

| Severity | Meaning |
|---|---|
| Blocker | Breaches a mandatory control, or an unbounded failure mode. Cannot go live |
| Major | Material risk, or a mandatory control met only partially |
| Minor | Real but contained |
| Advisory | Improvement or forward-looking concern |

Severity may move up one level for tier 1 or where regulated data or value-bearing
transactions are in the path, and down one level with written justification. Never two.

**Some rubric severities are conditional on the application** — `Blocker (T1)`,
`Blocker (internet-facing or T1)`, `Blocker if any regressed`,
`Major; Blocker for critical providers`. `synthesise.py` resolves these centrally against
the criticality tier, the change type, the regimes in scope, the prior-review delta and
the `severity_context` flags in `review.json`, rather than leaving each reviewer to guess
at a condition that often turns on facts outside their domain. Where it cannot settle a
condition it says so and leaves the severity alone:

```
WARNING: LZ-TEC-001: conditional severity 'any technology is on Hold' left at its base
         severity; cannot evaluate severity_context.radar_hold
```

That is a prompt to add the flag to `review.json`, not a defect. The full ordering —
rubric default, one level of adjustment, Major cap last — is in `SKILL.md`.

**A closed finding stays in `findings.json`.** Findings resolved since the prior review
are carried forward with `status: closed`, and ids are allocated from a high-water mark,
so a gap that closes and later reopens is reported as a regression against the same id
rather than as something new. Do not prune them.

**Silence is filed by severity.** When the submission says nothing about a rule the
rubric rates Blocker or Major, it is reported as a finding with status `Insufficient
information`, listed separately under "Not stated in the submission". Silent Minor and
Advisory rules go to the pre-read gap list. This keeps repeat runs consistent.

**Findings against a `[DEFAULT — CONFIRM]` clause are capped at Major and labelled
`provisional standard`.** Confirming the standards lifts the cap — see the adoption guide.

---

## 8. Running the extractor by hand

Useful for checking a submission before committing to a review:

```bash
python3 <skill-folder>/scripts/extract_submission.py \
  "<file>.pptx" --out ./extracted --convert
```

To see expected output on a known input, run it over `samples/northwind-payments/` in this
repository and compare with the answer key in `samples/northwind-payments/README.md`.

Output tells you the submission's weight and whether the diagrams are usable:

```
words: 2477  slides: 25  unreadable images: 0
```

`--convert` uses macOS `sips` to turn TIFF/BMP into PNG; omit it on other platforms.
Vector paste-ins (EMF, WMF, SVG) are never converted; they are listed for re-export because
a topology that cannot be seen must not be guessed at.

---

## 9. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| A domain reviewer returns prose instead of structured findings | Subagent drifted from the output contract | Re-dispatch that domain with the output structure restated |
| `unreadable images` non-zero | Diagrams pasted as EMF/WMF/SVG | Raise `LZ-DOC-002` and ask the team for PNG exports. Do not proceed on inference |
| "legacy binary format not supported" | `.ppt` or `.doc` | Ask for a re-save as `.pptx` / `.docx` |
| Whole domain returns "standard not populated" | The governing standards file is `[TBD]` | Correct behaviour. The owner is the standard's owner, not the submitting team |
| Under 800 words or fewer than 10 slides for a tier 1–2 system | Thin submission | Run the intake gate only; expect it to fail |
| Everything reads as generic cloud advice | Standards not populated and the reviewer fell back on memory | Report it. This is the failure mode the skill is built to prevent |

---

## 10. Other agent hosts

Installation for Kiro, Claude Code, Amazon Quick and other hosts, plus a five-step smoke
test, is in `installation.md`. Keep the `description` in the SKILL.md frontmatter
unchanged when porting; it is what decides activation.

### Acceptance test

Keep one known submission — ideally one with deliberate flaws (an RTO the DR pattern cannot
meet, a residency claim contradicted by a backup region, a diagram label that disagrees with
the prose, a missing dependency map) — and its reviewed output as a reference. Re-run it
after any change to the skill or any port. If the modified version stops finding the
diagram contradictions, something has broken, and the smoke test above tells you which
capability.

Speaker notes do not survive a PDF export. If the host cannot run the extractor and you fall
back to attaching a PDF, you lose them, and material gaps often live only in the notes.

---

## 11. Confidentiality

The skill is designed to run where the submission already lives. Standards, extraction and
outputs stay in your repository; model inference goes to whichever endpoint your agent host
is configured to use, so route it through an endpoint your organisation has approved for
confidential design material.

Treat this tool as in scope of the same review it performs: have your security function
review it before it touches a real design. Add `reviews/` and any submission files to
`.gitignore` so real designs are never committed to a public fork.
