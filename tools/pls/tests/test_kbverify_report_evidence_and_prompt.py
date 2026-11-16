"""The kb-verify report keeps every check a probe made, passing ones included (the KB curator records a pass from
them), and its confirmation asks for the command name, not a release id. Fake Pleasanter on 127.0.0.1 only:
python -m unittest discover -s tools/pls/tests -v"""
import contextlib
import io
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent))
import pls  # noqa: E402
import pls_kbverify as KV  # noqa: E402
import test_http as TH  # noqa: E402
import test_kbverify as TK  # noqa: E402
import test_tests_outside_dev_need_the_person as TO  # noqa: E402

LISTED = {"entry": "D1", "site": {"ReferenceType": "Results", "SiteSettings": {}},
          "tests": [{"id": "D1", "steps": [{"op": "create", "save": "r", "data": {"Title": "kbprobe"}},
                                            {"op": "list", "contains": ["$r"]}]}]}


class KbVerifyReportEvidenceTest(unittest.TestCase):
    setUp = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown
    use_kb = TK.CliTest.use_kb
    set_env = TK.CliTest.set_env

    def report(self):
        data = json.loads(next((self.r / "ops/kb-verify").glob("*-dev.json")).read_text(encoding="utf-8"))
        return {p["probe"]: p for p in data["probes"]}

    def test_passing_checks_are_in_the_report(self):
        self.use_kb({"D1-ok": TK.OK, "D1-listed": LISTED})
        self.set_env()
        self.assertEqual(pls.main(["kb-verify", "--env", "dev", "--yes"]), 0)
        got = self.report()
        self.assertEqual(got["D1-ok"]["status"], "pass")
        self.assertTrue(any(x.startswith("ok") and "ClassHash.ClassA" in x for x in got["D1-ok"]["log"]),
                        got["D1-ok"]["log"])
        self.assertTrue(any(x.startswith("ok") and "in view" in x for x in got["D1-listed"]["log"]),
                        got["D1-listed"]["log"])

    def test_the_confirmation_asks_for_the_command_name(self):
        self.use_kb({"D1-ok": TK.OK})
        self.set_env()
        out = io.StringIO()
        with TO.typed("kb-verify"), contextlib.redirect_stdout(out):
            self.assertEqual(pls.main(["kb-verify", "--env", "dev"]), 0)
        self.assertIn("type the command name to confirm (kb-verify)", out.getvalue())
        self.assertNotIn("release id", out.getvalue())


class KbVerifyMarkdownDetailTest(unittest.TestCase):
    def test_a_failing_check_after_long_passing_ones_is_shown(self):
        log = [f"ok  {i} in view" for i in range(40)] + ["NG  rB not in view"]
        md = KV.report("dev", None, [{"entry": "D1", "probe": "D1-x", "status": "fail", "log": log}], [], "2026-11-14")
        row = next(x for x in md.splitlines() if x.startswith("| D1 | D1-x"))
        self.assertIn("NG  rB not in view", row)
        self.assertIn("full log in the .json", row)


    def test_a_failure_reason_that_is_not_ng_is_shown_too(self):
        log = [f"ok  {i} in view" for i in range(40)] + ["control D1-control did not pass"]
        md = KV.report("dev", None, [{"entry": "D1", "probe": "D1-x", "status": "inconclusive", "log": log}], [], "d")
        self.assertIn("control D1-control did not pass", next(x for x in md.splitlines() if x.startswith("| D1 | D1-x")))


class KbEntryIdsTest(unittest.TestCase):
    def test_a_split_entry_id_sorts_and_reports(self):
        rows = [{"entry": e, "probe": f"{e}-x", "status": "pass", "log": []} for e in ("D41a", "D5", "D41", "D4a")]
        md = KV.report("dev", None, rows, ["D40", "D38"], "d")
        order = [x.split(" | ")[0][2:] for x in md.splitlines() if x.startswith("| D") and x.count("|") == 3]
        self.assertEqual(order, ["D4a", "D5", "D41", "D41a"])

    def test_every_entry_of_the_framework_probes_reports(self):
        probes = HERE.parents[3] / "skills/pls-kb-pleasanter/references/probes"
        entries = sorted({json.loads(f.read_text(encoding="utf-8"))["entry"] for f in probes.glob("D*.json")})
        rows = [{"entry": e, "probe": f"{e}-x", "status": "pass", "log": []} for e in entries]
        self.assertIn("D41a", entries)
        KV.report("dev", None, rows, [], "d")


if __name__ == "__main__":
    unittest.main()
