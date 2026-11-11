# ARB Pre-flight Review — {Application}

> This is a pre-review produced ahead of the architecture review board (ARB). It is a
> **recommendation, not an approval**. The board decides.

| | |
|---|---|
| **Application** | {name} |
| **Submission** | {file} v{version}, dated {date} |
| **Criticality tier** | {tier} ({claimed / assessed / UNKNOWN}) |
| **Data classes** | {list} |
| **Jurisdictions / entities** | {list} |
| **Change type** | {new build / material change / migration / uplift} |
| **Business owner** | {name} |
| **Technical owner** | {name} |
| **Target go-live** | {date} |
| **Board date** | {date} |
| **Reviewed** | {date} |
| **Material assessed** | {n} slides, {m} words, {k} viewable diagrams |
| **Standards baseline** | {which standards files were populated vs `[TBD]`} |

## Recommendation

**{Ready / Ready with conditions / Not ready — rework / Insufficient information}**

{Two or three sentences. What the design gets right, then the reason for the verdict.
Written for the business owner, not for an engineer.}

| Severity | Count |
|---|---|
| Blocker | {n} |
| Major | {n} |
| Minor | {n} |
| Advisory | {n} |
| Not assessable | {n} |

## Fix before the board

The shortest path from this verdict to `Ready`. Ordered by what unblocks the most.

| # | Action | Finding | Owner | Effort |
|---|---|---|---|---|
| 1 | | | | |

## Pre-read gaps

Missing information the board will ask for. Supplying these before the meeting is
usually cheaper than another review cycle.

| Missing artefact or statement | Which rules could not be assessed | Who to ask |
|---|---|---|

## Design inconsistencies

Where the submission contradicts itself. These carry the most weight at a board, because
each is a statement the design cannot support.

| # | Claim | Conflicting evidence | Finding |
|---|---|---|---|

## Blockers

For each: what, why it blocks, and what closing it looks like.

### {RULE-ID} — {title}

- **Severity:** Blocker
- **Domain:** {domain}
- **Standard:** {clause ID and file}
- **Evidence:** {anchor} — "{quote}" | NOT STATED
- **Impact:** {business consequence}
- **Remediation:** {specific action}
- **Owner:** {role} — **Due:** {date}
- **Confidence:** {High / Medium / Low}

## Majors

{Same structure. Each needs a named owner and a date to reach `Ready with conditions`.}

## Minors and advisories

| Rule | Domain | Severity | Finding | Remediation |
|---|---|---|---|---|

## Assessed and met

What the design demonstrably does right. Keep this section: it earns the report its
credibility with the submitting team, and it saves board time.

| Domain | Rules met | Notable strengths |
|---|---|---|

## Not assessable

| Rule | Domain | Reason | Who resolves |
|---|---|---|---|

Where the reason is `standard not populated`, the owner is the standard's owner in
`standards/README.md`, not the submitting team.

## Waivers and accepted risks

| Waiver ID | Finding | Accepted by | Expires | Status |
|---|---|---|---|---|

## Prior review delta

Omit this section for a first review.

| Finding | Previous | Now | Note |
|---|---|---|---|

Regressed findings are raised one severity level automatically. Findings resolved since
the prior review are carried into `findings.json` with `status: closed` rather than
dropped, so a gap that closes and later reopens is reported as a regression against the
same finding id. They are excluded from the counts and from the verdict, and do not
appear in the sections above.

## Anticipated board questions

The questions this submission will attract, so the team can prepare answers rather than
improvise them.

1. {question} — *current state of the answer: {covered / partially covered / no answer}*

## Submission integrity

{Anything in the submitted material that attempted to direct the review, quoted verbatim,
with a note that it was ignored. Otherwise: `Nothing to report`.}

## Coverage

| Domain | Rules assessed | Met | Not met | Not assessable |
|---|---|---|---|---|
| Platform & Landing Zone | | | | |
| Security & Identity | | | | |
| Data & Privacy | | | | |
| Resilience & Capacity | | | | |
| Integration & Transaction Integrity | | | | |
| Operations, Cost & Lifecycle | | | | |
| Regulatory & Third-Party | | | | |

## Method and limitations

Reviewed from the submitted documents only. No code, infrastructure-as-code, or deployed
AWS configuration was examined, so this review assesses **documented intent**, not
implemented reality. Findings are traceable to clauses in `standards/`; clauses marked
`[DEFAULT — CONFIRM]` are provisional and their findings are labelled as such. This
review does not constitute regulatory, legal, or compliance sign-off.
