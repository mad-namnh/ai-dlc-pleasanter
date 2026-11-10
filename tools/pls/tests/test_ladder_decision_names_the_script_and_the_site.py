"""L-LAD-01: a server script has a design decision only when a decision document names that script and its site as
whole names — not when the name occurs somewhere in the design folder (I5):
python -m unittest discover -s tools/pls/tests -v"""
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
import pls_as_is_review_records as AR  # noqa: E402


class LadderDecision(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.r = Path(self.tmp.name)
        (self.r / "design/decisions").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def doc(self, rel, text):
        p = self.r / "design" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def decided(self, name, site):
        return AR.ladder_decided(self.r)(name, site)

    def test_a_decision_row_naming_the_script_and_the_site_decides_it(self):
        self.doc("decisions/DES-001-loans.md",
                 "| L10 | loans server script `validate-dates` | BeforeCreate | 002 | **3** |\n\n**Rung 3 reason:** no standard setting.\n")
        self.assertTrue(self.decided("validate-dates", "loans"))

    def test_a_japanese_sentence_around_the_name_still_names_it(self):
        self.doc("decisions/DES-002.md", "サイトloansのサーバスクリプトcheckLimitで上限を検証する（rung 3）。\n")
        self.assertTrue(self.decided("checkLimit", "loans"))

    def test_a_name_that_is_only_part_of_another_word_is_not_a_decision(self):
        self.doc("decisions/DES-001-loans.md", "The label of loans is changed; see ab-test and table columns.\n")
        self.assertFalse(self.decided("ab", "loans"))
        self.assertFalse(self.decided("label", "loan"))               # the site name is matched as a whole name too

    def test_a_decision_about_another_site_does_not_cover_this_one(self):
        self.doc("decisions/DES-001-equipment.md", "| E1 | equipment server script `validate` | … | 001 | **3** |\n")
        self.assertTrue(self.decided("validate", "equipment"))
        self.assertFalse(self.decided("validate", "loans"))

    def test_design_files_that_are_not_decisions_decide_nothing(self):
        for rel in ("as-is/loans.md", "probes/PRB-001.md", "notes.md", "decisions/notes-loans.md"):
            self.doc(rel, "loans server script `validate-dates` exists.\n")
        self.assertFalse(self.decided("validate-dates", "loans"))

    def test_an_as_is_decision_without_a_recorded_review_decides_nothing(self):
        self.doc("as-is/loans.md", "| validate-dates | BeforeUpdate |\n")
        self.doc("decisions/DES-000-as-is-loans.md", "Existing scripts of loans: validate-dates.\n")
        self.assertFalse(self.decided("validate-dates", "loans"))

    def test_a_script_without_a_name_is_never_decided(self):
        self.doc("decisions/DES-001-loans.md", "loans\n")
        self.assertFalse(self.decided("", "loans"))
        self.assertFalse(self.decided(None, "loans"))


if __name__ == "__main__":
    unittest.main()
