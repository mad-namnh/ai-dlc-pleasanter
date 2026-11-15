"""Guard inputs and attestations come from records of the person's words, not from files an agent can edit (I4):
profile rows Approvers / Operators / Origin / Role tests and environment roles (`pls profile set`), the as-is review that lets
DES-000 clear L-LAD-01 (`pls review as-is`), refs decisions (`--quote`) and the jobs deploy confirmation."""
import json
import tempfile
import unittest
from pathlib import Path

import pls
import pls_gate as GT
import pls_profile_records as PR
import test_pls as TP

PRF = lambda issues: [i["msg"] for i in issues if i["rule"] == "L-PRF-01"]     # noqa: E731


def edit_row(root: Path, field: str, value: str) -> None:
    """A hand edit of a profile row, as an agent could make it."""
    p = root / "CLAUDE.md"
    p.write_text(PR._row(field).sub(f"| {field} | {value} |", p.read_text(encoding="utf-8"), count=1), encoding="utf-8")


class ProfileRecordTest(unittest.TestCase):
    tearDown = TP.PlsTest.tearDown

    def setUp(self):
        TP.PlsTest.setUp(self)
        (self.r / "CLAUDE.md").write_text("| Item | Value |\n|---|---|\n| Origin | `new` |\n| Approvers | Nam (all gates) |\n"
                                          "| Operators | dev: Nam; stg: Nam |\n", encoding="utf-8")

    def test_a_hand_edit_of_approvers_after_its_record_changes_nothing(self):
        PR.set_field(self.r, "Approvers", "Nam (all gates)", "Nam", "Nam approves every gate")
        edit_row(self.r, "Approvers", "Nam (all gates), Claude (all gates)")
        with self.assertRaisesRegex(pls.Fail, "not an approver"):
            pls.main(["gate", "G1", "--approver", "Claude", "--item", "REQ-001", "--quote", "approved"])
        self.assertTrue(any("differs from its record" in m for m in PRF(PR.lint(self.r))))
        self.assertEqual(pls.main(["profile", "set", "Approvers", "Nam (all gates), Taro (G3)", "--approver", "Nam",
                                   "--quote", "add Taro for G3"]), 0)
        self.assertEqual(GT._approver_for(self.r, "taro", "G3"), "Taro")
        self.assertIn("| Approvers | Nam (all gates), Taro (G3) |", (self.r / "CLAUDE.md").read_text(encoding="utf-8"))

    def test_who_may_set_a_value(self):
        (self.r / "CLAUDE.md").write_text("| Approvers | G1, G4: <name>; G2, G3: <name> |\n| Origin | `new` |\n", encoding="utf-8")
        with self.assertRaisesRegex(GT.GateError, "record Approvers first"):
            PR.set_field(self.r, "Origin", "existing", "Nam", "it is a takeover")
        with self.assertRaisesRegex(GT.GateError, "must name the person"):
            PR.set_field(self.r, "Approvers", "Taro (all gates)", "Nam", "Taro approves")
        PR.set_field(self.r, "Approvers", "Nam (all gates)", "nam", "I approve every gate")
        with self.assertRaisesRegex(GT.GateError, "not an approver"):
            PR.set_field(self.r, "Approvers", "Claude (all gates)", "Claude", "me")
        with self.assertRaisesRegex(GT.GateError, "own words"):
            PR.set_field(self.r, "Origin", "existing", "Nam", "  ")
        with self.assertRaisesRegex(GT.GateError, "`new` or `existing`"):
            PR.set_field(self.r, "Origin", "old", "Nam", "x")
        self.assertEqual(len(list((self.r / "gates/profile").glob("*.json"))), 1)

    def test_origin_existing_cannot_be_edited_away(self):
        PR.set_field(self.r, "Approvers", "Nam (all gates)", "Nam", "Nam approves every gate")
        PR.set_field(self.r, "Origin", "existing", "Nam", "we take over the running app")
        edit_row(self.r, "Origin", "`new`")
        with self.assertRaisesRegex(pls.Fail, "onboarding"):
            pls.main(["step", "P1", "new request"])

    def test_operators_come_from_the_record(self):
        PR.set_field(self.r, "Approvers", "Nam (G1, G2, G3)", "Nam", "Nam approves G1 to G3")
        PR.set_field(self.r, "Operators", "dev: Nam; stg: Nam", "Nam", "Nam deploys dev and stg")
        edit_row(self.r, "Operators", "dev: Nam; stg: Nam, Mallory")
        with self.assertRaisesRegex(GT.GateError, "neither an operator"):
            GT.job_verifier(self.r, "Mallory", "stg")
        self.assertEqual(GT.job_verifier(self.r, "Nam", "stg")["role"], "operator")

    def test_environment_role_is_recorded_and_hand_edits_are_reported(self):
        PR.set_field(self.r, "Approvers", "Nam (all gates)", "Nam", "Nam approves every gate")
        self.assertTrue(any("envs.stg.role has no record" in m for m in PRF(PR.lint(self.r))))
        self.assertFalse(any("envs.dev.role" in m for m in PRF(PR.lint(self.r))))       # made by setup / init
        self.assertEqual(pls.main(["profile", "set", "role", "stg", "--env", "stg", "--approver", "Nam",
                                   "--quote", "the stg server is the customer's test copy"]), 0)
        self.assertFalse(any("envs.stg.role" in m for m in PRF(PR.lint(self.r))))
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["envs"]["stg"]["role"] = "dev"
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        self.assertTrue(any("envs.stg.role 'dev' differs from its record 'stg'" in m for m in PRF(PR.lint(self.r))))
        with self.assertRaisesRegex(pls.Fail, "--env must name"):
            pls.main(["profile", "set", "role", "stg", "--env", "nowhere", "--approver", "Nam", "--quote", "x"])

    def test_role_tests_change_only_with_the_persons_words(self):
        # deferring role tests lowers what G3 proves: a hand edit is reported, the recorded value is the one shown
        p = self.r / "CLAUDE.md"
        p.write_text(p.read_text(encoding="utf-8") + "| Role tests | `per-role keys` |\n", encoding="utf-8")
        self.assertTrue(any("Role tests has no record" in m for m in PRF(PR.lint(self.r))))
        self.assertEqual(pls.main(["profile", "set", "Role tests", "per-role keys", "--approver", "Nam",
                                   "--quote", "role tests with a key per role"]), 0)
        self.assertEqual([m for m in PRF(PR.lint(self.r)) if "Role tests" in m], [])
        edit_row(self.r, "Role tests", "`deferred`")
        self.assertTrue(any("Role tests 'deferred' differs from its record" in m for m in PRF(PR.lint(self.r))))
        self.assertIn("| Role tests | `per-role keys` |", PR.effective_profile_text(self.r))
        self.assertEqual(pls.main(["profile", "set", "Role tests", "`deferred`", "--approver", "Nam",
                                   "--quote", "chon C: chi co key admin"]), 0)
        self.assertIn("| Role tests | `deferred` |", p.read_text(encoding="utf-8"))
        with self.assertRaisesRegex(GT.GateError, "Role tests is `deferred` or `per-role keys`"):
            PR.set_field(self.r, "Role tests", "none", "Nam", "no role tests")

    def test_an_unrecorded_role_tests_row_is_reported_unless_it_is_the_template_and_the_hint_runs(self):
        import shlex
        p = self.r / "CLAUDE.md"
        base = p.read_text(encoding="utf-8")
        for row, reported in (("`deferred` (one key, the operator's …) / `per-role keys` (a test user …)", False),
                              ("`deferred`", True), ("`deferred` (only an admin key, chosen C)", True),
                              ("deferred - no keys", True), ("`Deferred`", True)):
            with self.subTest(row=row):
                p.write_text(base + f"| Role tests | {row} |\n", encoding="utf-8")
                msgs = [m for m in PRF(PR.lint(self.r)) if "Role tests" in m]
                self.assertEqual(bool(msgs), reported, msgs)
        p.write_text(base + "| Role tests | `deferred` |\n", encoding="utf-8")
        hint = next(m for m in PRF(PR.lint(self.r)) if "Role tests" in m).split("pls profile set ", 1)[1]
        args = shlex.split(hint.replace("<name>", "Nam").replace("<their words>", "role tests deferred"))
        self.assertEqual(pls.main(["profile", "set", *args]), 0)                  # the printed command runs as printed
        self.assertEqual([m for m in PRF(PR.lint(self.r)) if "Role tests" in m], [])
        self.assertFalse([x for x in (self.r / "gates/profile").iterdir() if " " in x.name])   # no spaces in file names

    def test_unrecorded_rows_are_reported_and_a_damaged_record_refuses(self):
        self.assertEqual(len([m for m in PRF(PR.lint(self.r)) if "CLAUDE.md" in m and "has no record" in m]), 3)
        PR.set_field(self.r, "Approvers", "Nam (all gates)", "Nam", "Nam approves every gate")
        bad = self.r / "gates/profile/broken.json"
        bad.write_text("{", encoding="utf-8")
        with self.assertRaisesRegex(GT.GateError, "broken.json"):
            GT._approver_for(self.r, "Nam", "G1")
        self.assertTrue(any("broken.json" in m for m in PRF(PR.lint(self.r))))


class InitRecordsTest(unittest.TestCase):
    def test_init_with_an_approver_records_the_profile(self):
        with tempfile.TemporaryDirectory() as t:
            target = Path(t) / "app"
            pls.init_project(target, "demo", "dev", "Nam", origin="existing")
            fields = sorted(json.loads(p.read_text(encoding="utf-8"))["field"] for p in (target / "gates/profile").glob("*.json"))
            self.assertEqual(fields, ["Approvers", "Operators", "Origin", "Role tests"])
            self.assertIn("| Role tests | `deferred` |", (target / "CLAUDE.md").read_text(encoding="utf-8"))
            self.assertEqual(PRF(PR.lint(target)), [])
            self.assertEqual(GT.origin(target), "existing")


class AsIsReviewTest(unittest.TestCase):
    tearDown = TP.PlsTest.tearDown
    unpack_dev = TP.PlsTest.unpack_dev

    def setUp(self):
        TP.PlsTest.setUp(self)
        self.unpack_dev(scripts=[{"Id": 1, "Name": "calc", "Body": "context.Log('a');"},
                                 {"Id": 2, "Name": "late", "Body": "context.Log('b');"}])
        (self.r / "design/as-is").mkdir(parents=True)
        (self.r / "design/decisions").mkdir(parents=True, exist_ok=True)
        self.doc = self.r / "design/as-is/a.md"
        self.doc.write_text("# a\n## 9. スクリプト\n- calc: 合計を計算する\n", encoding="utf-8")

    def lad(self):
        return sorted(i["msg"] for i in pls.lint(self.r) if i["rule"] == "L-LAD-01")

    def test_des_000_clears_only_reviewed_scripts_of_an_unchanged_document(self):
        self.assertEqual(len(self.lad()), 2)                                  # the as-is document itself decides nothing
        (self.r / "design/decisions/DES-000-as-is-a.md").write_text(
            "# DES-000\n- calc: existing behaviour, adopted\n- late: existing behaviour, adopted\n", encoding="utf-8")
        self.assertEqual(len(self.lad()), 2)                                  # written by the agent, no review record
        with self.assertRaisesRegex(pls.Fail, "own words|required"):
            pls.main(["review", "as-is", "a", "--approver", "Nam", "--quote", " "])
        with self.assertRaisesRegex(pls.Fail, "not an approver"):
            pls.main(["review", "as-is", "a", "--approver", "Claude", "--quote", "reviewed"])
        self.assertEqual(pls.main(["review", "as-is", "a", "--approver", "Nam", "--quote", "I read the as-is of a, it is right"]), 0)
        self.assertEqual(len(self.lad()), 1)
        self.assertIn("'late'", self.lad()[0])                                # not in the reviewed document
        self.doc.write_text(self.doc.read_text(encoding="utf-8") + "- late: 追記\n", encoding="utf-8")
        self.assertEqual(len(self.lad()), 2)                                  # changed after the review
        pls.main(["review", "as-is", "a", "--approver", "Nam", "--quote", "reviewed again with late"])
        self.assertEqual(self.lad(), [])

    def test_review_needs_the_document(self):
        with self.assertRaisesRegex(pls.Fail, "spec-skeleton"):
            pls.main(["review", "as-is", "nosuch", "--approver", "Nam", "--quote", "ok"])


class JobsVerifiedTest(unittest.TestCase):
    setUp = TP.PlsTest.setUp
    tearDown = TP.PlsTest.tearDown

    def rel(self, name, verified):
        d = self.r / "releases" / name
        d.mkdir(parents=True)
        jobs = {"fingerprints": {"j": name}, "changed": ["j changed"], **({"verified": verified} if verified else {})}
        (d / "plan.json").write_text(json.dumps({"release": name, "env": "stg", "status": "applied",
                                                 "applied_at": "2026-11-05T10:00:00+09:00", "jobs": jobs}), encoding="utf-8")

    def test_a_hand_written_confirmation_is_not_a_deploy_baseline(self):
        good = {"by": "Nam", "role": "g4-approver", "env": "stg", "quote": "copied and compared", "at": "2026-11-05T11:00:00+09:00"}
        for name, v in (("R-mallory", dict(good, by="Mallory")), ("R-noquote", dict(good, quote="")),
                        ("R-otherenv", dict(good, env="dev")), ("R-truthy", "yes")):
            with self.subTest(name):
                self.rel(name, v)
                self.assertIsNone(pls.last_applied_jobs(self.r, "stg"))
        self.rel("R-ok", good)
        self.assertEqual(pls.last_applied_jobs(self.r, "stg"), {"j": "R-ok"})


if __name__ == "__main__":
    unittest.main()
