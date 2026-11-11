# Standards — organisation-owned ground truth

These files are the difference between a review your board acts on and a review your
board dismisses. A finding that says "consider using VPC endpoints" gets ignored. A
finding that says "breaches `landing-zone-baseline.md` §Egress, mandatory since 2024-Q3"
gets fixed.

## Ownership

| File | Owner | Review cadence |
|---|---|---|
| `landing-zone-baseline.md` | Cloud Platform Engineering | Quarterly |
| `security-baseline.md` | Security Architecture | Quarterly |
| `criticality-tiering.md` | Operational Resilience / Business Continuity | Annually |
| `obligations-register.md` | Compliance / Risk | On regulatory change |
| `tech-radar.md` | Enterprise Architecture | Quarterly |
| `pattern-catalog.md` | Enterprise Architecture | Continuous |

Rename the owners to match your organisation; what matters is that each file has one.

## Populating them

Every file ships as a **starter baseline with defaults marked `[DEFAULT — CONFIRM]`**.
Those defaults are common practice in multi-account AWS landing zones; they are not your
policy until someone with authority says so.

Three states, and the reviewer behaves differently in each:

| State | Marker | Reviewer behaviour |
|---|---|---|
| Confirmed | `[CONFIRMED yyyy-mm-dd by <role>]` | Assess normally. Findings cite the clause as mandatory. |
| Default, unconfirmed | `[DEFAULT — CONFIRM]` | Assess, but cap severity at `Major` and label the finding `provisional standard`. |
| Placeholder | `[TBD]` | Do not assess. Report dependent rules as `Insufficient information — standard not populated`. |

Do not let the reviewer fall back on generic cloud best practice in place of a standard
the organisation has not written down. Generic advice in a governance report erodes the
credibility of the findings that do matter.

## Adding a clause

Give every clause a stable ID and never reuse one. The rubric references clauses by ID,
and `findings.json` records them, so renaming an ID silently breaks re-review diffing.
Superseding a clause: mark it `[SUPERSEDED BY <new-id> yyyy-mm-dd]` and keep it in place.

## Fastest path from zero

You do not need all six files to start. In order of return on effort:

1. `criticality-tiering.md` — one table, and it makes the entire resilience domain
   assessable. Half of board pushback lives here.
2. `landing-zone-baseline.md` — even a partial network and account section catches the
   most expensive rework, because network topology is the hardest thing to change late.
3. `obligations-register.md` — just switch on the regimes that apply to your entities.
4. The rest as they mature.
