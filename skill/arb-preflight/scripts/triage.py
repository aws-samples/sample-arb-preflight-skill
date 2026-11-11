#!/usr/bin/env python3
"""Pre-triage rubric rules against the current state of standards/. Standard library only.

Before any reviewer starts, this decides mechanically which rules cannot be assessed
because the standard they depend on is not populated, so reviewers spend their time only
on rules that can actually be judged. It applies the same rule the reviewers follow:

  * a clause marked [TBD] (row-level, or file-level when the row has no marker) is not
    populated;
  * an OBL-* obligation is not populated unless at least one regime it lists has
    Applies = yes in obligations-register.md;
  * a rubric rule is BLOCKED only when every standard it cites is not populated. Rules
    citing intake, "—", or anything outside standards/ are always assessed.

For rules left to assess, it also reports the severity ceiling: rules whose clauses are
all [DEFAULT — CONFIRM] are capped at Major ("provisional standard").

Usage:
    python3 triage.py --out reviews/<app>/<date>/triage.json [--skill <skill-folder>]

Prints a per-domain summary. The JSON is what reviewers and synthesise.py read.
"""
import argparse
import json
import pathlib
import re
import sys

DOMAINS = {"platform": "LZ", "security": "SEC", "data": "DAT", "resilience": "RES",
           "integration": "INT", "operations": "OPS", "compliance": "REG"}
CLAUSE = re.compile(r"(?:LZB|SB|CT|OBL|PAT)-[A-Z0-9*]{1,4}(?:-(?:\d+|\*))?")
# `[add sector regulator]` and friends are prompts to the register's owner, not regimes.
PLACEHOLDER = re.compile(r"^\s*`?\[")


# ---------------------------------------------------------------------------
# Markdown tables, read by column heading rather than by position
# ---------------------------------------------------------------------------


def table_rows(text: str, *required: str) -> list:
    """Rows of the first table whose heading row contains all of `required`.

    Each row is `{heading: cell}`. Reading by heading rather than by column index means
    that renaming or reordering a column in a standards file — which their owners do,
    because these are documents people edit — fails loudly in `main` instead of silently
    changing which rules get triaged.
    """
    cols, rows = None, []
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            if cols is not None:
                break                                   # the table ended
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cols is None:
            head = [c.strip("* ").lower() for c in cells]
            if all(any(r in h for h in head) for r in required):
                cols = head
            continue
        if set("".join(cells)) <= set("-: "):
            continue                                    # the |---|---| separator
        rows.append(dict(zip(cols, cells)))
    return rows


def cell(row: dict, key: str) -> str:
    return next((v for h, v in row.items() if key in h), "")


# ---------------------------------------------------------------------------
# Regime applicability
# ---------------------------------------------------------------------------


def normalise(name: str) -> str:
    """A regime name reduced to a comparable form: case, backticks, dashes, spacing."""
    t = name.strip().strip("`").lower().replace("—", "-").replace("–", "-")
    t = re.sub(r"\s*/\s*", "/", t)          # "CCPA / CPRA" and "CCPA/CPRA" are one regime
    return re.sub(r"\s+", " ", t).strip(" .")


def aliases(name: str) -> set:
    """Every form of a register regime name an obligation row may legitimately cite.

    Comparison is exact against this set, never by substring: substring matching once let
    an applicable `EU AI Act` satisfy an obligation citing `EU Data Act`, because both
    contain "eu". A spaced slash or a spaced dash separates alternative names for one
    regime (`GDPR / UK GDPR`, `SOX — ITGC scope`); an unspaced slash does not
    (`ISO/IEC 27001`).
    """
    raw = name.strip().strip("`")
    out = set()
    for part in [raw, *re.split(r"\s+/\s+|\s+[—–-]\s+", raw)]:
        n = normalise(part)
        if not n:
            continue
        out.add(n)
        # A trailing dotted version is not part of the name: `PCI DSS 4.0` is cited as
        # `PCI DSS`. Only dotted, so `ISO 22301` and `SOC 2` keep their numbers.
        out.add(re.sub(r"\s+v?\d+\.\d[\d.]*$", "", n).strip())
    return {o for o in out if o}


def applicability(regimes: list, applies: dict) -> tuple:
    """`(does any cited regime apply, tokens that match no regime in the register)`."""
    index = {}
    for name in applies:
        for a in aliases(name):
            index.setdefault(a, name)
    hit, unmatched = False, []
    for token in regimes:
        t = normalise(token)
        if not t:
            continue
        name = index.get(t)
        if name is None:
            unmatched.append(token.strip())
        elif applies[name] == "yes":
            hit = True
    return hit, unmatched


def state_of(marker):
    m = (marker or "").upper()
    if "SUPERSEDED" in m:
        return "superseded"
    if "CONFIRMED" in m:
        return "confirmed"
    if "DEFAULT" in m:
        return "default"
    if "TBD" in m:
        return "tbd"
    return None


def load_standards(std):
    """Return {clause_id: state} and {obl_id: [regimes]} and {regime: applies}."""
    states = {}
    for f in std.glob("*.md"):
        text = f.read_text(encoding="utf-8")
        fm = re.search(r"Status:\s*`\[([^\]]+)\]`", text)
        file_state = state_of(fm.group(1)) if fm else "tbd"
        for line in text.splitlines():
            if line.startswith("#"):
                for cid in re.findall(r"`((?:LZB|SB|CT|OBL|PAT)-[A-Z0-9]{2,4}(?:-\d+)?)`", line):
                    states.setdefault(cid, file_state)
                continue
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            m = re.match(r"`((?:LZB|SB|CT|OBL|PAT)-[A-Z0-9]{2,4}(?:-\d+)?)`", cells[0]) if cells else None
            if not m:
                continue
            row_state = next((state_of(c) for c in reversed(cells[1:]) if state_of(c)), None)
            states[m.group(1)] = row_state or file_state

    reg = (std / "obligations-register.md").read_text(encoding="utf-8")
    applies, obl_regimes, notes = {}, {}, []
    for row in table_rows(reg, "regime", "applies"):
        name = cell(row, "regime")
        if name and not PLACEHOLDER.match(name):
            applies[name] = cell(row, "applies").strip("` ").lower()   # yes / no / tbc
    for row in table_rows(reg, "id", "regimes"):
        rid = cell(row, "id").strip("` ")
        if rid.startswith("OBL-"):
            obl_regimes[rid] = cell(row, "regimes").split(",")
    if not applies:
        raise SystemExit("obligations-register.md: found no Applicability table with "
                         "`Regime` and `Applies` columns. Triage cannot decide which "
                         "obligations are in scope; fix the table headings.")
    if not obl_regimes:
        raise SystemExit("obligations-register.md: found no obligations table with `ID` and "
                         "`Regimes` columns, so no OBL-* clause can be resolved.")

    unresolved: dict = {}
    for obl, regimes in obl_regimes.items():
        hit, unmatched = applicability(regimes, applies)
        for u in unmatched:
            unresolved.setdefault(u, []).append(obl)
        if not hit:
            states[obl] = "tbd"                     # no applicable regime
        elif states.get(obl) == "tbd":
            states[obl] = "default"                 # applies; clause text is a default
    # An obligation citing a regime the register does not list can never become
    # assessable, however the register is populated. Usually it means a regime was renamed
    # or deleted and the obligation rows were not followed through.
    for token, obls in sorted(unresolved.items()):
        notes.append(f"obligations-register.md: `{token}` is cited by "
                     f"{', '.join(sorted(obls))} but is not a regime in the Applicability "
                     f"table, so those obligations can never apply")
    return states, notes


def expand(ref, states):
    if ref.endswith("*"):
        prefix = ref.rstrip("*")
        return [c for c in states if c.startswith(prefix)] or [ref]
    return [ref]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--skill", default=str(pathlib.Path(__file__).resolve().parent.parent))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    skill = pathlib.Path(args.skill)
    states, notes = load_standards(skill / "standards")
    radar_tbd = state_of(re.search(r"Status:\s*`\[([^\]]+)\]`",
                                   (skill / "standards/tech-radar.md").read_text()).group(1)) == "tbd"
    pattern_tbd = state_of(re.search(r"Status:\s*`\[([^\]]+)\]`",
                                     (skill / "standards/pattern-catalog.md").read_text()).group(1)) == "tbd"
    register_tbd = all(s == "tbd" for c, s in states.items() if c.startswith("OBL-"))

    result = {"standards_state": {}, "register_notes": notes, "domains": {}}
    for f in sorted((skill / "standards").glob("*.md")):
        if f.name == "README.md":
            continue
        m = re.search(r"Status:\s*`\[([^\]]+)\]`", f.read_text(encoding="utf-8"))
        s = state_of(m.group(1)) if m else "tbd"
        result["standards_state"][f.stem] = {"tbd": "placeholder", "default": "default"}.get(s, "confirmed")
    if register_tbd:
        result["standards_state"]["obligations-register"] = "placeholder"

    for fname, dom in DOMAINS.items():
        assess, blocked = [], []
        for line in (skill / "rubric" / f"{fname}.md").read_text(encoding="utf-8").splitlines():
            m = re.match(r"\| `([A-Z]{2,3}-[A-Z0-9]{2,4}-\d{3})` \|(.+?)\|(.+?)\|(.+?)\|(.*?)\|", line)
            if not m:
                continue
            rid, check, std_col, sev = m.group(1), m.group(2).strip(), m.group(3).strip(), m.group(4).strip()
            refs = [c for r in CLAUSE.findall(std_col) for c in expand(r, states)]
            words = std_col.strip("` ").lower()
            if not refs and words in ("tech-radar", "pattern-catalog", "register"):
                tbd = {"tech-radar": radar_tbd, "pattern-catalog": pattern_tbd, "register": register_tbd}[words]
                refs_state = ["tbd" if tbd else "default"]
            else:
                refs_state = [states.get(c, "tbd") for c in refs]
            entry = {"rule_id": rid, "standard": std_col.replace("`", ""), "severity_default": sev,
                     "evidence_needed": m.group(5).strip()}
            if refs_state and all(s == "tbd" for s in refs_state):
                entry["reason"] = "standard not populated"
                entry["detail"] = "All cited standards are [TBD] or have no applicable regime: " + std_col.replace("`", "")
                blocked.append(entry)
            else:
                entry["ceiling"] = "Major (provisional standard)" if refs_state and all(
                    s in ("default", "tbd") for s in refs_state) else "rubric default"
                entry["check"] = check
                assess.append(entry)
        result["domains"][dom] = {"rubric_file": f"rubric/{fname}.md", "assess": assess, "blocked": blocked}

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    total_a = sum(len(d["assess"]) for d in result["domains"].values())
    total_b = sum(len(d["blocked"]) for d in result["domains"].values())
    for dom, d in result["domains"].items():
        print(f"{dom:4} assess {len(d['assess']):3}  blocked {len(d['blocked']):3}")
    print(f"total assess {total_a}  blocked {total_b}  -> {out}")
    for n in notes:
        print("NOTE:", n)


if __name__ == "__main__":
    sys.exit(main())
