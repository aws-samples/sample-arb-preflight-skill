#!/usr/bin/env python3
"""Tests for scripts/triage.py. Standard library only.

Triage decides which rules a reviewer is allowed to assess, so a mistake here does not
produce a wrong finding — it produces a rule nobody ever looks at, or a regulatory
obligation marked applicable because of a coincidence in a regime's name. Neither shows up
in the output. These tests pin the two mechanisms that decide it: regime matching, and
reading the register's tables by heading rather than by column position.

    python3 tests/test_triage.py          # or: python3 -m unittest discover tests
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = ROOT / "skill" / "arb-preflight"
SCRIPTS = SKILL / "scripts"

sys.path.insert(0, str(SCRIPTS))
import triage  # noqa: E402  (bundled script, loaded for its regime matching)

# The shipped Applicability table, as triage reads it: every regime still unconfirmed.
SHIPPED = {"GDPR / UK GDPR": "tbc", "CCPA / CPRA": "tbc", "HIPAA": "tbc",
           "PCI DSS 4.0": "tbc", "SOX — ITGC scope": "tbc", "NIS2": "tbc",
           "EU AI Act": "tbc", "EU Data Act — cloud switching": "tbc",
           "ISO/IEC 27001": "tbc", "SOC 2": "tbc", "ISO 22301": "tbc",
           "NIST AI RMF / ISO/IEC 42001": "tbc"}


def applies_only(regime: str) -> dict:
    return {k: ("yes" if k == regime else "tbc") for k in SHIPPED}


class TestRegimeNames(unittest.TestCase):
    def test_an_alternative_name_for_one_regime_matches(self):
        """`GDPR / UK GDPR` in the register is cited as plain `GDPR` by obligation rows."""
        self.assertIn("gdpr", triage.aliases("GDPR / UK GDPR"))
        self.assertIn("uk gdpr", triage.aliases("GDPR / UK GDPR"))
        self.assertIn("sox", triage.aliases("SOX — ITGC scope"))
        self.assertIn("eu data act", triage.aliases("EU Data Act — cloud switching"))
        self.assertIn("nist ai rmf", triage.aliases("NIST AI RMF / ISO/IEC 42001"))

    def test_spacing_around_a_slash_is_not_significant(self):
        self.assertEqual(triage.normalise("CCPA / CPRA"), triage.normalise("CCPA/CPRA"))

    def test_an_unspaced_slash_is_part_of_the_name(self):
        """`ISO/IEC 27001` is one regime, not `ISO` and `IEC 27001`."""
        self.assertNotIn("iso", triage.aliases("ISO/IEC 27001"))
        self.assertIn("iso/iec 27001", triage.aliases("ISO/IEC 27001"))

    def test_a_trailing_dotted_version_is_optional_but_a_number_is_not(self):
        self.assertIn("pci dss", triage.aliases("PCI DSS 4.0"))
        self.assertNotIn("iso", triage.aliases("ISO 22301"))
        self.assertNotIn("soc", triage.aliases("SOC 2"))


class TestApplicability(unittest.TestCase):
    def test_a_cited_regime_that_applies_makes_the_obligation_applicable(self):
        hit, unmatched = triage.applicability(["PCI DSS"], applies_only("PCI DSS 4.0"))
        self.assertTrue(hit)
        self.assertEqual(unmatched, [])

    def test_a_different_regime_does_not(self):
        hit, _ = triage.applicability(["PCI DSS"], applies_only("HIPAA"))
        self.assertFalse(hit)

    def test_regimes_sharing_a_first_word_are_not_confused(self):
        """The bug this replaced: matching by substring let any applicable regime whose
        first word was `EU` satisfy an obligation citing a different EU regulation."""
        applies = applies_only("EU AI Act")
        hit, _ = triage.applicability(["EU Data Act", "sector rules"], applies)
        self.assertFalse(hit, "EU AI Act must not make an EU Data Act obligation applicable")
        hit, _ = triage.applicability(["EU AI Act"], applies)
        self.assertTrue(hit)

    def test_a_regime_the_register_does_not_list_is_reported_not_ignored(self):
        hit, unmatched = triage.applicability(["sector rules"], applies_only("NIS2"))
        self.assertFalse(hit)
        self.assertEqual(unmatched, ["sector rules"],
                         "an obligation citing a regime nobody has defined can never "
                         "apply, so it has to be said out loud")

    def test_a_placeholder_regime_never_applies(self):
        applies = dict(SHIPPED, **{"`[add sector regulator]`": "yes"})
        hit, _ = triage.applicability(["sector rules"], applies)
        self.assertFalse(hit)


class TestTableReading(unittest.TestCase):
    APPLICABILITY = (
        "| Regime | Scope | Applies | Entity scope |\n"
        "|---|---|---|---|\n"
        "| NIS2 | EU entities | `yes` | Group |\n"
    )

    def test_rows_are_read_by_heading(self):
        rows = triage.table_rows(self.APPLICABILITY, "regime", "applies")
        self.assertEqual(len(rows), 1)
        self.assertEqual(triage.cell(rows[0], "regime"), "NIS2")
        self.assertEqual(triage.cell(rows[0], "applies"), "`yes`")

    def test_a_reordered_column_still_reads_correctly(self):
        reordered = ("| Scope | Applies | Regime |\n"
                     "|---|---|---|\n"
                     "| EU entities | `yes` | NIS2 |\n")
        rows = triage.table_rows(reordered, "regime", "applies")
        self.assertEqual(triage.cell(rows[0], "regime"), "NIS2")
        self.assertEqual(triage.cell(rows[0], "applies"), "`yes`")

    def test_a_table_without_the_required_headings_is_not_matched(self):
        rows = triage.table_rows("| Thing | Other |\n|---|---|\n| a | b |\n",
                                 "regime", "applies")
        self.assertEqual(rows, [])

    def test_the_separator_row_is_not_data(self):
        rows = triage.table_rows(self.APPLICABILITY, "regime", "applies")
        self.assertNotIn("---", triage.cell(rows[0], "regime"))


class TestEndToEnd(unittest.TestCase):
    """Runs triage.py as a subprocess, the way SKILL.md does."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = pathlib.Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.skill = self.tmp / "arb-preflight"
        shutil.copytree(SKILL, self.skill,
                        ignore=shutil.ignore_patterns("__pycache__", "reviews"))
        self.register = self.skill / "standards" / "obligations-register.md"

    def run_triage(self, expect_code=0):
        out = self.tmp / "triage.json"
        proc = subprocess.run([sys.executable, str(self.skill / "scripts" / "triage.py"),
                               "--skill", str(self.skill), "--out", str(out)],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, expect_code,
                         f"{proc.stdout}\n{proc.stderr}")
        data = json.loads(out.read_text(encoding="utf-8")) if expect_code == 0 else {}
        return data, proc

    def blocked(self, data, domain) -> set:
        return {b["rule_id"] for b in data["domains"][domain]["blocked"]}

    def test_the_shipped_standards_block_the_regulatory_domain(self):
        data, proc = self.run_triage()
        self.assertEqual(len(data["domains"]["REG"]["assess"]), 3)
        self.assertIn("NOTE:", proc.stdout)

    def test_confirming_one_regime_unblocks_only_its_own_obligations(self):
        """OBL-DAT-04 is the only obligation citing PCI DSS, so confirming PCI DSS must
        not unblock obligations that cite other regimes."""
        text = self.register.read_text(encoding="utf-8")
        self.register.write_text(
            text.replace("| PCI DSS 4.0 | Payment card data | `TBC` |",
                         "| PCI DSS 4.0 | Payment card data | `yes` |"), encoding="utf-8")
        after, _ = self.run_triage()
        before = shipped_triage()
        freed = self.blocked(before, "DAT") - self.blocked(after, "DAT")
        self.assertTrue(freed, "confirming a regime must make something assessable")
        for rule in freed:
            row = next(a for a in after["domains"]["DAT"]["assess"] if a["rule_id"] == rule)
            self.assertIn("OBL-DAT-04", row["standard"],
                          f"{rule} was unblocked but does not cite the confirmed regime")

    def test_a_renamed_applicability_heading_fails_loudly(self):
        """These files are edited by their owners. A heading they rename must stop the run,
        not silently change which obligations are in scope."""
        text = self.register.read_text(encoding="utf-8")
        self.register.write_text(text.replace("| Regime | Scope | Applies | Entity scope |",
                                              "| Law | Scope | In scope? | Entity scope |"),
                                 encoding="utf-8")
        _, proc = self.run_triage(expect_code=1)
        self.assertIn("Applicability table", proc.stderr)

    def test_a_renamed_obligations_heading_fails_loudly(self):
        text = self.register.read_text(encoding="utf-8")
        self.register.write_text(
            text.replace("| ID | Obligation | Regimes (examples) | Internal control | What the board asks |",
                         "| Ref | Obligation | Laws | Internal control | What the board asks |"),
            encoding="utf-8")
        _, proc = self.run_triage(expect_code=1)
        self.assertIn("obligations table", proc.stderr)

    def test_every_rule_is_either_assessed_or_blocked_exactly_once(self):
        data, _ = self.run_triage()
        rubric_ids = []
        for f in sorted((self.skill / "rubric").glob("*.md")):
            rubric_ids += re.findall(r"^\| `([A-Z]{2,3}-[A-Z0-9]{2,4}-\d{3})`",
                                     f.read_text(encoding="utf-8"), re.M)
        triaged = [r["rule_id"] for d in data["domains"].values()
                   for r in d["assess"] + d["blocked"]]
        self.assertEqual(sorted(triaged), sorted(rubric_ids))


_SHIPPED_CACHE: dict = {}


def shipped_triage() -> dict:
    """triage.json for the standards as shipped, for before/after comparisons."""
    if not _SHIPPED_CACHE:
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "t.json"
            subprocess.run([sys.executable, str(SCRIPTS / "triage.py"), "--out", str(out)],
                           capture_output=True, text=True, check=True)
            _SHIPPED_CACHE.update(json.loads(out.read_text(encoding="utf-8")))
    return _SHIPPED_CACHE


if __name__ == "__main__":
    unittest.main(verbosity=2)
