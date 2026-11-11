#!/usr/bin/env python3
"""End-to-end tests for scripts/synthesise.py. Standard library only, no fixtures on disk.

`validate.py` checks that the rubric and standards are internally consistent. These tests
check the thing validate.py cannot: that the severity, verdict, waiver and delta engine
behaves the way SKILL.md says it does. The synthesiser is the part of the skill that claims
to be *reproducible*, so it is the part that most needs a test.

Each test builds a complete synthetic review directory — real triage.json from the shipped
standards, seven reviewer files that account for every assessable rule exactly once — and
runs the script as a subprocess, the way the skill does.

    python3 tests/test_synthesise.py          # or: python3 -m unittest discover tests
"""
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = ROOT / "skill" / "arb-preflight"
SCRIPTS = SKILL / "scripts"
SYNTHESISE = SCRIPTS / "synthesise.py"

sys.path.insert(0, str(SCRIPTS))
import synthesise  # noqa: E402  (bundled script, loaded for its predicates)

DOMAINS = ["LZ", "SEC", "DAT", "RES", "INT", "OPS", "REG"]
SEVERITIES = {"Blocker", "Major", "Minor", "Advisory"}
STATUSES = {"open", "insufficient_information", "waived", "closed",
            "partially_addressed", "regressed"}
VERDICTS = {"Ready", "Ready with conditions", "Not ready - rework", "Insufficient information"}
RULE_ID = re.compile(r"^[A-Z]{2,3}-[A-Z0-9]{2,4}-\d{3}$")

_TRIAGE_CACHE: dict = {}


def triage() -> dict:
    """triage.json built from the shipped standards. Built once, treated as read-only."""
    if not _TRIAGE_CACHE:
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "triage.json"
            run = subprocess.run([sys.executable, str(SCRIPTS / "triage.py"), "--out", str(out)],
                                 capture_output=True, text=True)
            assert run.returncode == 0, f"triage.py failed: {run.stderr}"
            _TRIAGE_CACHE.update(json.loads(out.read_text(encoding="utf-8")))
    return _TRIAGE_CACHE


def rule_spec(rule_id: str) -> dict:
    for d in triage()["domains"].values():
        for a in d["assess"]:
            if a["rule_id"] == rule_id:
                return a
    raise AssertionError(f"{rule_id} is not in the assess list; this test needs a rule that is")


def first_word(spec: str) -> str:
    """What a reviewer writes for a conditional cell: the first severity word in it."""
    word = (spec or "Major").split()[0].strip("();,").title()
    return word if word in SEVERITIES else "Major"


class Review:
    """A synthetic review directory, complete enough for synthesise.py to accept."""

    def __init__(self, tmp: pathlib.Path, *, findings=(), not_assessable=(), app=None,
                 commitments=None, groups=(), prior=None, waivers=(), review_date="2026-11-09"):
        self.dir = tmp / "reviews" / "testapp" / review_date
        (self.dir / "reviewers").mkdir(parents=True)
        self.tri = triage()
        (self.dir / "triage.json").write_text(json.dumps(self.tri), encoding="utf-8")

        self.findings = dict(findings)          # rule_id -> severity the reviewer writes
        self.not_assessable = set(not_assessable)
        self._write_reviewers()

        meta = {
            "review_date": review_date,
            "application": {"name": "Test App", "tier": "1", "tier_source": "intake",
                            "business_owner": "Owner", "technical_owner": "Tech Owner",
                            "data_classes": ["payment instructions"], "jurisdictions": ["UK"],
                            "regimes_in_scope": []},
            "submission": {"files": ["test.pptx"], "version": "1.0", "dated": "2026-11-01",
                           "change_type": "migration", "slides": 10, "words": 1000,
                           "viewable_diagrams": 3, "unreadable_diagrams": 0},
            "severity_context": {"internet_facing": False, "critical_providers": False,
                                 "no_non_prod_before_cutover": False, "value_bearing": True,
                                 "radar_hold": False},
            "summary": "Synthetic review.", "groups": list(groups),
        }
        if app:
            meta["application"].update(app)
        if commitments:
            meta["commitments"] = commitments
        (self.dir / "review.json").write_text(json.dumps(meta), encoding="utf-8")

        self.prior_path = None
        if prior is not None:
            self.prior_path = tmp / "prior-findings.json"
            self.prior_path.write_text(json.dumps(prior), encoding="utf-8")

        for w in waivers:
            wdir = self.dir.parent / "waivers"
            wdir.mkdir(parents=True, exist_ok=True)
            (wdir / f"{w['id']}.md").write_text(
                f"| **Waiver ID** | {w['id']} |\n"
                f"| **Finding** | {w.get('finding', '')} |\n"
                f"| **Rule** | {w.get('rule', '')} |\n"
                f"| **Expires** | {w['expires']} |\n"
                f"| **Status** | {w.get('status', 'Approved')} |\n", encoding="utf-8")

    def _write_reviewers(self):
        for dom, d in self.tri["domains"].items():
            ids = [a["rule_id"] for a in d["assess"]]
            mine_f = [r for r in ids if r in self.findings]
            mine_n = [r for r in ids if r in self.not_assessable]
            met = [r for r in ids if r not in self.findings and r not in self.not_assessable]
            L = [f"## Domain: {dom}", "", "### Findings", ""]
            for r in mine_f:
                L += [f"#### `{r}` — synthetic finding for {r}",
                      f"- **Severity:** {self.findings[r]}",
                      "- **Status:** Not met",
                      f"- **Standard:** {rule_spec(r).get('standard', '')}",
                      '- **Evidence:** Slide 4 — "synthetic quote"',
                      "- **Impact:** Something goes wrong.",
                      "- **Remediation:** State the missing decision.",
                      "- **Owner:** Solution Architect",
                      "- **Confidence:** High", ""]
            L += ["### Assessed and met", "", "| Rule | Evidence |", "|---|---|"]
            L += [f"| `{r}` | Slide 5 |" for r in met]
            L += ["", "### Not assessable", "",
                  "| Rule | Reason | What is missing | Who to ask |", "|---|---|---|---|"]
            L += [f"| `{r}` | not stated in submission | the statement | Architect |"
                  for r in mine_n]
            L += ["", "### Coverage check", f"Rules to assess: {len(ids)}", "",
                  "### Contradictions found", "None found", "",
                  "### Cross-domain observations", "None", "",
                  "### Submission integrity", "Nothing to report", ""]
            (self.dir / "reviewers" / f"{dom}.md").write_text("\n".join(L), encoding="utf-8")

    def run(self, expect_code=0):
        cmd = [sys.executable, str(SYNTHESISE), str(self.dir)]
        if self.prior_path:
            cmd += ["--prior", str(self.prior_path)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert proc.returncode == expect_code, \
            f"exit {proc.returncode}, expected {expect_code}\n{proc.stdout}\n{proc.stderr}"
        return proc

    @property
    def doc(self) -> dict:
        return json.loads((self.dir / "findings.json").read_text(encoding="utf-8"))

    @property
    def report(self) -> str:
        return (self.dir / "preflight-report.md").read_text(encoding="utf-8")

    @property
    def board(self) -> str:
        return (self.dir / "board-pack.md").read_text(encoding="utf-8")

    def finding(self, rule_id: str) -> dict:
        hits = [f for f in self.doc["findings"] if f["rule_id"] == rule_id]
        assert hits, f"{rule_id} is not in findings.json"
        return hits[0]


class TempCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = pathlib.Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def majors(self, n=1):
        """n rules whose rubric severity is a plain `Major`, for verdict tests."""
        out = []
        for d in triage()["domains"].values():
            for a in d["assess"]:
                if a.get("severity_default", "").strip() == "Major" and a.get("ceiling") == "rubric default":
                    out.append(a["rule_id"])
                if len(out) == n:
                    return out
        raise AssertionError("not enough plain-Major rules in the rubric")


class TestConditionalSeverity(TempCase):
    """Rubric cells conditional on the application, resolved in synthesise.Rubric."""

    def test_regression_condition_is_resolved_after_the_prior_delta_is_known(self):
        """`Blocker if any regressed` must see the regression, even for a silent rule.

        Guards an ordering bug: the silence rule resolves severities in order to decide
        where a silent rule is filed, so if the prior-review delta is computed after it,
        the memoised answer for every conditional cell is the pre-delta one.
        """
        conditional = "OPS-GOV-002"            # severity cell: "Blocker if any regressed"
        self.assertIn("regress", rule_spec(conditional)["severity_default"].lower())
        regressing = self.majors(1)[0]
        prior = {"review": {"id_high_water": 7},
                 "findings": [{"id": "F-007", "rule_id": regressing, "domain": "LZ",
                               "title": "previously closed", "severity": "Major",
                               "status": "closed", "first_raised": "2026-01-01"}]}
        r = Review(self.tmp,
                   findings={regressing: "Major"},
                   not_assessable=[conditional],
                   prior=prior)
        r.run()
        self.assertEqual(r.finding(regressing)["status"], "regressed")
        self.assertEqual(r.finding(conditional)["severity"], "Blocker",
                         "a rule whose cell reads 'Blocker if any regressed' must be a "
                         "Blocker once something has regressed")

    def test_unresolvable_condition_warns_and_does_not_guess(self):
        conditional = "OPS-GOV-002"
        r = Review(self.tmp, not_assessable=[conditional])
        out = r.run().stdout
        self.assertEqual(r.finding(conditional)["severity"], "Major",
                         "with nothing regressed the cell sits one level below Blocker")
        self.assertNotIn("Blocker if any regressed", out.replace("WARNING", ""))

    def test_value_bearing_is_false_when_data_classes_are_stated(self):
        """A stated, non-value-bearing data set is a real False, not 'unknowable'.

        Returning None here left the condition permanently unresolved and warned on
        every ordinary application.
        """
        self.assertIs(synthesise.Context(data_classes=["public marketing copy"])
                      .predicate("value_bearing"), False)
        self.assertIs(synthesise.Context(data_classes=["payment instructions"])
                      .predicate("value_bearing"), True)
        self.assertIsNone(synthesise.Context(data_classes=[]).predicate("value_bearing"),
                          "an unstated data-class list is the only unknowable case")

    def test_explicit_flag_beats_inference(self):
        ctx = synthesise.Context(data_classes=["payment"], flags={"value_bearing": False})
        self.assertIs(ctx.predicate("value_bearing"), False)


class TestVerdict(TempCase):
    def test_no_findings_is_ready(self):
        r = Review(self.tmp)
        r.run()
        self.assertEqual(r.doc["review"]["verdict"], "Ready")

    def test_uncommitted_majors_hold_the_verdict(self):
        """`Ready with conditions` needs an owner and a date on every Major.

        Reviewers supply an owner role but never a date, so without a commitments
        channel this verdict was granted over a list nobody had committed to.
        """
        majors = self.majors(2)
        r = Review(self.tmp, findings={m: "Major" for m in majors})
        out = r.run().stdout
        self.assertEqual(r.doc["review"]["verdict"], "Insufficient information")
        self.assertIn("named owner and a date", out)
        self.assertIn("no named owner and date", r.report)
        for m in majors:
            self.assertNotIn("due_date", r.finding(m))

    def test_commitments_unlock_ready_with_conditions(self):
        majors = self.majors(2)
        r = Review(self.tmp, findings={m: "Major" for m in majors},
                   commitments={m: {"owner": "Platform Lead", "due": "2027-02-01"}
                                for m in majors})
        r.run()
        self.assertEqual(r.doc["review"]["verdict"], "Ready with conditions")
        for m in majors:
            self.assertEqual(r.finding(m)["due_date"], "2027-02-01")
            self.assertEqual(r.finding(m)["owner"], "Platform Lead")

    def test_commitment_by_finding_id_also_works(self):
        major = self.majors(1)[0]
        r = Review(self.tmp, findings={major: "Major"},
                   commitments={"F-001": {"owner": "Platform Lead", "due": "2027-02-01"}})
        r.run()
        self.assertEqual(r.doc["review"]["verdict"], "Ready with conditions")

    def test_a_blocker_forces_not_ready(self):
        blocker = next(a["rule_id"] for d in triage()["domains"].values() for a in d["assess"]
                       if first_word(a.get("severity_default", "")) == "Blocker"
                       and a.get("ceiling") == "rubric default")
        r = Review(self.tmp, findings={blocker: "Blocker"})
        r.run()
        self.assertEqual(r.doc["review"]["verdict"], "Not ready - rework")

    def test_verdict_is_always_a_schema_value(self):
        r = Review(self.tmp, findings={m: "Major" for m in self.majors(1)})
        r.run()
        self.assertIn(r.doc["review"]["verdict"], VERDICTS)


class TestWaivers(TempCase):
    def _blocker(self):
        return next(a["rule_id"] for d in triage()["domains"].values() for a in d["assess"]
                    if first_word(a.get("severity_default", "")) == "Blocker"
                    and a.get("ceiling") == "rubric default")

    def test_a_waived_blocker_leaves_the_verdict_and_the_outstanding_table_together(self):
        """A waiver clears a Blocker from the verdict, so it must also leave the
        'Blockers outstanding' table — a pack that recommends Ready above a table of
        blockers is worse than either answer alone."""
        blocker = self._blocker()
        r = Review(self.tmp, findings={blocker: "Blocker"},
                   waivers=[{"id": "W-001", "rule": blocker, "expires": "2027-12-31"}])
        r.run()
        self.assertEqual(r.finding(blocker)["status"], "waived")
        self.assertEqual(r.doc["summary"]["blocker"], 0)
        self.assertNotEqual(r.doc["review"]["verdict"], "Not ready - rework")
        board = r.board
        section = board.split("## Blockers outstanding")[1]
        outstanding, waiver_callout = section.split("covered by a live waiver")
        self.assertIn("None outstanding", outstanding)
        self.assertNotIn(blocker, outstanding,
                         "a waived Blocker must not be listed as outstanding")
        self.assertIn("W-001", waiver_callout)
        self.assertIn(blocker, waiver_callout, "but it must still be named, with its waiver")
        # Same story in the report the submitting team reads.
        self.assertIn("None outstanding", r.report.split("## Blockers")[1])
        self.assertIn("The risk is accepted, not resolved", r.report)

    def test_an_expired_waiver_becomes_a_major_finding(self):
        r = Review(self.tmp, waivers=[{"id": "W-002", "rule": "LZ-DOC-001",
                                       "expires": "2020-01-01"}])
        r.run()
        expired = r.finding("OPS-GOV-004")
        self.assertEqual(expired["severity"], "Major")
        self.assertEqual(expired["status"], "open")
        self.assertIn("W-002", expired["title"])

    def test_a_future_dated_unapproved_waiver_does_not_waive(self):
        blocker = self._blocker()
        r = Review(self.tmp, findings={blocker: "Blocker"},
                   waivers=[{"id": "W-003", "rule": blocker, "expires": "2027-12-31",
                             "status": "Requested"}])
        r.run()
        self.assertEqual(r.finding(blocker)["status"], "open")
        self.assertEqual(r.doc["review"]["verdict"], "Not ready - rework")


class TestDeltaAndIds(TempCase):
    def test_a_closed_finding_keeps_its_id_and_is_carried_forward(self):
        major = self.majors(1)[0]
        prior = {"review": {"id_high_water": 12},
                 "findings": [{"id": "F-012", "rule_id": "LZ-DOC-001", "domain": "LZ",
                               "title": "fixed since", "severity": "Major", "status": "open",
                               "first_raised": "2026-01-01"}]}
        r = Review(self.tmp, findings={major: "Major"}, prior=prior)
        r.run()
        carried = r.finding("LZ-DOC-001")
        self.assertEqual(carried["status"], "closed")
        self.assertEqual(carried["id"], "F-012")
        self.assertFalse(carried["board_condition"])
        ids = {f["id"] for f in r.doc["findings"]}
        self.assertNotIn("F-012", ids - {"F-012"})
        self.assertGreaterEqual(r.doc["review"]["id_high_water"], 13)
        self.assertEqual(r.finding(major)["id"], "F-013",
                         "a new finding must not reuse an id that once meant something else")


class TestCoverage(TempCase):
    def test_a_missing_reviewer_fails_the_run_and_writes_nothing(self):
        r = Review(self.tmp)
        (r.dir / "reviewers" / "REG.md").unlink()
        out = r.run(expect_code=2).stdout
        self.assertIn("COVERAGE GAPS", out)
        self.assertIn("REG", out)
        for name in ("findings.json", "preflight-report.md", "board-pack.md"):
            self.assertFalse((r.dir / name).exists(), f"{name} must not be written on a gap")

    def test_a_dropped_rule_fails_the_run(self):
        r = Review(self.tmp)
        path = r.dir / "reviewers" / "DAT.md"
        lines = [ln for ln in path.read_text(encoding="utf-8").splitlines()
                 if not re.match(r"^\| `DAT-", ln)]
        path.write_text("\n".join(lines), encoding="utf-8")
        out = r.run(expect_code=2).stdout
        self.assertIn("missing", out)

    def test_a_rule_whose_standard_is_unpopulated_is_never_a_finding(self):
        # Reviewers are never given blocked rules, so this asserts that triage stays
        # authoritative: the rule appears once, as a gap owned by the standard's owner.
        blocked = next(b["rule_id"] for d in triage()["domains"].values() for b in d["blocked"])
        r = Review(self.tmp)
        r.run()
        rows = [n for n in r.doc["not_assessable"] if n["rule_id"] == blocked]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["reason"], "standard not populated")
        self.assertNotIn(blocked, {f["rule_id"] for f in r.doc["findings"]})


class TestSilenceRule(TempCase):
    def test_a_silent_blocker_or_major_rule_becomes_a_finding(self):
        major = self.majors(1)[0]
        r = Review(self.tmp, not_assessable=[major])
        r.run()
        f = r.finding(major)
        self.assertEqual(f["status"], "insufficient_information")
        self.assertEqual(f["evidence"][0]["anchor"], "NOT STATED")
        self.assertNotIn(major, {n["rule_id"] for n in r.doc["not_assessable"]})

    def test_a_silent_minor_rule_stays_in_the_gap_list(self):
        minor = next((a["rule_id"] for d in triage()["domains"].values() for a in d["assess"]
                      if first_word(a.get("severity_default", "")) in ("Minor", "Advisory")), None)
        if minor is None:
            self.skipTest("no Minor/Advisory rule in the rubric")
        r = Review(self.tmp, not_assessable=[minor])
        r.run()
        self.assertIn(minor, {n["rule_id"] for n in r.doc["not_assessable"]})
        self.assertNotIn(minor, {f["rule_id"] for f in r.doc["findings"]})


class TestArtefacts(TempCase):
    def test_every_finding_matches_the_published_schema_enums(self):
        majors = self.majors(3)
        r = Review(self.tmp, findings={majors[0]: "Major"}, not_assessable=majors[1:],
                   commitments={majors[0]: {"owner": "Lead", "due": "2027-01-01"}})
        r.run()
        doc = r.doc
        self.assertEqual(doc["schema_version"], "1.0")
        self.assertIn(doc["review"]["verdict"], VERDICTS)
        self.assertEqual(doc["review"]["domains_reviewed"], DOMAINS)
        for f in doc["findings"]:
            self.assertIn(f["severity"], SEVERITIES, f["id"])
            self.assertIn(f["status"], STATUSES, f["id"])
            self.assertIn(f["domain"], DOMAINS, f["id"])
            self.assertLessEqual(len(f["title"]), 120, f["id"])
            self.assertTrue(f["rule_id"] == "NONE" or RULE_ID.match(f["rule_id"]), f["rule_id"])
            if adj := f.get("severity_adjusted"):
                self.assertIn(adj["from"], SEVERITIES)
                self.assertIn(adj["direction"], ("up", "down"))
                self.assertTrue(adj["reason"], "an adjustment must carry its reason")

    def test_both_documents_state_that_this_is_a_recommendation(self):
        r = Review(self.tmp)
        r.run()
        self.assertIn("recommendation, not an approval", r.report)
        self.assertIn("recommendation, not an approval", r.board)
        self.assertNotIn("Approved", r.board)

    def test_coverage_totals_account_for_every_rule(self):
        r = Review(self.tmp)
        out = r.run().stdout
        total = sum(len(d["assess"]) + len(d["blocked"]) for d in triage()["domains"].values())
        self.assertIn(f"over {total} rules", out)

    def test_a_warning_is_not_printed_twice(self):
        """Severities are resolved twice by design (before and after the prior delta);
        the operator must still see each warning once."""
        r = Review(self.tmp, not_assessable=["OPS-GOV-002"])
        warnings = [ln for ln in r.run().stdout.splitlines() if ln.startswith("WARNING:")]
        self.assertEqual(len(warnings), len(set(warnings)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
