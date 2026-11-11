#!/usr/bin/env python3
"""Integrity checks for the arb-preflight skill. Standard library only.

Checks:
  1. SKILL.md has frontmatter with name and description.
  2. Every rubric rule ID matches the findings.schema.json pattern.
  3. No rubric rule ID is defined twice.
  4. Every standards clause a rubric cites exists in standards/.
  5. Templates referenced from SKILL.md exist.
  6. findings.schema.json is valid JSON.
  7. Bundled scripts compile, and triage.py runs against the current standards.
  8. The rule counts README.md advertises match the rubric and triage.

Exit code 0 when clean, 1 otherwise. Run from anywhere:
    python3 tools/validate.py
"""
import json
import pathlib
import re
import sys

SKILL = pathlib.Path(__file__).resolve().parent.parent / "skill" / "arb-preflight"
CLAUSE = re.compile(r"`((?:LZB|SB|CT|OBL|PAT)-[A-Z0-9]{2,4}(?:-\d+)?)`")
RULE_ROW = re.compile(r"^\| `([A-Z]{2,3}-[A-Z0-9]{2,4}-\d{3})`", re.M)

errors = []

skill_md = (SKILL / "SKILL.md").read_text(encoding="utf-8")
front = re.match(r"^---\n(.*?)\n---\n", skill_md, re.S)
if not front or not re.search(r"^name:\s*\S", front.group(1), re.M) or "description:" not in front.group(1):
    errors.append("SKILL.md frontmatter must contain name and description")

try:
    schema = json.loads((SKILL / "templates" / "findings.schema.json").read_text(encoding="utf-8"))
    pattern = re.compile(schema["properties"]["findings"]["items"]["properties"]["rule_id"]["pattern"])
except (ValueError, KeyError) as exc:
    errors.append(f"findings.schema.json unreadable: {exc}")
    pattern = re.compile(r".*")

defined = set()
for f in (SKILL / "standards").glob("*.md"):
    defined |= set(CLAUSE.findall(f.read_text(encoding="utf-8")))

sys.path.insert(0, str(SKILL / "scripts"))
import synthesise  # noqa: E402  (bundled script, loaded for its severity grammar)

FULL_ROW = re.compile(r"^\| `([A-Z]{2,3}-[A-Z0-9]{2,4}-\d{3})` \|(?:[^|]*\|){2}([^|]*)\|")
# A context in which every conditional predicate is answerable, so the only thing that can
# fail below is a condition no predicate recognises.
PROBE = synthesise.Context(tier="1", change_type="migration", regimes_in_scope=["example"],
                           data_classes=["payment"],
                           flags={"internet_facing": True, "critical_providers": True,
                                  "no_non_prod_before_cutover": True, "value_bearing": True,
                                  "radar_hold": True},
                           regressed_rules={"X"})

rules, per_file = [], {}
for f in sorted((SKILL / "rubric").glob("*.md")):
    text = f.read_text(encoding="utf-8")
    ids = RULE_ROW.findall(text)
    per_file[f.name] = len(ids)
    rules += ids
    for c in sorted(set(CLAUSE.findall(text)) - defined):
        errors.append(f"{f.name}: cites clause {c}, which is not defined in standards/")
    # Severity cells may be conditional ("Blocker (T1)", "Major; Blocker if ..."), and
    # synthesise.py resolves them. A cell outside that grammar would silently fall back
    # to Major on every review, so it fails here instead. See AUTHORING.md 4.3.1.
    for line in text.splitlines():
        m = FULL_ROW.match(line)
        if not m:
            continue
        rid, spec = m.group(1), m.group(2).strip()
        base, conds, leftover = synthesise.parse_severity_spec(spec)
        if not base and not conds:
            errors.append(f"{f.name}: {rid} severity '{spec}' is not a severity; "
                          f"it will default to Major on every review")
        for _, cond in conds:
            if synthesise.condition_holds(cond, PROBE, [], rid) is None:
                errors.append(f"{f.name}: {rid} severity condition '{cond}' matches no "
                              f"predicate in synthesise.py; see AUTHORING.md 4.3.1")

errors += [f"rule ID {r} does not match schema pattern" for r in rules if not pattern.fullmatch(r)]
errors += [f"rule ID {r} defined more than once" for r in sorted({r for r in rules if rules.count(r) > 1})]

for ref in sorted(set(re.findall(r"`(templates/[\w.-]+|scripts/[\w.-]+|intake\.md)`", skill_md))):
    if not (SKILL / ref).exists():
        errors.append(f"SKILL.md references missing file {ref}")

import py_compile, subprocess, tempfile
for script in sorted((SKILL / "scripts").glob("*.py")):
    try:
        py_compile.compile(str(script), doraise=True)
    except py_compile.PyCompileError as exc:
        errors.append(f"{script.name} does not compile: {exc.msg}")
tri = None
with tempfile.TemporaryDirectory() as tmp:
    run = subprocess.run([sys.executable, str(SKILL / "scripts" / "triage.py"), "--out", f"{tmp}/t.json"],
                         capture_output=True, text=True)
    if run.returncode:
        errors.append("triage.py failed: " + run.stderr.strip()[-200:])
    else:
        tri = json.loads(pathlib.Path(f"{tmp}/t.json").read_text())
        n = sum(len(d["assess"]) + len(d["blocked"]) for d in tri["domains"].values())
        if n != len(rules):
            errors.append(f"triage.py accounted for {n} rules, rubric has {len(rules)}")
        total = next((ln for ln in run.stdout.splitlines() if ln.startswith("total assess")), "")
        print("triage: " + total.split(" -> ")[0])
        # Not errors: an obligation may legitimately cite a regime nobody has defined yet,
        # because the shipped register names sector rules the adopting organisation fills
        # in. Printed so that the gap is visible rather than silent.
        for note in tri.get("register_notes", []):
            print("  note:", note)

# 8. The numbers README.md advertises, checked against the rubric and against triage.
# A headline that has drifted is the kind of error nobody notices until a reader counts,
# and the counts here are the skill's main claim about itself.
if tri is not None:
    readme = (SKILL.parents[1] / "README.md").read_text(encoding="utf-8")
    assessable = {dom: len(d["assess"]) for dom, d in tri["domains"].items()}
    total_rules, total_assessable = len(rules), sum(assessable.values())

    head = re.search(r"\*\*(\d+) rules\*\*\s*\((\d+) assessable", readme)
    if not head:
        errors.append("README.md: cannot find the '**N rules** (M assessable' headline; "
                      "if you reworded it, update this check too")
    else:
        if int(head.group(1)) != total_rules:
            errors.append(f"README.md headline says {head.group(1)} rules, rubric has {total_rules}")
        if int(head.group(2)) != total_assessable:
            errors.append(f"README.md headline says {head.group(2)} assessable, triage reports "
                          f"{total_assessable}")

    table = {dom: (int(n), int(m)) for dom, n, m in re.findall(
        r"^\|[^|]+\|\s*`([A-Z]{2,3})`\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|", readme, re.M)}
    if set(table) != set(assessable):
        errors.append(f"README.md Domains table lists {sorted(table)}, triage has "
                      f"{sorted(assessable)}")
    for dom, (claimed_rules, claimed_assessable) in table.items():
        actual_rules = len(tri["domains"][dom]["assess"]) + len(tri["domains"][dom]["blocked"])
        if claimed_rules != actual_rules:
            errors.append(f"README.md Domains table: {dom} says {claimed_rules} rules, "
                          f"rubric has {actual_rules}")
        if claimed_assessable != assessable[dom]:
            errors.append(f"README.md Domains table: {dom} says {claimed_assessable} "
                          f"assessable, triage reports {assessable[dom]}")

print(f"rules: {len(rules)}  " + "  ".join(f"{k[:-3]}={v}" for k, v in per_file.items()))
print(f"clauses defined: {len(defined)}")
if errors:
    print("\nFAILED:")
    for e in errors:
        print("  -", e)
    sys.exit(1)
print("OK")
