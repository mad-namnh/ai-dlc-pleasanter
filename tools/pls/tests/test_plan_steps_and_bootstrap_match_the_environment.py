"""What apply, mark-applied and bootstrap act on is what the checks looked at: a release step must use its own site's
payload and planned snapshot, mark-applied reads back with the same rule, and a bootstrap step creates only a site of
the environment under the environment's folder. Fake Pleasanter on 127.0.0.1 only."""
import json
import re
import unittest

import pls
import test_http as TH


class ReleaseStepsTest(unittest.TestCase):
    setUp = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown
    plan = TH.HttpTest.plan

    def writes(self, n):
        return [p for p, _ in self.fake.calls[n:] if re.search(r"/(updatesite|createsite)$", p)]

    def edit(self, d, change):
        p = d / "plan.json"
        plan = json.loads(p.read_text(encoding="utf-8"))
        change(plan)
        p.write_text(json.dumps(plan), encoding="utf-8")

    def test_a_step_with_another_sites_payload_is_never_written(self):
        _, d = self.plan()                                        # per_site names no files: release-plan's names count
        self.edit(d, lambda p: p["steps"][0].update(payload_file="payload-loans.json"))
        n = len(self.fake.calls)
        self.assertEqual(pls.main(["apply", "R-1", "--yes"]), 2)
        self.assertEqual(self.writes(n), [])

    def test_an_edited_expected_snapshot_is_never_written(self):
        _, d = self.plan()

        def change(p):
            for s in p["sites"]:
                p["per_site"][s]["snapshot_updated_time"] = "t0"
            p["steps"][1]["expect_updated_time"] = "t-later"     # would let a changed site pass the preflight
        self.edit(d, change)
        n = len(self.fake.calls)
        self.assertEqual(pls.main(["apply", "R-1", "--yes"]), 2)
        self.assertEqual(self.writes(n), [])

    def test_mark_applied_refuses_steps_that_differ_from_per_site(self):
        _, d = self.plan()
        self.edit(d, lambda p: p["steps"][0].update(payload_file="payload-loans.json"))
        self.assertEqual(pls.main(["mark-applied", "R-1", "--export", "equipment=e.json", "--export", "loans=l.json"]), 1)
        self.assertEqual(json.loads((d / "plan.json").read_text(encoding="utf-8"))["status"], "planned")


class BootstrapStepsTest(unittest.TestCase):
    setUp = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown

    def bootstrap(self, steps, parent=TH.FOLDER):
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["envs"]["dev"]["sites"]["x1"] = {"title": "X1"}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        d = self.r / "releases/B-1"
        d.mkdir(parents=True, exist_ok=True)
        (d / "bootstrap.json").write_text(json.dumps({"release": "B-1", "env": "dev", "parent_id": parent, "status": "planned",
                                                      "steps": steps}), encoding="utf-8")
        n = len(self.fake.sites)
        code = pls.main(["bootstrap", "B-1", "--yes"])
        return code, len(self.fake.sites) - n

    def step(self, site="x1", parent=TH.FOLDER, op="createsite"):
        return {"op": op, "site": site, "parent_id": parent, "payload": {"Title": "X1", "ReferenceType": "Results", "SiteSettings": {}}}

    def test_only_sites_of_the_environment_under_its_folder(self):
        cases = {"site not in environments.json": [self.step("intruder")],
                 "step under another folder": [self.step(parent=12345)],
                 "same site twice": [self.step(), self.step()],
                 "not a createsite": [self.step(op="updatesite")]}
        for label, steps in cases.items():
            with self.subTest(label):
                self.assertEqual(self.bootstrap(steps), (2, 0))
        with self.subTest("plan under another folder"):
            self.assertEqual(self.bootstrap([self.step(parent=12345)], parent=12345), (2, 0))
        self.assertEqual(self.bootstrap([self.step()]), (0, 1))                       # control


if __name__ == "__main__":
    unittest.main()
