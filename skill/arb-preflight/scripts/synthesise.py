#!/usr/bin/env python3
"""Deterministic Phase 4-5 synthesis for arb-preflight. Standard library only.

Reads the per-domain reviewer outputs and writes findings.json, preflight-report.md and
board-pack.md. The model supplies judgement in one small file (review.json); everything
mechanical is done here so it is identical on every run and every host:

  * coverage check per domain (one row per rule, triage-blocked rules included)
  * severity, decided in one place (see `Rubric`): rubric default resolved against the
    application's tier and context -> at most one level of adjustment -> Major cap last
  * root-cause grouping (from review.json), severity = highest member after adjustment
  * prior-review delta (closed / open / regressed, regressions raised one level), with
    closed findings carried into findings.json so the next review can detect a regression
  * waiver reconciliation (live -> waived; expired -> new Major)
  * verdict, counts, and rendering of the three artefacts

Usage:
    python3 synthesise.py <review-dir> [--prior <path/to/previous/findings.json>]

<review-dir> must contain triage.json, reviewers/<DOMAIN>.md for all seven domains, and
review.json (see templates/review-input.example.json). Exit codes: 0 written, 2 coverage
gaps (nothing written; re-dispatch the listed domains), 1 bad input.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import sys
from dataclasses import dataclass, field

DOMAINS = ["LZ", "SEC", "DAT", "RES", "INT", "OPS", "REG"]
NAMES = {"LZ": "Platform & Landing Zone", "SEC": "Security & Identity", "DAT": "Data & Privacy",
         "RES": "Resilience & Capacity", "INT": "Integration & Transaction Integrity",
         "OPS": "Operations, Cost & Lifecycle", "REG": "Regulatory & Third-Party"}
SEVS = ["Advisory", "Minor", "Major", "Blocker"]
REASONS = ["not stated in submission", "standard not populated", "artefact not supplied",
           "diagram not viewable", "regime applicability unconfirmed"]
RID = r"[A-Z]{2,3}-[A-Z0-9]{2,4}-\d{3}"
ANCHOR = re.compile(r"(Slide \d+(?: notes)?|§[\d.]+|media/[\w.-]+\.(?:png|jpe?g|gif)|NOT STATED)")
CLAUSE = re.compile(r"(?:LZB|SB|CT|OBL|PAT)-[A-Z0-9*]{1,4}(?:-(?:\d+|\*))?")
LIVE_STATUSES = ("open", "insufficient_information", "partially_addressed", "regressed")


# ---------------------------------------------------------------------------
# Severity scale
# ---------------------------------------------------------------------------


def index(sev: str) -> int:
    return SEVS.index(sev)


def bump(sev: str, up: bool = True) -> str:
    i = index(sev) + (1 if up else -1)
    return SEVS[max(0, min(i, len(SEVS) - 1))]


def worst(sevs) -> str:
    return max(sevs, key=index)


# ---------------------------------------------------------------------------
# Conditional rubric severities
# ---------------------------------------------------------------------------
#
# Most rubric rows carry a plain severity, but some are conditional on the application:
# "Blocker (T1)", "Blocker (internet-facing or T1)", "Blocker if any regressed",
# "Major; Blocker if migrating a live system with no non-prod before cutover". Reading
# those as a plain "Blocker" over-states every tier-3 application; reading them as the
# first word understates every tier-1 one. They are evaluated here instead.
#
# A condition is a disjunction of alternatives ("A or B"); each alternative is the
# conjunction of every predicate recognised inside it. A predicate that cannot be
# resolved from the facts leaves the severity at its base and emits a warning naming the
# `severity_context` flag that would settle it — the script never guesses.

TIER_RE = re.compile(r"\bT([1-4])\b|\btier\s*([1-4])\b", re.I)

CONDITION_PREDICATES = [
    (re.compile(r"internet[\s-]facing|public[\s-]facing", re.I), "internet_facing"),
    (re.compile(r"\bin scope\b|applicab", re.I), "regime_in_scope"),
    (re.compile(r"\bmigrat", re.I), "migrating"),
    (re.compile(r"regress", re.I), "prior_condition_regressed"),
    (re.compile(r"critical (?:provider|third|supplier)", re.I), "critical_providers"),
    (re.compile(r"no non[\s-]prod before cutover", re.I), "no_non_prod_before_cutover"),
    (re.compile(r"live system|live production", re.I), "live_system"),
    (re.compile(r"value[\s-]bearing|payment|regulated data", re.I), "value_bearing"),
    (re.compile(r"\bon hold\b|\bhold ring\b|\bis on Hold\b", re.I), "radar_hold"),
]

SEV_CLAUSE = re.compile(r"^(Blocker|Major|Minor|Advisory)\b[\s:(]*(.*?)\)?\s*$", re.I)


@dataclass
class Context:
    """The facts a conditional rubric severity is judged against.

    Everything here comes from review.json (`application`, `submission`,
    `severity_context`) or from the prior-review delta. `flags` lets the synthesiser
    state a fact the script cannot derive, such as whether the design is internet-facing.
    """

    tier: str = "UNKNOWN"
    change_type: str = "unknown"
    data_classes: list = field(default_factory=list)
    jurisdictions: list = field(default_factory=list)
    regimes_in_scope: list = field(default_factory=list)
    flags: dict = field(default_factory=dict)
    regressed_rules: set = field(default_factory=set)

    @classmethod
    def from_meta(cls, meta: dict) -> "Context":
        app = meta.get("application", {}) or {}
        sub = meta.get("submission", {}) or {}
        return cls(tier=str(app.get("tier", "UNKNOWN")).strip() or "UNKNOWN",
                   change_type=str(sub.get("change_type", "unknown")).lower(),
                   data_classes=list(app.get("data_classes", [])),
                   jurisdictions=list(app.get("jurisdictions", [])),
                   regimes_in_scope=list(app.get("regimes_in_scope", [])),
                   flags=dict(meta.get("severity_context", {}) or {}))

    def predicate(self, name: str):
        """True / False / None, where None means 'not knowable from the inputs'."""
        if name in self.flags:
            return bool(self.flags[name])
        if name == "regime_in_scope":
            return bool(self.regimes_in_scope)
        if name == "prior_condition_regressed":
            return bool(self.regressed_rules)
        if name == "migrating":
            return self.change_type == "migration"
        if name == "live_system":
            if self.change_type == "unknown":
                return None
            return self.change_type in ("migration", "material change", "uplift")
        if name == "value_bearing":
            # Stated-and-not-value-bearing is a real False. Only an unstated data-class
            # list is unknowable; collapsing both to None warns on every ordinary
            # application and leaves the condition permanently unresolved.
            if not self.data_classes:
                return None
            joined = " ".join(self.data_classes).lower()
            return any(w in joined for w in ("payment", "card", "transaction", "entitlement",
                                             "personal", "regulated"))
        return None

    def tier_matches(self, tiers: set) -> bool | None:
        if self.tier not in {"1", "2", "3", "4"}:
            return None
        return self.tier in tiers


def tier_set(text: str) -> set:
    return {m.group(1) or m.group(2) for m in TIER_RE.finditer(text)}


def condition_holds(cond: str, ctx: Context, log: list, label: str):
    """True / False / None for a rubric severity condition. None = cannot be evaluated."""
    unknown = []
    for alt in re.split(r"\bor\b", cond, flags=re.I):
        tests, names = [], []
        tiers = tier_set(alt)
        if tiers:
            tests.append(ctx.tier_matches(tiers))
            names.append(f"criticality tier (T{'/T'.join(sorted(tiers))})")
        for pattern, name in CONDITION_PREDICATES:
            if pattern.search(alt):
                tests.append(ctx.predicate(name))
                names.append(f"severity_context.{name}")
        if not tests:
            unknown.append(f"unrecognised condition '{alt.strip()}'")
            continue
        if any(t is False for t in tests):
            continue
        if any(t is None for t in tests):
            unknown += [n for n, t in zip(names, tests) if t is None]
            continue
        return True
    if unknown:
        log.append(f"{label}: conditional severity '{cond}' left at its base severity; "
                   f"cannot evaluate {', '.join(sorted(set(unknown)))}")
        return None
    return False


def parse_severity_spec(spec: str):
    """Split a rubric severity cell into (base, [(severity, condition)], unparsed)."""
    base, conds, leftover = None, [], []
    for clause in (c.strip() for c in (spec or "").split(";")):
        if not clause:
            continue
        m = SEV_CLAUSE.match(clause)
        if not m:
            leftover.append(clause)
            continue
        cond = re.sub(r"^(?:if|for|when|where)\s+", "", m.group(2).strip().strip("()").strip(),
                      flags=re.I)
        if cond:
            conds.append((m.group(1).title(), cond))
        else:
            base = m.group(1).title()
    return base, conds, leftover


def resolve_spec(spec: str, ctx: Context, log: list, label: str) -> str:
    """The rubric default severity for one rule, resolved against this application."""
    base, conds, leftover = parse_severity_spec(spec)
    if base is None:
        if conds:
            # "Blocker (T1)" states only the escalated case. An application the
            # condition does not cover sits one level below it, not at Advisory.
            base = bump(worst(s for s, _ in conds), up=False)
        else:
            base = "Major"
            log.append(f"{label}: severity '{spec.strip()}' is not a severity "
                       f"(it defers to another document); treated as Major")
    elif leftover:
        log.append(f"{label}: ignored unparsed severity text '{'; '.join(leftover)}'")
    sev = base
    for cond_sev, cond in conds:
        if condition_holds(cond, ctx, log, label) and index(cond_sev) > index(sev):
            sev = cond_sev
    return sev


# ---------------------------------------------------------------------------
# Rubric: the only place severity is decided
# ---------------------------------------------------------------------------


@dataclass
class Decision:
    severity: str
    base: str
    provisional: bool
    capped: bool
    reason: str = ""


@dataclass
class Rubric:
    """Rubric rows and ceilings from triage.json, plus the severity pipeline.

    Severity is decided in exactly two calls, in this order, and nowhere else:

      `for_raw`    rubric default (resolved against `Context`) -> at most one level of
                   adjustment from the reviewer -> no cap yet.
      `finalise`   base = worst member of the root-cause group -> at most one level of
                   adjustment from the synthesiser's override or a regression -> the
                   Major cap for provisional standards, applied last.

    An adjustment never moves more than one level, escalation beats de-escalation so a
    regression cannot be softened away, and the cap is last so that a provisional
    standard can never produce a Blocker by any route.
    """

    rows: dict = field(default_factory=dict)
    blocked: dict = field(default_factory=dict)
    standards_state: dict = field(default_factory=dict)
    context: Context = field(default_factory=Context)
    _defaults: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_triage(cls, triage: dict, context: Context) -> "Rubric":
        rows, blocked = {}, {}
        for dom, d in triage["domains"].items():
            for a in d["assess"]:
                rows[a["rule_id"]] = {**a, "domain": dom}
            for b in d["blocked"]:
                blocked[b["rule_id"]] = {**b, "domain": dom}
        return cls(rows=rows, blocked=blocked,
                   standards_state=triage.get("standards_state", {}), context=context)

    def rules_for(self, dom: str) -> list:
        return [r for r, v in self.rows.items() if v["domain"] == dom] + \
               [r for r, v in self.blocked.items() if v["domain"] == dom]

    def row(self, rule_id: str) -> dict:
        return self.rows.get(rule_id, {})

    def default_severity(self, rule_id: str, log: list) -> str | None:
        """Rubric default for a rule, resolved for this application. Warns once."""
        if rule_id not in self.rows:
            return None
        if rule_id not in self._defaults:
            self._defaults[rule_id] = resolve_spec(
                self.rows[rule_id].get("severity_default", ""), self.context, log, rule_id)
        return self._defaults[rule_id]

    def invalidate(self) -> None:
        """Drop the resolved defaults so a later change to `context` is picked up.

        `default_severity` memoises, and a conditional cell such as
        `Blocker if any regressed` resolves differently once the prior-review delta is
        known. Anything that completes `context` must call this before the resolved
        severities are read, or the stale answer is served for the rest of the run.
        """
        self._defaults.clear()

    def provisional(self, rule_id: str) -> bool:
        return str(self.row(rule_id).get("ceiling", "")).startswith("Major")

    def _adjust(self, base: str, requests: list, log: list, label: str) -> tuple:
        """Apply at most one level of movement from `base`. Escalation wins."""
        up = [(index(s) - index(base), r) for s, r in requests if s and index(s) > index(base)]
        down = [(index(s) - index(base), r) for s, r in requests if s and index(s) < index(base)]
        for delta, reason in up + down:
            if abs(delta) > 1:
                log.append(f"{label}: {reason} asks for {abs(delta)} levels from the rubric "
                           f"default {base}; clamped to one level")
        # Escalation beats de-escalation, so a regression cannot be softened away.
        if up:
            return bump(base, up=True), max(up, key=lambda t: t[0])[1]
        if down:
            return bump(base, up=False), min(down, key=lambda t: t[0])[1]
        return base, ""

    def _cap(self, sev: str, rule_ids, reason: str) -> tuple:
        if any(self.provisional(r) for r in rule_ids):
            if sev == "Blocker":
                return "Major", True, "capped at Major: governing standard is [DEFAULT — CONFIRM]"
            return sev, False, reason
        return sev, False, reason

    def for_raw(self, x: dict, log: list) -> Decision:
        """Rubric default plus the reviewer's one-level adjustment. No cap yet."""
        rule = x["rule_id"]
        base = self.default_severity(rule, log)
        if base is None:                      # rule_id NONE: no rubric row to anchor to
            return Decision(x["severity"], x["severity"], False, False, "")
        requests = []
        if x["severity"] != base:
            if x.get("severity_note"):
                requests.append((x["severity"], f"reviewer: {x['severity_note']}"))
            else:
                log.append(f"{rule}: reviewer filed {x['severity']} but the rubric default "
                           f"for this application is {base} and no reason was given; "
                           f"using {base}")
        sev, reason = self._adjust(base, requests, log, rule)
        return Decision(sev, base, self.provisional(rule), False, reason)

    def finalise(self, group: "Group", regressed: bool, log: list) -> Decision:
        """Group severity, the synthesiser's adjustment, the regression bump, then the cap."""
        members = group.all()
        rule_ids = [m["rule_id"] for m in members]
        base = worst(m["severity"] for m in members)
        label = group.primary["rule_id"]

        requests = []
        if group.meta.get("severity"):
            requests.append((group.meta["severity"].title(),
                             f"review.json group override ({group.meta.get('reason', 'no reason given')})"))
        if regressed:
            requests.append((bump(base, up=True), "regressed since the prior review"))
        sev, reason = self._adjust(base, requests, log, label)

        if len(members) > 1 and not reason:
            reason = "highest severity among the grouped findings"
        sev, capped, reason = self._cap(sev, rule_ids, reason)
        provisional = any(self.provisional(r) for r in rule_ids) or \
            any(m.get("provisional") for m in members)
        return Decision(sev, base, provisional, capped, reason)


# ---------------------------------------------------------------------------
# Reviewer output parsing
# ---------------------------------------------------------------------------


def section(text: str, name: str) -> str:
    m = re.search(r"^### " + re.escape(name) + r"\s*$(.*?)(?=^### |\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def field_of(block: str, name: str) -> str:
    m = re.search(r"\*\*" + name + r":\*\*\s*(.+)", block)
    return m.group(1).strip() if m else ""


def table_ids(text: str) -> list:
    return re.findall(r"^\|\s*`?(" + RID + r")`?\s*\|", text, re.M)


def parse_reviewer(path: pathlib.Path, dom: str, log: list):
    text = path.read_text(encoding="utf-8")
    findings = []
    for blk in re.split(r"^(?=#### )", section(text, "Findings"), flags=re.M):
        m = re.match(r"#### `?(" + RID + r"|NONE)`?\s*[—–-]\s*(.+)", blk)
        if not m:
            continue
        sev_txt = field_of(blk, "Severity")
        sev = next((s for s in SEVS if sev_txt.lower().startswith(s.lower())), None)
        if not sev:
            log.append(f"{dom} {m.group(1)}: unreadable severity '{sev_txt[:40]}', treated as Major")
            sev = "Major"
        # Anything the reviewer wrote after the severity word, minus the provisional
        # marker, is their justification for moving off the rubric default. A bare
        # severity is an echo of the rubric and is not treated as an adjustment: the
        # reviewer sees the unresolved cell ("Blocker (T1)") and has to pick one word
        # from it, so a bare word carries no intent to move.
        tail = re.sub(r"\(?\s*\+?\s*provisional standard\s*\)?", "", sev_txt[len(sev):],
                      flags=re.I)
        sev_note = tail.strip(" ()[]—–-·,;:.")
        ev_txt = field_of(blk, "Evidence")
        anchors = list(dict.fromkeys(ANCHOR.findall(ev_txt))) or ["NOT STATED"]
        conf = (field_of(blk, "Confidence").split() or ["Medium"])[0].strip(".,;")
        findings.append({
            "rule_id": m.group(1), "domain": dom, "title": m.group(2).strip()[:120],
            "severity": sev, "severity_note": sev_note,
            "provisional": "provisional" in sev_txt.lower(),
            "status": "insufficient_information" if "insufficient" in field_of(blk, "Status").lower() else "open",
            "standard": field_of(blk, "Standard"), "evidence_text": ev_txt, "anchors": anchors,
            "impact": field_of(blk, "Impact"), "remediation": field_of(blk, "Remediation"),
            "owner": field_of(blk, "Owner") or "UNASSIGNED",
            "confidence": conf if conf in ("High", "Medium", "Low") else "Medium"})
    met = table_ids(section(text, "Assessed and met"))
    na = []
    for row in re.findall(r"^\|\s*`?(" + RID + r")`?\s*\|([^\n]*)$", section(text, "Not assessable"), re.M):
        cells = [c.strip() for c in row[1].strip().strip("|").split("|")]
        low = " ".join(cells).lower()
        reason = next((r for r in REASONS if r in low), "not stated in submission")
        na.append({"rule_id": row[0], "domain": dom, "reason": reason,
                   "detail": (cells[1] if len(cells) > 1 else cells[0])[:300],
                   "owner": cells[2][:120] if len(cells) > 2 else "UNASSIGNED"})
    return findings, met, na


@dataclass
class Coverage:
    findings: list = field(default_factory=list)
    met: dict = field(default_factory=dict)
    not_assessable: list = field(default_factory=list)
    rubric_count: dict = field(default_factory=dict)
    gaps: dict = field(default_factory=dict)


def collect_reviewers(review_dir: pathlib.Path, rubric: Rubric, log: list) -> Coverage:
    """One row per rule per domain, or a gap list. Triage is authoritative for blocked rules."""
    cov = Coverage()
    for dom in DOMAINS:
        rules = rubric.rules_for(dom)
        blocked = {r: v for r, v in rubric.blocked.items() if v["domain"] == dom}
        cov.rubric_count[dom] = len(rules)
        path = review_dir / "reviewers" / f"{dom}.md"
        if not path.exists():
            cov.gaps[dom] = ["reviewer output missing"]
            continue
        f, m, n = parse_reviewer(path, dom, log)
        for x in [x for x in f if x["rule_id"] in blocked]:
            log.append(f"{dom} {x['rule_id']}: raised as a finding but its standard is not "
                       f"populated; reported as not assessable")
        f = [x for x in f if x["rule_id"] not in blocked]
        m = [r for r in m if r not in blocked]
        n = [x for x in n if x["rule_id"] not in blocked]
        n += [{"rule_id": r, "domain": dom, "reason": "standard not populated",
               "detail": b["detail"][:300]} for r, b in blocked.items()]
        seen = [x["rule_id"] for x in f if x["rule_id"] != "NONE"] + m + [x["rule_id"] for x in n]
        missing = sorted(set(rules) - set(seen))
        dups = sorted({r for r in seen if seen.count(r) > 1})
        extra = sorted(set(seen) - set(rules))
        if missing or dups or extra:
            cov.gaps[dom] = ([f"missing {missing}"] if missing else []) + \
                            ([f"listed twice {dups}"] if dups else []) + \
                            ([f"unknown {extra}"] if extra else [])
        cov.findings += f
        cov.met[dom] = len(m)
        cov.not_assessable += n
    return cov


def print_gaps(gaps: dict) -> None:
    print("COVERAGE GAPS — re-dispatch these domains, nothing written:")
    for d, g in gaps.items():
        print(f"  {d}: {'; '.join(g)}")


# ---------------------------------------------------------------------------
# Silence rule, grouping
# ---------------------------------------------------------------------------


def apply_silence_rule(findings: list, na: list, rubric: Rubric, log: list):
    """Where a rule the submission is silent on is filed, decided by rubric severity.

    Blocker/Major -> Findings (the board must see it). Minor/Advisory -> the pre-read gap
    list. Enforced here so the result does not depend on which way a reviewer filed it.
    """
    raw, na = list(findings), list(na)
    promoted, demoted = [], []

    for n in [n for n in na if n["reason"] == "not stated in submission"]:
        sev = rubric.default_severity(n["rule_id"], log)
        if sev not in ("Blocker", "Major"):
            continue
        row = rubric.row(n["rule_id"])
        na.remove(n)
        raw.append({"rule_id": n["rule_id"], "domain": n["domain"],
                    "title": ("Not stated: " + row.get("check", n["rule_id"]))[:120],
                    "severity": sev, "provisional": False, "status": "insufficient_information",
                    "standard": row.get("standard", ""),
                    "evidence_text": "NOT STATED — " + n.get("detail", ""),
                    "anchors": ["NOT STATED"],
                    "impact": "The board cannot confirm this control; it is treated as unmet until shown.",
                    "remediation": "Provide: " + (row.get("evidence_needed") or "evidence for this check"),
                    "owner": n.get("owner") or "UNASSIGNED", "confidence": "High",
                    "silent_promoted": True})
        promoted.append(n["rule_id"])

    for x in [x for x in raw if x["status"] == "insufficient_information" and x["rule_id"] != "NONE"]:
        if rubric.default_severity(x["rule_id"], log) in ("Minor", "Advisory"):
            raw.remove(x)
            na.append({"rule_id": x["rule_id"], "domain": x["domain"],
                       "reason": "not stated in submission", "detail": x["title"][:300],
                       "owner": x["owner"]})
            demoted.append(x["rule_id"])

    if promoted:
        log.append(f"silence rule: {len(promoted)} silent Blocker/Major rules moved from "
                   f"Not assessable to Findings")
    if demoted:
        log.append(f"silence rule: {len(demoted)} silent Minor/Advisory findings moved to "
                   f"Not assessable: {demoted}")
    return raw, na


def resolve_severities(raw: list, rubric: Rubric, log: list) -> None:
    """Set each raw finding's pre-group severity. The Major cap is deliberately not
    applied here: it belongs after grouping and adjustment, in `Rubric.finalise`."""
    for x in raw:
        d = rubric.for_raw(x, log)
        x["rubric_severity"], x["severity"] = d.base, d.severity
        x["severity_reason"] = d.reason
        x["provisional"] = x.get("provisional") or d.provisional


@dataclass
class Group:
    primary: dict
    members: list = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    def all(self) -> list:
        return [self.primary, *self.members]


def group_root_causes(raw: list, groups_meta: list, log: list) -> list:
    """Merge the synthesiser's root-cause groups; everything else stands alone."""
    by_rule: dict = {}
    for x in raw:
        by_rule.setdefault(x["rule_id"], []).append(x)
    groups, used = [], set()
    for g in groups_meta:
        wanted = [g["primary"], *g.get("members", [])]
        members = [by_rule[r][0] for r in wanted if r in by_rule]
        if not members:
            log.append(f"group {g['primary']}: no matching findings, ignored")
            continue
        for r in wanted:
            if r not in by_rule:
                log.append(f"group {g['primary']}: member {r} not raised by any reviewer")
        groups.append(Group(members[0], members[1:], g))
        used |= {id(m) for m in members}
    groups += [Group(x) for x in raw if id(x) not in used]
    groups.sort(key=lambda gr: -index(worst(m["severity"] for m in gr.all())))
    return groups


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------


def parse_waivers(folder: pathlib.Path) -> list:
    out = []
    for f in sorted(folder.glob("*.md")) if folder.is_dir() else []:
        t = f.read_text(encoding="utf-8")

        def cell(k, text=t):
            m = re.search(r"\|\s*\*\*" + k + r"\*\*\s*\|\s*([^|]+)\|", text)
            return m.group(1).strip() if m else ""

        out.append({"id": cell("Waiver ID") or f.stem, "finding": cell("Finding"),
                    "rule": cell("Rule"), "expires": cell("Expires")[:10],
                    "status": cell("Status").lower()})
    return out


class IdAllocator:
    """Finding IDs are never reused, so a closed F-012 cannot come back as something else.

    The high-water mark is the highest ID ever issued for this application, read from the
    prior findings.json (`review.id_high_water`, with every id in the file as a floor) —
    not from the open findings alone, which drops every id that has since closed.
    """

    def __init__(self, prior: dict | None) -> None:
        ids = [f.get("id", "") for f in (prior or {}).get("findings", [])]
        used = [int(i[2:]) for i in ids if re.fullmatch(r"F-\d{3,}", i)]
        recorded = int((prior or {}).get("review", {}).get("id_high_water", 0) or 0)
        self.high = max([recorded, *used] or [0])

    def next(self) -> str:
        self.high += 1
        return f"F-{self.high:03d}"


@dataclass
class Inputs:
    review_dir: pathlib.Path
    skill: pathlib.Path
    triage: dict
    meta: dict
    prior: dict | None
    prior_path: str | None
    waivers: list
    today: str
    context: Context


def parse_args(argv: list | None = None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("review_dir")
    ap.add_argument("--prior", help="previous findings.json for the same application")
    ap.add_argument("--skill", default=str(pathlib.Path(__file__).resolve().parent.parent))
    return ap.parse_args(argv)


def load_inputs(args) -> Inputs:
    rd = pathlib.Path(args.review_dir)
    triage = json.loads((rd / "triage.json").read_text(encoding="utf-8"))
    meta = json.loads((rd / "review.json").read_text(encoding="utf-8"))
    prior = json.loads(pathlib.Path(args.prior).read_text(encoding="utf-8")) if args.prior else None
    return Inputs(review_dir=rd, skill=pathlib.Path(args.skill), triage=triage, meta=meta,
                  prior=prior, prior_path=args.prior,
                  waivers=parse_waivers(rd.parent / "waivers"),
                  today=meta.get("review_date") or dt.date.today().isoformat(),
                  context=Context.from_meta(meta))


def prior_by_rule(prior: dict | None) -> dict:
    return {p["rule_id"]: p for p in (prior or {}).get("findings", []) if p.get("rule_id") != "NONE"}


def detect_regressions(raw: list, prior: dict | None) -> set:
    """Rules closed by a previous review and raised again by this one."""
    closed = {r for r, p in prior_by_rule(prior).items() if p.get("status") == "closed"}
    return {x["rule_id"] for x in raw} & closed


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------


def build_findings(groups: list, rubric: Rubric, inputs: Inputs, log: list):
    prior = prior_by_rule(inputs.prior)
    ids = IdAllocator(inputs.prior)
    today, waivers = inputs.today, inputs.waivers
    # Who has committed to fix what, by when. Keyed by finding id or by rule id, so a
    # commitment survives a re-review even when the finding is renumbered. Without this
    # there is no way to put an owner and a date on a finding that is not in a group, and
    # `Ready with conditions` is unreachable. See decide_verdict.
    commitments = inputs.meta.get("commitments", {}) or {}
    findings, delta = [], []

    for group in groups:
        primary, members = group.primary, group.members
        p = prior.get(primary["rule_id"])
        regressed = bool(p) and p.get("status") == "closed"
        d = rubric.finalise(group, regressed, log)

        if p:
            fid, first = p["id"], p.get("first_raised", today)
            status = "regressed" if regressed else primary["status"]
            delta.append((fid, p.get("status", "open"), status, primary["rule_id"]))
        else:
            fid, first, status = ids.next(), today, primary["status"]

        f = {"id": fid, "rule_id": primary["rule_id"], "domain": primary["domain"],
             "title": group.meta.get("title", primary["title"])[:120],
             "severity": d.severity, "status": status,
             "provisional_standard": d.provisional,
             "standard_ref": sorted(set(CLAUSE.findall(
                 " ".join([primary["standard"]] + [m["standard"] for m in members])))),
             "evidence": [{"anchor": a} for a in primary["anchors"]],
             "impact": primary["impact"], "remediation": primary["remediation"],
             "owner": primary["owner"], "confidence": primary["confidence"],
             "first_raised": first, "last_seen": today,
             "board_condition": d.severity in ("Blocker", "Major")}
        f["evidence"][0]["quote"] = primary["evidence_text"][:300]
        # `from` is always the rubric default for the primary rule, so the report shows
        # the whole movement rather than the last hop of it.
        from_sev = primary.get("rubric_severity") or d.base
        if d.severity != from_sev:
            reasons = [r for r in (primary.get("severity_reason"), d.reason) if r]
            f["severity_adjusted"] = {
                "from": from_sev,
                "direction": "up" if index(d.severity) > index(from_sev) else "down",
                "reason": "; ".join(reasons) or "highest severity among the grouped findings"}
        notes = []
        if members:
            notes.append("Root cause of: " + ", ".join(m["rule_id"] for m in members))
        if group.meta.get("note"):
            notes.append(group.meta["note"])
        if notes:
            f["notes"] = "; ".join(notes)
        if due := group.meta.get("due_date"):
            f["due_date"] = due
        # A per-finding commitment is more specific than a group's, so it wins.
        for key in (fid, f["rule_id"]):
            if c := commitments.get(key):
                f["owner"] = c.get("owner") or f["owner"]
                f["due_date"] = c.get("due") or f.get("due_date", "")
                if not f["due_date"]:
                    f.pop("due_date")
                break
        for w in waivers:
            if (w["finding"] == fid or w["rule"] == f["rule_id"]) and \
                    w["status"] == "approved" and w["expires"] >= today:
                f["status"], f["waiver_id"], f["waiver_expires"] = "waived", w["id"], w["expires"]
        findings.append(f)

    for w in waivers:
        if w["status"] in ("approved", "expired") and w["expires"] and w["expires"] < today:
            findings.append({"id": ids.next(), "rule_id": "OPS-GOV-004", "domain": "OPS",
                             "title": f"Waiver {w['id']} expired {w['expires']}",
                             "severity": "Major", "status": "open",
                             "evidence": [{"anchor": f"waivers/{w['id']}.md"}],
                             "impact": "A time-boxed risk acceptance has lapsed without review.",
                             "remediation": "Close the gap, or re-approve the waiver with a new expiry.",
                             "owner": "Risk owner", "first_raised": today, "last_seen": today,
                             "board_condition": True})

    # Carry the prior review's resolved findings forward as `closed` rather than dropping
    # them. A dropped finding cannot be shown to have regressed next time, and its id
    # would be handed to an unrelated finding.
    current = {f["rule_id"] for f in findings}
    for rule, p in prior.items():
        if rule in current:
            continue
        carried = {**p, "status": "closed", "board_condition": False, "last_seen": today}
        carried.pop("waiver_id", None)
        carried.pop("waiver_expires", None)
        if p.get("status") != "closed":
            carried["closed_in"] = today
            delta.append((p["id"], p.get("status", "open"), "closed", rule))
        findings.append(carried)

    return findings, delta, ids.high


def is_live(f: dict) -> bool:
    return f.get("status") in LIVE_STATUSES


# ---------------------------------------------------------------------------
# Verdict and document
# ---------------------------------------------------------------------------


def count_severities(findings: list) -> dict:
    return {s.lower(): sum(1 for f in findings if f["severity"] == s and is_live(f)) for s in SEVS}


def uncommitted_majors(findings: list) -> list:
    """Live Majors with no named owner or no date. A condition nobody owns is not one."""
    return [f["id"] for f in findings if f["severity"] == "Major" and is_live(f) and
            (f.get("owner", "UNASSIGNED").startswith("UNASSIGNED") or not f.get("due_date"))]


def decide_verdict(findings: list, na: list, rubric: Rubric, meta: dict, log: list) -> tuple:
    """`(verdict, uncommitted Major ids)`.

    Waived findings are not live, so they do not count towards the verdict: a waiver is a
    recorded risk acceptance by the organisation. It is named in both artefacts instead, so
    it can never change the recommendation silently.
    """
    count = count_severities(findings)
    assessable = len(rubric.rows)
    not_stated = sum(1 for n in na if n["reason"] != "standard not populated")
    if meta.get("intake_failed"):
        return "Insufficient information", []
    if count["blocker"]:
        return "Not ready - rework", []
    if assessable and not_stated / assessable > 1 / 3:
        return "Insufficient information", []
    if count["major"]:
        # `Ready with conditions` means handing the board conditions it can hold someone
        # to. A Major with no owner or no date is not a condition, so the verdict is
        # withheld rather than granted over an uncommitted list.
        uncommitted = uncommitted_majors(findings)
        if uncommitted:
            log.append("Ready with conditions requires a named owner and a date on every "
                       f"Major; missing on {uncommitted}. Verdict held at Insufficient "
                       "information — supply them in review.json `commitments` and re-run.")
            return "Insufficient information", uncommitted
        return "Ready with conditions", []
    return "Ready", []


def resolve_contradictions(items: list, findings: list, log: list) -> list:
    """Allow review.json to reference a contradiction's finding by rule_id instead of F-id."""
    by_rule: dict = {}
    for f in findings:
        by_rule.setdefault(f["rule_id"], f["id"])
        for r in f.get("notes", "").replace("Root cause of: ", "").split(";")[0].split(", "):
            by_rule.setdefault(r.strip(), f["id"])
    out = []
    for c in items:
        c = dict(c)
        rule = c.pop("rule_id", None)
        if rule and "finding_id" not in c:
            if rule in by_rule:
                c["finding_id"] = by_rule[rule]
            else:
                log.append(f"contradiction '{c.get('claim', '')[:40]}': rule {rule} has no finding")
        out.append(c)
    return out


def build_document(inputs: Inputs, rubric: Rubric, findings: list, na: list, met: dict,
                   verdict: str, high_water: int, log: list) -> dict:
    meta, today = inputs.meta, inputs.today
    app = meta.get("application", {})
    count = count_severities(findings)
    review = {"date": today, "verdict": verdict,
              "standards_state": rubric.standards_state, "domains_reviewed": DOMAINS,
              "id_high_water": high_water}
    if inputs.prior_path:
        review["previous_review"] = inputs.prior_path
    review.update({k: meta[k] for k in ("board_date", "target_go_live") if meta.get(k)})
    return {
        "schema_version": "1.0",
        "application": {"name": app.get("name", "UNKNOWN"),
                        "criticality_tier": str(app.get("tier", "UNKNOWN")),
                        "tier_source": app.get("tier_source", "unknown"),
                        "business_owner": app.get("business_owner", "NOT STATED"),
                        "technical_owner": app.get("technical_owner", "NOT STATED"),
                        "data_classes": app.get("data_classes", []),
                        "jurisdictions": app.get("jurisdictions", []),
                        "regimes_in_scope": app.get("regimes_in_scope", [])},
        "submission": meta.get("submission", {"files": ["UNKNOWN"]}),
        "review": review,
        "summary": {**count, "not_assessable": len(na), "met": sum(met.values()),
                    "waived": sum(1 for f in findings if f["status"] == "waived"),
                    "regressed": sum(1 for f in findings if f["status"] == "regressed"),
                    "closed": sum(1 for f in findings if f["status"] == "closed")},
        "findings": findings,
        "contradictions": resolve_contradictions(meta.get("contradictions", []), findings, log),
        "not_assessable": na,
        "submission_integrity": meta.get("submission_integrity", []),
    }


@dataclass
class ReportContext:
    doc: dict
    meta: dict
    raw: list
    met: dict
    na: list
    rubric: dict
    delta: list
    assessable: int
    verdict: str
    uncommitted: list = field(default_factory=list)

    @property
    def live(self) -> list:
        """Everything the artefacts show: open findings plus waived ones, which are
        reported rather than hidden even though they do not count towards the verdict."""
        return [f for f in self.doc["findings"] if is_live(f) or f["status"] == "waived"]

    def outstanding(self, severity: str) -> list:
        """Findings of `severity` that still count: waived ones are excluded, because the
        verdict excludes them and a table that disagrees with the verdict is worse than
        either. They are listed under the waiver sections instead."""
        return [f for f in self.live if f["severity"] == severity and f["status"] != "waived"]

    def waived(self, severity: str | None = None) -> list:
        return [f for f in self.live if f["status"] == "waived"
                and (severity is None or f["severity"] == severity)]


def write_outputs(review_dir: pathlib.Path, doc: dict, ctx: ReportContext) -> None:
    (review_dir / "findings.json").write_text(
        json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    (review_dir / "preflight-report.md").write_text(render_report(ctx), encoding="utf-8")
    (review_dir / "board-pack.md").write_text(render_board(ctx), encoding="utf-8")


def print_summary(doc: dict, raw: list, coverage: Coverage, log: list) -> None:
    print(f"verdict: {doc['review']['verdict']}")
    print("counts:", dict(doc["summary"]))
    live = [f for f in doc["findings"] if is_live(f) or f["status"] == "waived"]
    rows = sum(1 for x in raw if x["rule_id"] != "NONE") + sum(coverage.met.values()) + \
        len(doc["not_assessable"])
    print(f"raw findings {len(raw)} -> root causes {len(live)}; coverage "
          f"{rows} rows over {sum(coverage.rubric_count.values())} rules")
    for w in dict.fromkeys(log):          # a severity may be resolved twice; warn once
        print("WARNING:", w)


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def plural(n: int, one: str, many: str) -> str:
    return one if n == 1 else many


def tbl(head, rows) -> str:
    return "\n".join(["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] +
                     ["| " + " | ".join(str(c).replace("|", "/").replace("\n", " ") for c in r)
                      + " |" for r in rows])


def render_report(ctx: ReportContext) -> str:
    doc, meta, raw, met, na = ctx.doc, ctx.meta, ctx.raw, ctx.met, ctx.na
    a, s, F = doc["application"], doc["summary"], ctx.live
    sub = doc["submission"]
    snp = sum(1 for n in na if n["reason"] == "standard not populated")
    prov = [f for f in ctx.outstanding("Major") if f.get("provisional_standard")]
    std = ", ".join(f"{k} = {v}" for k, v in doc["review"]["standards_state"].items())
    L = [f"# ARB Pre-flight Review — {a['name']}", "",
         "> This is a pre-review produced ahead of the architecture review board (ARB). It is a",
         "> **recommendation, not an approval**. The board decides.", "",
         tbl(["", ""], [["**Application**", a["name"]],
                        ["**Submission**", f"{', '.join(sub.get('files', []))} v{sub.get('version', '?')}, dated {sub.get('dated', '?')}"],
                        ["**Criticality tier**", f"{a['criticality_tier']} ({a['tier_source']})"],
                        ["**Data classes**", ", ".join(a["data_classes"]) or "NOT STATED"],
                        ["**Jurisdictions / entities**", ", ".join(a["jurisdictions"]) or "NOT STATED"],
                        ["**Change type**", sub.get("change_type", "unknown")],
                        ["**Business owner**", a["business_owner"]], ["**Technical owner**", a["technical_owner"]],
                        ["**Target go-live**", meta.get("target_go_live_text", doc["review"].get("target_go_live", "NOT STATED"))],
                        ["**Board date**", doc["review"].get("board_date", "NOT STATED")],
                        ["**Reviewed**", doc["review"]["date"]],
                        ["**Material assessed**", f"{sub.get('slides', '?')} slides, {sub.get('words', '?')} words, "
                                                  f"{sub.get('viewable_diagrams', '?')} viewable diagrams, {sub.get('unreadable_diagrams', 0)} unreadable"],
                        ["**Standards baseline**", std]]), "",
         "## Recommendation", "", f"**{ctx.verdict}**", "", meta.get("summary", ""), ""] + \
        (["", f"**{len(ctx.uncommitted)} Major{plural(len(ctx.uncommitted), '', 's')} "
          f"carr{plural(len(ctx.uncommitted), 'ies', 'y')} no named owner and date**, so "
          "`Ready with conditions` cannot be recommended: a condition nobody owns by a "
          "stated date is not something the board can hold anyone to. Supply them in "
          "`review.json` under `commitments` and re-run.", "",
          "Uncommitted: " + ", ".join(ctx.uncommitted), ""] if ctx.uncommitted else []) + \
        [
         tbl(["Severity", "Count"], [[k.title(), s[k]] for k in ("blocker", "major", "minor", "advisory")] +
             [["Not assessable", s["not_assessable"]], ["Assessed and met", s["met"]]]), "",
         f"{len(raw)} raw findings from seven reviewers, deduplicated to {len(F)} root causes. "
         f"{len(prov)} Majors rest on `[DEFAULT — CONFIRM]` clauses and are provisional; confirming "
         f"the baselines lifts the cap.", ""]
    if meta.get("fix_before_board"):
        L += ["## Fix before the board", "",
              tbl(["#", "Action", "Closes", "Owner", "Effort"],
                  [[i, x["action"], ", ".join(x.get("closes", [])), x.get("owner", ""), x.get("effort", "")]
                   for i, x in enumerate(meta["fix_before_board"], 1)]), ""]
    by_dom = {d: [n for n in na if n["domain"] == d] for d in DOMAINS}
    L += ["## Pre-read gaps", "", meta.get("pre_read_note", ""), "",
          tbl(["Domain", "Not stated in submission", "Standard not populated"],
              [[NAMES[d], sum(1 for n in v if n["reason"] != "standard not populated"),
                sum(1 for n in v if n["reason"] == "standard not populated")] for d, v in by_dom.items()]), "",
          f"**{snp} of {s['not_assessable']} unassessable rules are blocked by unpopulated standards**, "
          f"owned by the standard's owner in `standards/README.md`, not by the submitting team.", ""]
    if doc["contradictions"]:
        L += ["## Design inconsistencies", "",
              tbl(["#", "Claim", "Conflicting evidence", "Finding"],
                  [[i, f"{c['claim']} ({c.get('claim_anchor', '')})", f"{c['conflict']} ({c.get('conflict_anchor', '')})",
                    c.get("finding_id", "")] for i, c in enumerate(doc["contradictions"], 1)]), ""]
    if ctx.delta:
        L += ["## Prior review delta", "", tbl(["Finding", "Rule", "Previous", "Now"],
                                               [[d[0], d[3], d[1], d[2]] for d in ctx.delta]),
              "", "Regressed findings are raised one severity level automatically. Closed "
                  "findings stay in `findings.json` so a later regression is detectable.", ""]
    L += ["## Blockers", ""]
    for f in ctx.outstanding("Blocker"):
        L += [f"### {f['id']} {f['rule_id']} — {f['title']}", "",
              f"- **Domain:** {NAMES[f['domain']]} · **Status:** {f['status']}",
              f"- **Standard:** {', '.join(f.get('standard_ref', [])) or 'rubric / intake'}",
              f"- **Evidence:** {f['evidence'][0].get('quote', f['evidence'][0]['anchor'])}",
              f"- **Impact:** {f['impact']}", f"- **Remediation:** {f['remediation']}",
              f"- **Owner:** {f.get('owner', 'UNASSIGNED')} — **Due:** {f.get('due_date', 'TBC')} · "
              f"**Confidence:** {f.get('confidence', 'Medium')}"] + \
             ([f"- {f['notes']}"] if f.get("notes") else []) + [""]
    if not ctx.outstanding("Blocker"):
        L += ["None outstanding.", ""]
    if wb := ctx.waived("Blocker"):
        L += [f"**{len(wb)} Blocker-severity finding{plural(len(wb), '', 's')} "
              f"{plural(len(wb), 'is', 'are')} covered by a live waiver** and excluded from "
              "the recommendation above. The risk is accepted, not resolved.", "",
              tbl(["Waiver", "Finding", "Rule", "Expires", "Finding title"],
                  [[f["waiver_id"], f["id"], f["rule_id"], f["waiver_expires"], f["title"]]
                   for f in wb]), ""]
    majors = ctx.outstanding("Major")
    evidenced = [f for f in majors if f["status"] != "insufficient_information"]
    silent = [f for f in majors if f["status"] == "insufficient_information"]
    L += ["## Majors", "", f"{len(majors)} Majors: {len(evidenced)} where the submission shows a gap, "
          f"{len(silent)} where it is silent. Each needs a named owner and a date to reach "
          "`Ready with conditions`. ✱ = provisional standard.", "",
          "### Gaps the submission shows", "",
          tbl(["ID", "Rule", "Finding", "Owner", "Due", "Consolidates"],
              [[f["id"] + (" ✱" if f.get("provisional_standard") else ""), f["rule_id"], f["title"],
                f.get("owner", "")[:50], f.get("due_date", "TBC"), f.get("notes", "").replace("Root cause of: ", "")]
               for f in evidenced]), "",
          "### Not stated in the submission", "",
          "The rubric rates these Major, so silence is reported as a finding rather than a gap-list "
          "item. Most close by adding a statement or a diagram, not by changing the design.", ""]
    for dom in DOMAINS:
        rows = [f for f in silent if f["domain"] == dom]
        if rows:
            L += [f"**{NAMES[dom]}** ({len(rows)})", "",
                  tbl(["ID", "Rule", "What is missing", "Provide", "Ask"],
                      [[f["id"] + (" ✱" if f.get("provisional_standard") else ""), f["rule_id"],
                        f["title"].replace("Not stated: ", ""), f["remediation"].replace("Provide: ", "")[:120],
                        f.get("owner", "")[:40]] for f in rows]), ""]
    L += ["## Minors and advisories", "",
          tbl(["ID", "Rule", "Domain", "Severity", "Finding", "Remediation"],
              [[f["id"], f["rule_id"], f["domain"], f["severity"], f["title"], f["remediation"][:160]]
               for f in ctx.outstanding("Minor") + ctx.outstanding("Advisory")]), ""]
    if meta.get("strengths"):
        L += ["## Assessed and met", "", tbl(["Domain", "Rules met", "Notable strengths"],
                                             [[NAMES[d], met.get(d, 0), meta["strengths"].get(d, "")] for d in DOMAINS]), ""]
    L += ["## Not assessable", "", f"{s['not_assessable']} rules, one row each in `findings.json` "
          "(`not_assessable`) with the reason and who resolves it.", "",
          "## Waivers and accepted risks", "",
          "Waived findings are excluded from the severity counts and the recommendation. "
          "They are open risks that someone with authority has accepted for a fixed period.", "",
          tbl(["Waiver", "Finding", "Rule", "Severity", "Expires", "Finding title"],
              [[f["waiver_id"], f["id"], f["rule_id"], f["severity"], f["waiver_expires"], f["title"]]
               for f in ctx.waived()])
          if ctx.waived() else "None on record.", ""]
    if meta.get("board_questions"):
        L += ["## Anticipated board questions", ""] + \
             [f"{i}. {q['q']} — *{q.get('state', 'no answer')}*" for i, q in enumerate(meta["board_questions"], 1)] + [""]
    integ = doc["submission_integrity"]
    L += ["## Submission integrity", "",
          "\n".join(f"- {x['anchor']}: \"{x['quote']}\" — ignored and reported" for x in integ) or "Nothing to report.", "",
          "## Coverage", "",
          tbl(["Domain", "Rules", "Raw findings", "Met", "Not assessable"],
              [[NAMES[d], ctx.rubric[d], sum(1 for x in raw if x["domain"] == d and x["rule_id"] != "NONE"),
                met.get(d, 0), len(by_dom[d])] for d in DOMAINS] +
              [["**Total**", sum(ctx.rubric.values()), sum(1 for x in raw if x["rule_id"] != "NONE"),
                sum(met.values()), len(na)]]), ""]
    if meta.get("timings"):
        L += ["Run timings: " + ", ".join(f"{k} {v}" for k, v in meta["timings"].items()), ""]
    L += ["## Method and limitations", "",
          "Reviewed from the submitted documents only. No code, infrastructure-as-code, or deployed "
          "configuration was examined, so this review assesses **documented intent**, not implemented "
          "reality. Findings against `[DEFAULT — CONFIRM]` clauses are provisional. "
          + meta.get("limitations_extra", "") +
          " This review does not constitute regulatory, legal, or compliance sign-off.", ""]
    return "\n".join(L)


def render_board(ctx: ReportContext) -> str:
    doc, meta, na = ctx.doc, ctx.meta, ctx.na
    a, s = doc["application"], doc["summary"]
    snp = sum(1 for n in na if n["reason"] == "standard not populated")
    blockers = ctx.outstanding("Blocker")
    b = meta.get("board", {})
    L = [f"# Board Pack — {a['name']}", "",
         f"**{a['name']}** · Tier {a['criticality_tier']} ({a['tier_source']}) · "
         f"{doc['submission'].get('change_type', '')} · Go-live {meta.get('target_go_live_text', doc['review'].get('target_go_live', 'NOT STATED'))}",
         f"Business owner {a['business_owner']} · Technical owner {a['technical_owner']} · Pre-review {doc['review']['date']}", "",
         "## Recommendation to the board", "", f"**{ctx.verdict}**", "", b.get("summary", meta.get("summary", "")), "",
         "## What the board is being asked to decide", "",
         tbl(["#", "Decision requested", "Recommendation"],
             [[i, d["decision"], d["recommendation"]] for i, d in enumerate(b.get("decisions", []), 1)]), "",
         "## Conditions proposed", "",
         tbl(["#", "Condition", "Owner", "By"],
             [[i, c["condition"], c.get("owner", ""), c.get("by", "")] for i, c in enumerate(b.get("conditions", []), 1)]), "",
         "## Risks proposed for acceptance", "",
         tbl(["#", "Risk", "Impact if realised", "Mitigation in place", "Accepting authority"],
             [[i, r["risk"], r["impact"], r.get("mitigation", ""), r.get("authority", "")]
              for i, r in enumerate(b.get("risks", []), 1)]), "",
         "## Blockers outstanding", "",
         tbl(["#", "Blocker", "Owner"], [[i, f"{f['title']} ({f['id']})", f.get("owner", "")[:60]]
                                         for i, f in enumerate(blockers, 1)]) if blockers else
         "None outstanding. The board should read this as an explicit statement, not an omission.", ""]
    if wb := ctx.waived("Blocker"):
        L += [f"**{len(wb)} Blocker-severity finding{plural(len(wb), '', 's')} "
              f"{plural(len(wb), 'is', 'are')} covered by a live waiver** and excluded from "
              "the recommendation above:", "",
              tbl(["Waiver", "Covers", "Rule", "Expires"],
                  [[f["waiver_id"], f["id"], f["rule_id"], f["waiver_expires"]] for f in wb]), ""]
    if ctx.uncommitted:
        L += [f"**{len(ctx.uncommitted)} Major{plural(len(ctx.uncommitted), '', 's')} "
              f"ha{plural(len(ctx.uncommitted), 's', 've')} no named owner and date**, so no "
              "conditions can be proposed for them: " + ", ".join(ctx.uncommitted), ""]
    if b.get("resilience"):
        L += ["## Resilience summary", "", tbl(["", "Claimed", "Required for tier", "Assessment"], b["resilience"]), ""]
    if b.get("regulatory"):
        L += ["## Regulatory and third-party summary", "", tbl(["", ""], b["regulatory"]), ""]
    L += ["## Open waivers", "",
          tbl(["Waiver", "Covers", "Rule", "Severity", "Expires"],
              [[f["waiver_id"], f["id"], f["rule_id"], f["severity"], f["waiver_expires"]]
               for f in ctx.waived()])
          if ctx.waived() else "None.", "", "---", "",
          f"*Pre-review produced by the `arb-preflight` skill from the submitted documents. It is a "
          f"recommendation, not an approval, and not regulatory sign-off. {s['not_assessable']} rules could "
          f"not be assessed, {snp} of them because the standard is not yet populated; see `preflight-report.md`.*", ""]
    return "\n".join(L)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main(argv: list | None = None) -> int:
    args = parse_args(argv)
    log: list = []
    try:
        inputs = load_inputs(args)
    except (OSError, ValueError) as exc:
        print(f"bad input: {exc}", file=sys.stderr)
        return 1

    rubric = Rubric.from_triage(inputs.triage, inputs.context)

    coverage = collect_reviewers(inputs.review_dir, rubric, log)
    if coverage.gaps:
        print_gaps(coverage.gaps)
        return 2

    # The prior-review delta has to be known before any severity is resolved: a cell like
    # `Blocker if any regressed` is evaluated against it, and `apply_silence_rule` resolves
    # severities in order to decide where a silent rule is filed.
    inputs.context.regressed_rules = detect_regressions(coverage.findings, inputs.prior)
    raw, na = apply_silence_rule(coverage.findings, coverage.not_assessable, rubric, log)
    # A rule the silence rule promoted out of the gap list can itself be a regression, so
    # the set is completed here and everything resolved during the silence rule recomputed.
    inputs.context.regressed_rules |= detect_regressions(raw, inputs.prior)
    rubric.invalidate()
    resolve_severities(raw, rubric, log)

    groups = group_root_causes(raw, inputs.meta.get("groups", []), log)
    findings, delta, high_water = build_findings(groups, rubric, inputs, log)
    verdict, uncommitted = decide_verdict(findings, na, rubric, inputs.meta, log)

    doc = build_document(inputs, rubric, findings, na, coverage.met, verdict, high_water, log)
    write_outputs(inputs.review_dir, doc, ReportContext(
        doc=doc, meta=inputs.meta, raw=raw, met=coverage.met, na=na,
        rubric=coverage.rubric_count, delta=delta, assessable=len(rubric.rows),
        verdict=verdict.replace(" - ", " — "), uncommitted=uncommitted))
    print_summary(doc, raw, coverage, log)
    return 0


if __name__ == "__main__":
    sys.exit(main())
