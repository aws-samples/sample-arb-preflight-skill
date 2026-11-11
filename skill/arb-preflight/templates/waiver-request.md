# Waiver / Risk Acceptance — {WAIVER-ID}

Store as `reviews/<app>/waivers/<WAIVER-ID>.md`. The reviewer reads this directory and
reports covered findings as `Waived` rather than open. An expired waiver becomes a Major
finding in its own right, which is the point: waivers that quietly become permanent are how
an organisation's control environment erodes.

| | |
|---|---|
| **Waiver ID** | {e.g. W-CHK-001} |
| **Application** | {name} |
| **Finding** | {F-nnn} |
| **Rule** | {RULE-ID} |
| **Standard clause** | {clause ID and file} |
| **Original severity** | {Blocker / Major} |
| **Raised** | {date} |
| **Expires** | {date — mandatory, no open-ended waivers} |
| **Status** | Requested / Approved / Rejected / Expired / Closed early |

## What is not being met

{The control, and specifically what the design does instead. Written so someone reading it
in eighteen months, with no memory of this review, understands the gap.}

## Why an exception is being requested

{The business or delivery reason. "The date" is a reason; record it honestly rather than
dressing it as a technical rationale.}

## Risk being accepted

| | |
|---|---|
| **Scenario** | {what has to happen for this to bite} |
| **Likelihood** | {with the reasoning} |
| **Impact** | {customers affected, financial exposure, regulatory consequence, reputational} |
| **Detection** | {how the organisation would know it had happened, and how quickly} |

## Compensating controls

What reduces the risk in the meantime, and who operates each. A waiver with no
compensating control is a plain risk acceptance; label it as such rather than implying
mitigation that does not exist.

| Control | Owner | Evidence it is operating |
|---|---|---|

## Path to compliance

| Step | Owner | By |
|---|---|---|

If there is no path, say so. A permanent exception needs a different decision, at a higher
authority, than a time-boxed one.

## Approval

| Role | Name | Decision | Date |
|---|---|---|---|
| Risk owner (accountable executive) | | | |
| Domain architect | | | |
| Security (where a security control is waived) | | | |
| Compliance (where an obligation is engaged) | | | |
| Board chair | | | |

Approval authority should scale with severity and with the value at risk. A Blocker waiver
on a tier 1 service is not a decision an architect makes alone.

## Review

| Date | Reviewer | Outcome |
|---|---|---|

Review before expiry, not after. Expiry without review is an incident in the control
process, not an administrative detail.
