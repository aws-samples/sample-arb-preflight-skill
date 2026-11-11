# ARB-Preflight

An AI pre-flight check for architecture review boards (ARB): an agent skill that reviews an
AWS solution design against your organisation's own standards, before the meeting.

Give it an HLD as PPTX or DOCX (plus diagrams). It extracts the text and diagrams with
citation anchors, builds a cited fact sheet, runs **seven specialist reviewers in
parallel** (platform, security, data, resilience, integration, operations, regulatory)
across **284 rules** (191 assessable against the starter standards; the rest report as
`standard not populated` until you write the clause), deduplicates findings by root cause,
and writes:

- `preflight-report.md` — every finding with rule ID, evidence anchor, impact, remediation, owner
- `board-pack.md` — a one-page recommendation for the board
- `findings.json` — machine-readable, for re-review diffing and condition tracking

Scope: **AWS**, **documents only**. No code, no IaC, no live account inspection.

> This is an example / reference implementation. It ships with starter standards marked
> `[DEFAULT — CONFIRM]` or `[TBD]`. Replace them with your own policy before relying on
> the output. It recommends; it never approves.

---

## Why this rather than a good prompt

A capable model with a well-written prompt does find the obvious things. Ask one to review
an HLD and it will spot that a 15-minute RTO cannot be met by restoring from a backup, or
that two availability zones is thin for a tier 1 service. Those are classic, they are in
the training data, and you do not need 284 rules to get them.

What a prompt does not give you is a governance process. The gap is not in finding issues;
it is in everything a board needs around a finding:

| A prompt gives you | A board needs |
|---|---|
| Findings that vary run to run | The same 284 checks on every submission, so the fifth review is as deep as the first |
| Generic cloud best practice | A citation to *your* clause — `LZB-NET-05`, not "consider VPC endpoints" |
| Confident prose where the pack is silent | "Not stated", named, owned, and separated from "not compliant" |
| An opinion where you have no policy | "Standard not populated" — the gap is yours, not the submitting team's |
| A fresh answer each time | A diff against the last review: closed, still open, **regressed** |
| Prose | `findings.json`, so you can answer "which conditions from the last four boards are still open?" |
| A severity it felt like | A severity derived in one place from the rubric, the tier and the prior review, reproducibly |
| A wall of forty items | Forty items deduplicated to nine root causes, because boards reject reports that inflate one gap |

Two of those are worth more than the finding quality. **Repeatability**: coverage is
checked mechanically and a missing rule fails the run rather than quietly shrinking the
review, so the output does not depend on which lens the model happened to apply or who
was on leave. **Assets**: the same review produces a report for the team, a one-page pack
for the board, and a machine-readable file that makes conditions trackable across reviews
instead of chased over email.

So the honest framing is that the rubric is a floor, not a ceiling. It guarantees that the
boring 80% is covered identically every time, which is precisely what frees a principal
architect to spend the meeting on the 20% that needs adversarial imagination. It will not
catch a novel failure mode that is not in the rubric. A good prompt will not catch the
third-party classification nobody remembered to ask for, three reviews in a row.

---

## Install

The skill is host-neutral. `install.sh` puts it where your agent host looks for skills:

```bash
./install.sh kiro   --dest <workspace>     # Kiro       -> <workspace>/.kiro/skills/
./install.sh claude --dest <project>       # Claude Code -> <project>/.claude/skills/
./install.sh quick                         # Amazon Quick -> dist/arb-preflight.zip to upload
./install.sh dir    --dest <skills-folder> # any other host
```

Use `--global` for user-wide Kiro or Claude Code installs. On Amazon Quick desktop, upload
the zip, or import the `skill/arb-preflight/` folder, via **Customize › Skills › Create**.
Details and a smoke test are in [`docs/installation.md`](docs/installation.md).

Requirements: an agent host with skills, local file access, Python 3.9+ (standard library
only), image input, and subagents. Hosts without fan-out run the seven reviewers
sequentially.

## Quick start

Put the submission file in your working folder and ask:

```
Run an ARB pre-flight review on "<file>.pptx".

Application: <name>
Criticality tier: <1-4>
Legal entity / jurisdiction: <entity, country>
Data classes: <what it handles>
Change type: <new build | material change | migration | uplift>
Target go-live: <date>
Board date: <date>
Business owner: <name>
Technical owner: <name>
```

See [`docs/usage-guide.md`](docs/usage-guide.md) for variants and troubleshooting.

## Try it on the sample

The repository ships a fictional submission, **Northwind Payment Hub**: a 16-slide
tier 1 payment-platform migration on a corporate template, with seven diagrams and about
two dozen planted gaps. `samples/northwind-payments/README.md` is its answer key: each
gap, the slide it is on, and the rule a correct review should raise. Run the skill on it
first, and compare.

```bash
# Extract: 16 slides, 7 diagrams, all viewable
python3 skill/arb-preflight/scripts/extract_submission.py \
  samples/northwind-payments --out /tmp/preflight

# Triage: which of the 284 rules are assessable against the standards as they stand
python3 skill/arb-preflight/scripts/triage.py --out /tmp/preflight/triage.json
```

Those two run without an agent and show what the skill starts from. The full review, with
the seven domain reviewers and the report, board pack and `findings.json`, needs an agent
host: see [Quick start](#quick-start).

```bash
python3 tools/validate.py              # rule ids, clause references, schema — run after editing standards/ or rubric/
python3 -m unittest discover -s tests  # behaviour of the triage and synthesis scripts
```

`validate.py` checks that the rubric and standards agree with each other. The tests build
synthetic reviews against the real rubric and check the behaviour the documents promise —
that a conditional severity resolves against the prior review, that a waived blocker leaves
both the verdict and the outstanding list, that an uncommitted major holds the verdict, that
confirming one regime does not make an unrelated obligation assessable. Standard library
only; the whole lot runs in a few seconds.


---

## Three principles

**It reviews against your standards, not generic cloud advice.** Where a standard is not
written down, the check is reported as *not assessable* rather than filled with an opinion.
A finding citing `LZB-NET-05` gets fixed; "consider using VPC endpoints" gets ignored.

**It recommends; it never approves.** The board decides. Accountability does not move.

**It distinguishes "not compliant" from "not stated."** The pre-read gap list, a week before
the meeting, is often worth more than the findings.

---

## Layout

```
install.sh                     installs the skill into Kiro, Claude Code, Amazon Quick, or any folder
tools/
  validate.py                  integrity checks (rule IDs, clause references, schema); run in CI
tests/
  test_synthesise.py           severity, verdict, waiver and prior-review-delta behaviour
  test_triage.py               regime applicability and standards-table parsing
samples/                       start here
  northwind-payments/          a fictional 16-slide submission and its answer key
skill/arb-preflight/           THE SKILL — host-neutral; this folder is what gets installed
  SKILL.md                     six phases, hard rules, verdict and severity model
  AUTHORING.md                 how to add rules and policy
  intake.md                    mandatory artefacts, metadata, the gate
  scripts/
    extract_submission.py      DOCX/PPTX to text with citation anchors, plus diagrams
    triage.py                  skips rules whose standard is not populated; sets severity ceilings
    synthesise.py              coverage, severity, merge, delta, waivers, verdict, three artefacts
  standards/                   ORGANISATION-OWNED. Populate these
    README.md                  ownership, clause states, priority order
    landing-zone-baseline.md   accounts, regions, network, encryption, guardrails
    security-baseline.md       identity, SoD, service auth, secrets, threat modelling
    criticality-tiering.md     tier definitions and the resilience matrix they mandate
    obligations-register.md    applicable regimes and their architecture obligations
    tech-radar.md              adopt / trial / assess / hold
    pattern-catalog.md         approved patterns and named anti-patterns
  rubric/                      284 rules across seven domains
    platform.md  security.md  data.md  resilience.md
    integration.md  operations.md  compliance.md
  templates/
    reviewer-dispatch.md       the per-domain subagent prompt skeleton
    preflight-report.md        findings report
    board-pack.md              one-page board pack
    findings.schema.json       machine-readable findings contract
    waiver-request.md          time-boxed risk acceptance
    review-input.example.json  the small judgement file the model writes for synthesise.py
docs/
  installation.md              per-host install and smoke test
  overview.md                  the problem, the approach, mapping to review teams
  usage-guide.md               prompts, variants, outputs, troubleshooting, porting
  adoption-guide.md            taking it live: sequencing, RACI, calibration, metrics
```

Review outputs are written to `reviews/<app>/<yyyy-mm-dd>/` in your working folder.
`reviews/`, `dist/` and every `.pptx` / `.docx` except the named sample are
git-ignored, so a real submission cannot be committed by accident.

### Domains

| Domain | Prefix | Rules | Assessable as shipped |
|---|---|---|---|
| Operations, Cost & Lifecycle | `OPS` | 51 | 45 |
| Platform & Landing Zone | `LZ` | 50 | 43 |
| Regulatory & Third-Party | `REG` | 44 | 3 |
| Resilience & Capacity | `RES` | 39 | 34 |
| Security & Identity | `SEC` | 36 | 34 |
| Integration & Transaction Integrity | `INT` | 33 | 22 |
| Data & Privacy | `DAT` | 31 | 10 |

The right-hand column is the honest day-one figure, and it is the point rather than a
caveat: the 93 blocked rules are blocked because *your* standard is not written down yet,
and the review says so instead of substituting generic cloud advice. `REG` is almost
entirely dark until Compliance sets `Applies` in `standards/obligations-register.md`, and
`DAT` until the data clauses are confirmed — both cheap, and `standards/criticality-tiering.md`
alone converts most of `RES`. Run `python3 skill/arb-preflight/scripts/triage.py` to see
the current split for your own standards; `tools/validate.py` keeps this table honest.

---

## Making it yours

1. Confirm `standards/criticality-tiering.md` — one table, and it makes the whole resilience
   domain assessable.
2. Replace the landing zone and security baselines with your own clauses (the agent can
   bulk-convert policy documents; see `AUTHORING.md` §6).
3. Set applicability in `standards/obligations-register.md`. The regimes listed are
   illustrative cross-industry examples; delete what does not apply and add your sector's.
4. Calibrate against three past submissions that already went through your board.

See [`docs/adoption-guide.md`](docs/adoption-guide.md).

---

## Limitations

It reviews documents, so it assesses documented intent, not deployed reality. It cannot
judge whether a design is *good*, only whether it is complete and conformant against the
rubric. It will not catch a novel failure mode absent from the rubric. Output quality
depends on the standards corpus. It is not legal, regulatory or compliance advice.

## Security

Submitted documents are treated as untrusted input; content that tries to direct the review
is ignored and reported. Do not commit real submissions or `reviews/` output to a public
repository, and route model inference through an endpoint approved for confidential
material.

To report a security issue in this project, see
[CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications).

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.
