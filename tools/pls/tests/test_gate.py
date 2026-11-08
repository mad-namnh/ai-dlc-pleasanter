"""Gate decisions as records (I4): approvers from the profile, L-GATE-01, stg writes need G4."""
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent))
import pls  # noqa: E402
import pls_gate as GT  # noqa: E402
import test_http as TH  # noqa: E402

PROFILE = "| Item | Value |\n|---|---|\n| Approvers | G1, G4: Nam; G2, G3: Taro |\n"


class ApproversTest(unittest.TestCase):
    def test_profile_forms(self):
        self.assertEqual(GT.approvers("| Approvers | Nam (all gates) |"), {"Nam": set(GT.GATES)})
        self.assertEqual(GT.approvers("| Approvers | Nam (G1, G2), Taro (G3, G4) |"),
                         {"Nam": {"G1", "G2"}, "Taro": {"G3", "G4"}})
        self.assertEqual(GT.approvers(PROFILE), {"Nam": {"G1", "G4"}, "Taro": {"G2", "G3"}})
        self.assertEqual(GT.approvers("| Approvers | G1, G4: <name>; G2, G3: <name> |"), {})   # template placeholder
        self.assertEqual(GT.approvers("no profile row"), {})
        # a note in parentheses or an exception grants nothing (the person is asked); ranges expand
        self.assertEqual(GT.approvers("| Approvers | Nam (PM) |"), {})
        self.assertEqual(GT.approvers("| Approvers | Nam (all gates except G4) |"), {})
        self.assertEqual(GT.approvers("| Approvers | Nam (G1-G3) |"), {"Nam": {"G1", "G2", "G3"}})


class RecordTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.r = Path(self.tmp.name)
        (self.r / "CLAUDE.md").write_text(PROFILE, encoding="utf-8")
        (self.r / "environments.json").write_text(json.dumps({"envs": {}}), encoding="utf-8")
        self.cwd = os.getcwd()
        os.chdir(self.r)

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def gate(self, *argv):
        return pls.main(["gate", *argv])

    def test_record_checks_approver_gate_quote_and_scope(self):
        self.assertEqual(self.gate("G1", "--approver", "Nam", "--item", "REQ-001", "--quote", "G1 approved, continue"), 0)
        rec = GT.load(self.r)[0]
        self.assertEqual((rec["gate"], rec["approver"], rec["items"], rec["quote"]),
                         ("G1", "Nam", ["REQ-001"], "G1 approved, continue"))
        self.assertEqual(self.gate("G1", "--approver", "nam", "--item", "REQ-002", "--quote", "ok"), 0)   # case-insensitive
        self.assertEqual(GT.load(self.r)[1]["approver"], "Nam")
        for argv in (["G1", "--approver", "Claude", "--item", "REQ-1", "--quote", "x"],     # not in the profile
                     ["G2", "--approver", "Nam", "--item", "DES-001", "--quote", "x"],      # Nam does not approve G2
                     ["G2", "--approver", "Taro", "--item", "DES-001", "--quote", "  "],    # no words of the person
                     ["G2", "--approver", "Taro", "--quote", "x"],                          # G2 without DES ids
                     ["G4", "--approver", "Nam", "--quote", "x"]):                          # G4 without release
            with self.assertRaises(pls.Fail, msg=argv):
                self.gate(*argv)
        self.assertEqual(len(GT.load(self.r)), 2)

    def test_records_are_never_overwritten_and_the_last_one_wins(self):
        a = GT.record(self.r, "G4", "approved", "Nam", "ok", [], ["R-1"], "2026-11-08")
        b = GT.record(self.r, "G4", "rejected", "Nam", "stop", [], ["R-1"], "2026-11-08")
        a.unlink()                                                   # a gap must not make the next name collide
        c = GT.record(self.r, "G4", "approved", "Nam", "ok again", [], ["R-1"], "2026-11-08")
        self.assertNotEqual(b, c)
        self.assertEqual(json.loads(b.read_text(encoding="utf-8"))["decision"], "rejected")
        self.assertEqual(GT.latest(self.r, "G4", release="R-1")["quote"], "ok again")

    def test_require_rechecks_the_approver(self):
        (self.r / "gates").mkdir()
        (self.r / "gates/2026-11-08-G4-x.json").write_text(json.dumps(
            {"gate": "G4", "decision": "approved", "approver": "Claude", "date": "2026-11-08", "releases": ["R-1"]}), encoding="utf-8")
        with self.assertRaisesRegex(GT.GateError, "not an approver"):
            GT.require(self.r, "G4", "R-1", "applying to stg")

    def test_lint_reads_other_wordings_and_slugless_names(self):
        (self.r / "requirements").mkdir()
        (self.r / "requirements/REQ-007.md").write_text("- **Status:** G1 approved by Nam on 2026-11-08\n", encoding="utf-8")
        self.assertEqual(len(GT.lint(self.r)), 1)
        GT.record(self.r, "G1", "approved", "Nam", "yes", ["REQ-007"], [], "2026-11-08")
        self.assertEqual(GT.lint(self.r), [])

    def test_no_approver_in_profile_means_ask(self):
        (self.r / "CLAUDE.md").write_text("| Approvers | G1, G4: <name>; G2, G3: <name> |\n", encoding="utf-8")
        with self.assertRaisesRegex(GT.GateError, "ask the person"):
            GT.record(self.r, "G1", "approved", "Nam", "ok", ["REQ-001"], [], "2026-11-08")

    def test_lint_status_lines_need_records(self):
        (self.r / "requirements").mkdir()
        (self.r / "requirements/REQ-001-loan.md").write_text("- **Status:** G1 approved (Nam, 2026-11-08)\n", encoding="utf-8")
        (self.r / "requirements/REQ-002-ret.md").write_text("- **Status:** G1 approved (Claude, 2026-11-08)\n", encoding="utf-8")
        (self.r / "requirements/REQ-003-x.md").write_text("- **Status:** awaiting G1\n", encoding="utf-8")
        rel = self.r / "releases/R-20261108-01"
        rel.mkdir(parents=True)
        (rel / "g3-verification.md").write_text("- **Status:** G3 approved (Taro, 2026-11-08)\n", encoding="utf-8")
        (rel / "approvals.md").write_text("| G4 | approved: ok | Nam | 2026-11-08 |\n", encoding="utf-8")
        msgs = [i["msg"] for i in GT.lint(self.r)]
        self.assertEqual(len([m for m in msgs if "no approval record" in m]), 4, msgs)
        self.assertTrue(any("REQ-002" in m and "'Claude'" in m for m in msgs), msgs)
        GT.record(self.r, "G1", "approved", "Nam", "G1 approved", ["REQ-001", "REQ-002"], [], "2026-11-08")
        GT.record(self.r, "G3", "approved", "Taro", "G3 ok", [], ["R-20261108-01"], "2026-11-08")
        GT.record(self.r, "G4", "approved", "Nam", "G4 ok", [], ["R-20261108-01"], "2026-11-08")
        msgs = [i["msg"] for i in GT.lint(self.r)]
        self.assertEqual(len(msgs), 1, msgs)                      # only the approval by someone outside the profile
        self.assertIn("'Claude'", msgs[0])
        GT.record(self.r, "G4", "rejected", "Nam", "stop, wrong data", [], ["R-20261108-01"], "2026-11-08")
        self.assertTrue(any("approvals.md" in i["msg"] for i in GT.lint(self.r)))   # a later rejection overrides


class StgWriteTest(unittest.TestCase):
    setUp = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown
    plan = TH.HttpTest.plan

    def stg(self):
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["envs"]["stg"] = {"role": "stg", "parent_id": TH.FOLDER, "sites": {"equipment": {"id": TH.EQ, "title": "stg_E"},
                                                                                "loans": {"id": TH.LO, "title": "stg_L"}},
                               "side_effects": {"mail": "sink", "jobs": "disabled"}}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        c = json.loads((self.r / ".pls/connections.json").read_text(encoding="utf-8"))
        c["stg"] = dict(c["dev"])
        (self.r / ".pls/connections.json").write_text(json.dumps(c), encoding="utf-8")
        (self.r / "CLAUDE.md").write_text(PROFILE, encoding="utf-8")
        plan, d = self.plan("R-20261108-01")
        plan["env"] = "stg"
        for s in ("equipment", "loans"):
            plan["per_site"][s]["payload_file"] = f"payload-{s}.json"
        (d / "plan.json").write_text(json.dumps(plan), encoding="utf-8")

    def writes(self, n):
        return [p for p, _ in self.fake.calls[n:] if re.search(r"/(updatesite|createsite)$", p)]

    def test_apply_to_stg_needs_g4_of_that_release(self):
        self.stg()
        n = len(self.fake.calls)
        self.assertEqual(pls.main(["apply", "R-20261108-01", "--yes"]), 2)
        GT.record(self.r, "G4", "approved", "Nam", "G4 approved", [], ["R-20261108-02"], "2026-11-08")   # another release
        self.assertEqual(pls.main(["apply", "R-20261108-01", "--yes"]), 2)
        self.assertEqual(self.writes(n), [])
        GT.record(self.r, "G4", "approved", "Nam", "G4 approved, apply", [], ["R-20261108-01"], "2026-11-08")
        pls.main(["apply", "R-20261108-01", "--yes"])
        self.assertTrue(self.writes(n))

    def test_bootstrap_on_stg_needs_g4_naming_it(self):
        self.stg()
        b = self.r / "releases/B-20261108-stg"
        b.mkdir(parents=True)
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["envs"]["stg"]["sites"]["x1"] = {"title": "stg_X1"}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        (b / "bootstrap.json").write_text(json.dumps({"release": "B-20261108-stg", "env": "stg", "parent_id": TH.FOLDER,
                                                      "status": "planned", "steps": [{"op": "createsite", "site": "x1", "parent_id": TH.FOLDER,
                                                      "payload": {"Title": "stg_X1", "ReferenceType": "Results", "SiteSettings": {}}}]}),
                                          encoding="utf-8")
        n = len(self.fake.calls)
        self.assertEqual(pls.main(["bootstrap", "B-20261108-stg", "--yes"]), 2)
        self.assertEqual(self.writes(n), [])
        GT.record(self.r, "G4", "approved", "Nam", "G4 approved", [], ["R-20261108-01", "B-20261108-stg"], "2026-11-08")
        pls.main(["bootstrap", "B-20261108-stg", "--yes"])
        self.assertTrue(self.writes(n))

    def test_dev_needs_no_gate(self):
        plan, d = self.plan()
        for s in ("equipment", "loans"):
            plan["per_site"][s]["payload_file"] = f"payload-{s}.json"
        (d / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
        n = len(self.fake.calls)
        pls.main(["apply", "R-1", "--yes"])
        self.assertTrue(self.writes(n))

    def test_release_plan_for_stg_needs_g3(self):
        self.stg()
        with self.assertRaisesRegex(pls.Fail, "G3 approval of R-20261108-09"):
            pls.release_plan(self.r, "stg", "R-20261108-09", {}, None)
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        del envs["envs"]["stg"]["role"]                              # a missing role fails closed
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        with self.assertRaisesRegex(pls.Fail, "G3 approval"):
            pls.release_plan(self.r, "stg", "R-20261108-09", {}, None)


if __name__ == "__main__":
    unittest.main()
