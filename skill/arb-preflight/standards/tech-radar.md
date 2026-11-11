# Technology Radar

Status: `[TBD]` — owned by Enterprise Architecture.

Until populated, `rubric/platform.md` rules `LZ-TEC-*` report as
`Insufficient information — standard not populated`. Do not have the reviewer opine on
technology choice without this file; unsupported technology opinions are the fastest way
to lose the submitting team's trust.

## Rings

| Ring | Meaning | Effect at the board |
|---|---|---|
| Adopt | Default choice. Supported, patterns exist, teams trained. | No finding |
| Trial | Permitted with an architect sponsor and a named support model. | Minor finding: name the sponsor and support model |
| Assess | Not permitted in production. Proof of concept only. | Major finding |
| Hold | Not permitted for new build. Existing use is being retired. | Blocker |

## Compute

| Technology | Ring | Notes |
|---|---|---|
| `[TBD]` | | e.g. ECS Fargate — Adopt; EKS — Trial with platform onboarding; EC2 — Assess for new build |

## Data stores

| Technology | Ring | Notes |
|---|---|---|
| `[TBD]` | | |

## Integration and messaging

| Technology | Ring | Notes |
|---|---|---|
| `[TBD]` | | |

## Identity, security and observability tooling

| Technology | Ring | Notes |
|---|---|---|
| `[TBD]` | | |

## AI / ML

| Technology | Ring | Notes |
|---|---|---|
| `[TBD]` | | Include which foundation models and which regions are permitted, and whether prompt or inference data may leave the jurisdiction |

## Standing constraints

`[TBD]` — the handful of blanket rules worth stating once rather than per technology.
Common examples: no unmanaged databases on EC2; no self-managed Kafka where MSK is
available; no new SOAP interfaces; no technology without a named production support
model; no service in preview or without an SLA in a tier 1 path.
