"""G4 covers exactly what is written: the record stores the digest of the planned release, and apply / bootstrap on
stg refuse when the plan, a payload, a rollback file or the target changed since the person approved it. Every step
apply writes must match the per-site entries the environment check reads. Fake Pleasanter on 127.0.0.1 only."""
import json
import unittest

import pls
import pls_gate as GT
import test_gate as TG
import test_http as TH

R = "R-20261108-01"


class G4BindingTest(unittest.TestCase):
    setUp = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown
    plan = TH.HttpTest.plan
    stg = TG.StgWriteTest.stg
    writes = TG.StgWriteTest.writes

    def rel(self):
        return self.r / "releases" / R

    def g4(self, quote="G4 approved, apply"):
        return json.loads(GT.record(self.r, "G4", "approved", "Nam", quote, [], [R], "2026-11-08").read_text(encoding="utf-8"))

    def edit_plan(self, **kw):
        p = self.rel() / "plan.json"
        p.write_text(json.dumps(dict(json.loads(p.read_text(encoding="utf-8")), **kw)), encoding="utf-8")

    def test_the_record_names_the_content_it_approves(self):
        self.stg()
        b = self.g4()["bound"][R]
        self.assertEqual(b["env"], "stg")
        self.assertEqual(len(b["sha256"]), 64)

    def test_a_payload_changed_after_g4_is_never_written(self):
        self.stg()
        self.g4()
        f = self.rel() / "payload-loans.json"
        f.write_text(f.read_text(encoding="utf-8").replace("new loans", "new loanz"), encoding="utf-8")
        n = len(self.fake.calls)
        self.assertEqual(pls.main(["apply", R, "--yes"]), 2)
        self.assertEqual(self.writes(n), [])
        self.g4("G4 approved again after seeing the new payload")                   # the person approves the new content
        pls.main(["apply", R, "--yes"])
        self.assertTrue(self.writes(n))
        self.assertIn(json.loads((self.rel() / "plan.json").read_text(encoding="utf-8"))["status"], pls.APPLIED)

    def test_a_rollback_file_or_the_plan_changed_after_g4_is_refused(self):
        self.stg()
        self.g4()
        f = self.rel() / "rollback-loans.json"
        f.write_text(f.read_text(encoding="utf-8").replace("old", "olD"), encoding="utf-8")
        n = len(self.fake.calls)
        self.assertEqual(pls.main(["apply", R, "--yes"]), 2)
        f.write_text(f.read_text(encoding="utf-8").replace("olD", "old"), encoding="utf-8")
        self.edit_plan(classification="data-impacting")
        self.assertEqual(pls.main(["apply", R, "--yes"]), 2)
        self.assertEqual(self.writes(n), [])

    def test_a_target_changed_after_g4_is_refused(self):
        self.stg()
        self.g4()
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["envs"]["stg2"] = dict(envs["envs"]["stg"])
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        c = json.loads((self.r / ".pls/connections.json").read_text(encoding="utf-8"))
        c["stg2"] = dict(c["stg"])
        (self.r / ".pls/connections.json").write_text(json.dumps(c), encoding="utf-8")
        self.edit_plan(env="stg2")
        n = len(self.fake.calls)
        self.assertEqual(pls.main(["apply", R, "--yes"]), 2)
        self.assertEqual(self.writes(n), [])

    def test_g4_recorded_before_the_plan_does_not_cover_it(self):
        self.stg()
        plan = (self.rel() / "plan.json").read_text(encoding="utf-8")
        (self.rel() / "plan.json").unlink()
        self.assertIsNone(self.g4()["bound"][R])
        (self.rel() / "plan.json").write_text(plan, encoding="utf-8")
        n = len(self.fake.calls)
        self.assertEqual(pls.main(["apply", R, "--yes"]), 2)
        self.assertEqual(self.writes(n), [])

    def test_fields_written_after_g4_do_not_break_the_binding(self):
        self.stg()
        self.g4()
        self.edit_plan(post_apply_check="x", readback={}, checked_at="t")
        self.assertIsNone(GT.require(self.r, "G4", R, "applying to stg"))

    def test_a_hand_written_releases_string_does_not_match_by_substring(self):
        self.stg()
        (self.r / "gates").mkdir(exist_ok=True)
        (self.r / "gates/2026-11-08-G4-x.json").write_text(json.dumps(
            {"gate": "G4", "decision": "approved", "approver": "Nam", "date": "2026-11-08", "at": "2026-11-08T10:00:00+09:00",
             "releases": R + "0"}), encoding="utf-8")
        self.assertIsNone(GT.latest(self.r, "G4", release=R))


class PlanStepsMatchPerSiteTest(unittest.TestCase):
    setUp = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown
    plan = TH.HttpTest.plan

    def test_an_edited_step_site_id_is_never_written(self):
        plan, d = self.plan()
        plan["steps"][1]["site_id"] = TH.FOLDER                                    # not a site of this env
        (d / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
        n = len(self.fake.calls)
        self.assertEqual(pls.main(["apply", "R-1", "--yes"]), 2)
        self.assertFalse([p for p, _ in self.fake.calls[n:] if p.endswith("/updatesite")])

    def test_steps_must_list_every_site_once_in_order(self):
        plan, _ = self.plan()
        self.assertIsNone(pls.plan_steps_problem(plan))
        for broken in (dict(plan, steps=plan["steps"][:1]), dict(plan, steps=plan["steps"][::-1]),
                       dict(plan, rollback=plan["rollback"][::-1]), dict(plan, steps="x")):
            self.assertIsNotNone(pls.plan_steps_problem(broken))
        bad_file = json.loads(json.dumps(plan))
        bad_file["per_site"]["loans"]["payload_file"] = "payload-loans.json"
        bad_file["steps"][1]["payload_file"] = "payload-equipment.json"
        self.assertIsNotNone(pls.plan_steps_problem(bad_file))


if __name__ == "__main__":
    unittest.main()
