"""Coverage counts the test results of one environment, tells failed, errored and never-run tests apart, shows
pass-api-only, checks the design links, and never reports an empty traceability as covered (I8):
python -m unittest discover -s tools/pls/tests -v"""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
import pls  # noqa: E402


class CoverageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.r = Path(self.tmp.name)
        (self.r / "config/a").mkdir(parents=True)
        (self.r / "config/a/site.json").write_text(json.dumps({"Columns": [{"ColumnName": "ClassA"}]}), encoding="utf-8")
        (self.r / "design/decisions").mkdir(parents=True)
        (self.r / "design/decisions/DES-001-loans.md").write_text("# DES-001\n", encoding="utf-8")
        (self.r / "tests/results").mkdir(parents=True)
        self.trace({"REQ-001": {"design": ["DES-001"], "config": ["config/a/site.json#Columns[ClassA]"], "tests": ["T-1", "T-2"]}})

    def tearDown(self):
        self.tmp.cleanup()

    def trace(self, doc):
        (self.r / "traceability.json").write_text(json.dumps(doc), encoding="utf-8")

    def result(self, name, env, at, **status):
        (self.r / "tests/results" / f"{name}.json").write_text(json.dumps(
            {"env": env, "executed_at": at, "tests": [{"id": k.replace("_", "-"), "status": v} for k, v in status.items()]}),
            encoding="utf-8")

    def row(self, env="dev"):
        c = pls.coverage(self.r, env)
        return c["ok"], c["rows"][0]

    def test_all_linked_tests_passed_in_the_environment_is_covered(self):
        self.result("dev-1", "dev", "2026-11-10T01:00:00.000Z", T_1="pass", T_2="pass")
        ok, row = self.row()
        self.assertTrue(ok)
        self.assertEqual((row["status"], row["passed"], row["api_only"]), ("covered", 2, 0))

    def test_pass_api_only_is_counted_apart_and_shown(self):
        self.result("dev-1", "dev", "2026-11-10T01:00:00.000Z", T_1="pass", T_2="pass-api-only")
        ok, row = self.row()
        self.assertTrue(ok)
        self.assertEqual((row["passed"], row["api_only"]), (1, 1))
        out = io.StringIO()
        (self.r / "environments.json").write_text(json.dumps({"envs": {"dev": {"role": "dev", "sites": {}}}}), encoding="utf-8")
        import os
        cwd = os.getcwd()
        os.chdir(self.r)
        try:
            with contextlib.redirect_stdout(out):
                self.assertEqual(pls.main(["coverage"]), 0)
        finally:
            os.chdir(cwd)
        self.assertIn("api-only: 1", out.getvalue())

    def test_failed_errored_and_never_run_are_told_apart(self):
        self.trace({"REQ-001": {"design": ["DES-001"], "config": ["config/a/site.json#Columns[ClassA]"],
                                "tests": ["T-1", "T-2", "T-3", "T-4"]}})
        self.result("dev-1", "dev", "2026-11-10T01:00:00.000Z", T_1="pass", T_2="fail", T_3="error")
        ok, row = self.row()
        self.assertFalse(ok)
        self.assertEqual((row["status"], row["passed"], row["failed"], row["error"], row["not_run"]), ("GAP", 1, 1, 1, 1))

    def test_a_result_of_another_environment_never_hides_a_failure(self):
        self.result("dev-1", "dev", "2026-11-10T01:00:00.000Z", T_1="pass", T_2="pass")
        self.result("stg-1", "stg", "2026-11-10T02:00:00.000Z", T_1="pass", T_2="fail")
        self.assertEqual(self.row("dev")[1]["status"], "covered")
        self.assertEqual(self.row("stg")[1]["status"], "GAP")
        self.result("zz-dev-2", "dev", "2026-11-10T03:00:00.000Z", T_2="pass")       # a later dev run changes nothing on stg
        self.assertEqual(self.row("stg")[1]["failed"], 1)

    def test_the_latest_run_in_the_environment_counts_whatever_the_file_name(self):
        self.result("z-old", "dev", "2026-11-09T01:00:00.000Z", T_1="pass", T_2="fail")
        self.result("a-new", "dev", "2026-11-10T01:00:00.000Z", T_2="pass")
        self.assertEqual(self.row()[1]["status"], "covered")
        self.result("a-new", "dev", "2026-11-08T01:00:00.000Z", T_2="pass")           # now older than the failure
        self.assertEqual(self.row()[1]["status"], "GAP")

    def test_an_empty_traceability_is_a_gap(self):
        self.trace({})
        self.assertFalse(pls.coverage(self.r)["ok"])

    def test_a_design_link_must_name_an_existing_decision_document(self):
        self.result("dev-1", "dev", "2026-11-10T01:00:00.000Z", T_1="pass", T_2="pass")
        for design in (["DES-002"], ["design/decisions/DES-001-loans.md#x"], []):
            self.trace({"REQ-001": {"design": design, "config": ["config/a/site.json#Columns[ClassA]"], "tests": ["T-1", "T-2"]}})
            ok, row = self.row()
            self.assertFalse(ok, design)
            self.assertEqual(row["status"], "GAP")
        self.trace({"REQ-001": {"config": ["config/a/site.json#Columns[ClassA]"], "tests": ["T-1", "T-2"]}})
        self.assertIn("no design link", self.row()[1]["why"])


if __name__ == "__main__":
    unittest.main()
