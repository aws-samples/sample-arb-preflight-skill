# Approved Pattern Catalogue

Status: `[TBD]` — owned by Enterprise Architecture.

A design that reuses an approved pattern should get a shorter review, and the reviewer
should say so. Deviation from a pattern is not automatically wrong, but it is always
worth a stated reason, because the pattern encodes decisions the board already took.

## Entry format

Each pattern needs enough for the reviewer to detect conformance from a diagram and a
few paragraphs.

```markdown
### PAT-nnn — <name>
**Use for:** <situations>
**Not for:** <situations>
**Shape:** <components and their relationships, as they appear on a diagram>
**Inherited controls:** <what a conforming design gets for free, with clause IDs>
**Must still evidence:** <what conformance does not cover>
**Owner:** <team>  **Status:** Approved | Provisional | Retiring
```

## Patterns

`[TBD]` — start with the three or four shapes your teams actually build. Typical first
entries in an AWS estate:

- Internet-facing customer channel: central edge → private ALB → container compute →
  managed data store.
- Internal API: API gateway → compute → data store, mTLS between internal callers.
- Event-driven integration between domains: outbox → managed streaming → idempotent
  consumer → dead-letter with replay.
- Batch file exchange with a third party: managed transfer landing zone → scan →
  validate → process → archive with retention lock.
- Statutory or regulatory reporting extract: golden source → transformation with lineage
  capture → submission with immutable evidence.
- Data platform consumption: producer-owned data product → catalogue → governed access.

## Anti-patterns

Name the ones your board keeps rejecting, so the reviewer flags them by name and the
finding lands as a known position rather than an opinion.

`[TBD]` — common candidates:

- Shared mutable database between two owning domains.
- Synchronous chain of three or more services in a customer-facing path, with no
  degradation mode.
- Batch reconciliation as the only integrity control on an asynchronous payment or order flow.
- Point-to-point integration bypassing the central integration layer.
- A single region with a documented but never-tested DR plan for a tier 1 service.
- Workload-owned public endpoint bypassing the central edge.
- Long-lived credentials shared between environments or between systems.
