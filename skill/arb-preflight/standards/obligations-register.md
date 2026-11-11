# Obligations Register

Status: `[TBD]` — owned by Compliance / Risk.

**The reviewer may only cite a regime whose `Applies` column reads `yes`.** Everything
below ships as `TBC`. Until Compliance sets them, the `REG` domain reports
`Insufficient information — standard not populated`. This is deliberate: a wrong
regulatory citation in a governance report is worse than no citation.

The regimes listed are **illustrative, cross-industry examples** — privacy law, payment
card security, security certifications, listed-company controls, AI governance. Delete the
ones that do not apply to you and add your sector's own regulator and local law. The
obligation rows further down are written to be regime-neutral, so most of them survive
that edit unchanged.

## Applicability

Set per legal entity. If the solution spans entities, the strictest applicable regime
governs.

`triage.py` reads this table by its column **headings**, not by column order, so you may
reorder or add columns — but if you rename `Regime` or `Applies`, the run stops with an
error rather than guessing. A regime name in brackets is treated as a placeholder and never
applies. An obligation's `Regimes` column must name a regime **exactly** as it appears
here; alternatives separated by a spaced slash or dash count as the same regime
(`GDPR / UK GDPR` may be cited as `GDPR`), and a trailing version number is optional
(`PCI DSS 4.0` may be cited as `PCI DSS`). Anything else is reported as unmatched, because
an obligation citing a regime this table does not list can never become applicable.

| Regime | Scope | Applies | Entity scope |
|---|---|---|---|
| GDPR / UK GDPR | Personal data of EU / UK residents | `TBC` | |
| CCPA / CPRA | Personal data of California residents | `TBC` | |
| HIPAA | US protected health information | `TBC` | |
| PCI DSS 4.0 | Payment card data | `TBC` | |
| SOX — ITGC scope | US-listed companies, financial reporting systems | `TBC` | |
| NIS2 | EU essential and important entities | `TBC` | |
| EU AI Act | AI systems placed on the EU market | `TBC` | |
| EU Data Act — cloud switching | Customers of EU data processing services | `TBC` | |
| ISO/IEC 27001 | Certification commitment | `TBC` | |
| SOC 2 | Commitments made to your own customers | `TBC` | |
| ISO 22301 | Business continuity certification commitment | `TBC` | |
| NIST AI RMF / ISO/IEC 42001 | AI governance framework adopted internally | `TBC` | |
| `[add sector regulator]` | e.g. health, energy, telecoms, public sector, financial | `TBC` | |
| `[add national data-localisation law]` | | `TBC` | |

## Architecture-relevant obligations

What each obligation asks of a design, and therefore what the board asks. Populate the
internal control ID column so findings tie to your control library rather than to
regulation text. The `Regimes` column lists examples only; correct it to your register.

The generic entries — `sector rules`, `sector records rules`, `sector reporting rules`,
`data-localisation laws` — are deliberately not regimes in the Applicability table above.
They are prompts: **replace each with your own regulator or statute** when you populate
this file. Until you do, `triage.py` reports them as unmatched and the obligations citing
only them stay unassessable, which is the honest state.

| ID | Obligation | Regimes (examples) | Internal control | What the board asks |
|---|---|---|---|---|
| `OBL-RES-01` | Impact tolerance defined for the critical business service, and the design demonstrably able to remain within it | NIS2, ISO 22301, sector rules | `[TBD]` | "What is the tolerance, and what happens at minute 16?" |
| `OBL-RES-02` | Scenario testing including severe-but-plausible failure, evidenced | ISO 22301, NIS2 | `[TBD]` | "When did you last fail this over, and did you fail back?" |
| `OBL-RES-03` | Mapping of the service to its supporting resources and people | ISO 22301, NIS2 | `[TBD]` | "Show me the dependency map." |
| `OBL-TPR-01` | Third parties classified; critical arrangements registered and, where required, notified | NIS2, ISO/IEC 27001, SOC 2, sector rules | `[TBD]` | "Is this a critical supplier, and who classified it?" |
| `OBL-TPR-02` | Exit and substitutability plan for critical providers, tested | EU Data Act, sector rules | `[TBD]` | "If we had to leave this provider in 90 days, how?" |
| `OBL-TPR-03` | Concentration risk assessed, including region and provider concentration | NIS2, sector rules | `[TBD]` | "What else of ours dies with this same component?" |
| `OBL-TPR-04` | Contractual audit and access rights, including for regulators and subcontractors | GDPR, ISO/IEC 27001, sector rules | `[TBD]` | "Do we have right to audit, and does it flow down?" |
| `OBL-DAT-01` | Lawful basis, purpose limitation, minimisation; privacy impact assessment where high risk | GDPR, CCPA/CPRA, HIPAA | `[TBD]` | "Where is the DPIA?" |
| `OBL-DAT-02` | Cross-border transfer mechanism documented, including support and telemetry paths | GDPR, data-localisation laws | `[TBD]` | "Can a support engineer outside the region see this data?" |
| `OBL-DAT-03` | Retention and defensible disposal; immutable retention where records rules apply | GDPR, HIPAA, sector records rules | `[TBD]` | "How long, and can anyone delete it early?" |
| `OBL-DAT-04` | Payment card data scope minimised, segmentation evidenced | PCI DSS | `[TBD]` | "What is in scope, and what took it out of scope?" |
| `OBL-DAT-05` | Data quality, lineage and traceability for financial, statutory or regulatory reporting | SOX, sector reporting rules | `[TBD]` | "Can you trace a reported number back to source?" |
| `OBL-AUD-01` | Immutable audit trail of significant events, retained and reviewable | SOX, HIPAA, ISO/IEC 27001, SOC 2 | `[TBD]` | "Who changed this, when, and can they erase the record?" |
| `OBL-AUD-02` | Segregation of duties enforced technically, not only by process | SOX, ISO/IEC 27001, SOC 2 | `[TBD]` | "Can a developer change production data, or deploy unreviewed?" |
| `OBL-AUD-03` | Change management with evidence of approval and testing before production | SOX, SOC 2, ISO/IEC 27001 | `[TBD]` | "Show the approval for the last prod change." |
| `OBL-SEC-01` | Information security capability proportionate to threat; vulnerability and patch management | NIS2, ISO/IEC 27001, SOC 2 | `[TBD]` | "What is the patch SLA and who enforces it?" |
| `OBL-SEC-02` | Incident detection, classification and regulatory notification within deadline | GDPR, NIS2, HIPAA | `[TBD]` | "Who declares an incident, and what clock starts?" |
| `OBL-SEC-03` | Independent security testing before go-live | PCI DSS, sector rules | `[TBD]` | "Has it been pen tested, and were findings closed?" |
| `OBL-MDL-01` | Model inventory, validation, monitoring and human oversight | EU AI Act, NIST AI RMF, ISO/IEC 42001 | `[TBD]` | "Who validated the model, and who can override it?" |
| `OBL-MDL-02` | AI system risk classification and transparency obligations | EU AI Act | `[TBD]` | "What risk class, and does a user know?" |
| `OBL-TIM-01` | Clock synchronisation and timestamp granularity for audit and reportable events | PCI DSS, ISO/IEC 27001, sector rules | `[TBD]` | "What is your divergence from UTC?" |

## Reviewer rules

- Cite the obligation ID and the internal control ID. Cite regulation text only where it
  is already reproduced in this register.
- Never write "compliant" or "non-compliant" against a regime. Write: the obligation,
  what the design states, the gap, who owns closing it.
- Where a regime is `TBC`, report the obligation as unassessed and name Compliance as the
  owner of resolving applicability. That itself is a legitimate pre-review finding.
