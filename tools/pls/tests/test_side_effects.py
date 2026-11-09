"""Mail and job safety outside production (ADR-0010):  python -m unittest discover -s tools/pls/tests -v"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pls  # noqa: E402
import pls_side_effects as SE  # noqa: E402
import test_http as TH  # noqa: E402
import test_pls as TP  # noqa: E402

NOTIFY = [{"Id": 1, "Type": 1, "Address": "[Manager]", "Subject": "s"}]


def write_job(r: Path, name="nightly", body="context.Log('x');", entry=True):
    d = r / SE.JOBS_DIR
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{name}.js").write_bytes(body.encode("utf-8"))
    if entry:
        (d / SE.JOBS_INDEX).write_text(json.dumps([{"name": name, "schedule": "毎日 02:00", "enabled": True}]), encoding="utf-8")


class JobsPureTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.r = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_declared_jobs_fingerprint_entry_and_body(self):
        self.assertEqual(SE.declared_jobs(self.r), {})
        write_job(self.r)
        a = SE.declared_jobs(self.r)
        self.assertEqual(list(a), ["nightly"])
        write_job(self.r, body="context.Log('y');")
        self.assertNotEqual(SE.declared_jobs(self.r), a)                     # body change
        write_job(self.r)
        idx = self.r / SE.JOBS_DIR / SE.JOBS_INDEX
        idx.write_text(json.dumps([{"name": "nightly", "schedule": "毎週", "enabled": True}]), encoding="utf-8")
        self.assertNotEqual(SE.declared_jobs(self.r), a)                     # schedule change

    def test_body_without_entry_still_counts_and_is_a_lint_problem(self):
        write_job(self.r, entry=False)
        self.assertEqual(list(SE.declared_jobs(self.r)), ["nightly"])
        self.assertIn("not listed", SE.job_problems(self.r)[0])
        (self.r / SE.JOBS_DIR / SE.JOBS_INDEX).write_text(json.dumps([{"name": "a"}, {"name": "a"}]), encoding="utf-8")
        with self.assertRaises(ValueError):
            SE.declared_jobs(self.r)
        self.assertIn("used twice", SE.job_problems(self.r)[0])
        (self.r / SE.JOBS_DIR / SE.JOBS_INDEX).write_text("{}", encoding="utf-8")
        self.assertIn("must be a list", SE.job_problems(self.r)[0])

    def test_changed_jobs_and_refusals(self):
        self.assertEqual(SE.changed_jobs({"a": "1", "b": "2"}, {"a": "1", "b": "3", "c": "4"}), ["b changed", "c added"])
        self.assertEqual(SE.changed_jobs({"a": "1"}, {}), ["a removed"])
        self.assertIn("no applied release", SE.changed_jobs(None, {"a": "1"})[0])
        unk, live, off = ({"mail": "sink", "jobs": j} for j in ("unknown", "live", "disabled"))
        self.assertIsNotNone(SE.jobs_test_refusal("dev", unk, {"a": "1"})[0])
        self.assertEqual(SE.jobs_test_refusal("dev", unk, {}), (None, None))
        self.assertIsNotNone(SE.jobs_test_refusal("dev", live, {"a": "1"})[1])
        self.assertEqual(SE.jobs_test_refusal("dev", off, {"a": "1"}), (None, None))
        self.assertIsNotNone(SE.jobs_apply_refusal("dev", unk, ["a added"], True)[0])
        self.assertIsNotNone(SE.jobs_apply_refusal("dev", live, ["a added"], True)[1])
        self.assertEqual(SE.jobs_apply_refusal("dev", unk, [], True), (None, None))
        self.assertIsNotNone(SE.jobs_apply_refusal("dev", live, None, True)[0])      # planned before the check
        self.assertEqual(SE.jobs_apply_refusal("dev", unk, None, False), (None, None))
        self.assertIsNone(SE.manual_job_step("dev", []))
        self.assertIn("サーバスクリプト", SE.manual_job_step("dev", ["a added"]))
        self.assertEqual(SE.cautious({"mail": "sink", "jobs": "disabled"}, {"mail": "live", "jobs": "unknown"}),
                         {"mail": "live", "jobs": "unknown"})
        self.assertEqual(SE.cautious({"mail": "sink", "jobs": "disabled"}, {"mail": "disabled", "jobs": "disabled"}),
                         {"mail": "disabled", "jobs": "disabled"})                 # tie → the base's value
        self.assertIsNotNone(SE.bad_plan_jobs({"changed": ""}))
        self.assertIsNone(SE.bad_plan_jobs({"changed": [], "fingerprints": None}))

    def test_rendered_bodies_and_directories_named_js(self):
        write_job(self.r, body="x = ${site:a};")
        (self.r / SE.JOBS_DIR / "folder.js").mkdir()                        # not a body
        jobs = SE.load_jobs(self.r, lambda v: v.replace("${site:a}", "101") if isinstance(v, str) else v)
        self.assertEqual(list(jobs), ["nightly"])
        self.assertEqual(jobs["nightly"]["body"], "x = 101;")
        self.assertNotEqual(SE.fingerprints(jobs), SE.declared_jobs(self.r))   # an env value is part of the job
        (self.r / SE.JOBS_DIR / "nightly.js").write_bytes(b"\xff\xfe")
        with self.assertRaises(ValueError):
            SE.declared_jobs(self.r)


class PureTest(unittest.TestCase):
    def test_effects_default_unknown_and_reject_unknown_values(self):
        self.assertEqual(SE.effects({}), {"mail": "unknown", "jobs": "unknown"})
        self.assertEqual(SE.effects({"side_effects": {"mail": "sink"}}), {"mail": "sink", "jobs": "unknown"})
        with self.assertRaises(ValueError):
            SE.effects({"side_effects": {"mail": "off"}})
        with self.assertRaises(ValueError):
            SE.effects({"side_effects": {"jobs": "sink"}})        # a job cannot run into a mail sink
        with self.assertRaises(ValueError):
            SE.effects({"side_effects": "sink"})                  # not an object: a clear error, not a crash

    def test_changed_mail_elements_covers_site_and_process_notifications_and_reminders(self):
        before = {"Notifications": NOTIFY, "Processes": [{"Id": 1, "Name": "return"}]}
        after = {"Notifications": [dict(NOTIFY[0], Subject="new")], "Reminders": [{"Id": 1, "Subject": "r"}],
                 "Processes": [{"Id": 1, "Name": "return", "Notifications": [{"Id": 1, "Address": "[Owner]"}]}]}
        self.assertEqual(SE.changed_mail_elements(before, after),
                         ["Notifications[1] changed", "Processes[return:1].Notifications[1] added", "Reminders[1] added"])
        self.assertEqual(SE.changed_mail_elements(after, before)[-1], "Reminders[1] removed")
        self.assertEqual(SE.changed_mail_elements(before, before), [])
        self.assertEqual(SE.changed_mail_elements({"Columns": [1]}, {"Columns": [2]}), [])   # not a mail element

    def test_literal_addresses_only_in_mail_elements_and_not_placeholders_or_references(self):
        settings = {"Notifications": [{"Id": 1, "Address": "[Manager],soumu@example.co.jp", "Body": "${env:MAIL_TO}"}],
                    "Reminders": [{"Id": 2, "To": "x.y+z@corp.example"}],
                    "ServerScripts": [{"Name": "s", "Body": "// owner@example.com"}]}
        self.assertEqual(SE.literal_addresses(settings), [("Notifications[1]", "soumu@example.co.jp"),
                                                          ("Reminders[2]", "x.y+z@corp.example")])

    def test_address_glued_to_japanese_text_is_found(self):
        settings = {"Notifications": [{"Id": 1, "Body": "担当soumu@example.co.jpへ連絡"}]}
        self.assertEqual(SE.literal_addresses(settings), [("Notifications[1]", "soumu@example.co.jp")])

    def test_processes_with_the_same_name_and_items_without_id_keep_separate_keys(self):
        settings = {"Processes": [{"Id": 1, "Name": "p", "Notifications": [{"Id": 1, "Address": "a@x.jp"}]},
                                  {"Id": 2, "Name": "p", "Notifications": [{"Id": 1, "Address": "b@x.jp"}]}],
                    "Notifications": [{"Id": 1}, {"Address": "c@x.jp"}]}
        self.assertEqual(len(SE.mail_elements(settings)), 4)
        self.assertEqual(sorted(a for _, a in SE.literal_addresses(settings)), ["a@x.jp", "b@x.jp", "c@x.jp"])

    def test_which_tests_write_and_where(self):
        read_only = {"steps": [{"op": "get", "record": "$e"}, {"op": "siteConfig", "expect": {}}]}
        self.assertFalse(SE.test_writes(read_only))
        all_sites = {900, 901, 902}
        # create with a site; exec on the record it created -> only that site
        spec = {"run_on": "902", "steps": [{"op": "create", "site": "901", "save": "e"}, {"op": "exec", "record": "$e"}]}
        self.assertTrue(SE.test_writes(spec))
        self.assertEqual(SE.test_sites(spec, 900, all_sites), {"901"})
        # create without a site goes to the command's site, never to run_on
        self.assertEqual(SE.test_sites({"run_on": "902", "steps": [{"op": "create"}]}, 900, all_sites), {"900"})
        # mixed creates: both sites
        self.assertEqual(SE.test_sites({"steps": [{"op": "create", "site": "901"}, {"op": "create"}]}, 900, all_sites), {"900", "901"})
        # update on a --var fixture: its site is unknown -> every site of the env
        self.assertEqual(SE.test_sites({"steps": [{"op": "update", "record": "$LOAN"}]}, 900, all_sites), {"900", "901", "902"})

    def test_apply_refusal_by_declared_state(self):
        changed = {"loans": ["Notifications[1] added"], "equipment": []}
        refusal, warning = SE.apply_refusal("dev", {"mail": "unknown", "jobs": "unknown"}, changed)
        self.assertIn("REFUSED", refusal)
        self.assertIsNone(warning)
        self.assertIn("real mail", SE.apply_refusal("stg", {"mail": "live", "jobs": "unknown"}, changed)[1])
        self.assertEqual(SE.apply_refusal("dev", {"mail": "sink", "jobs": "unknown"}, changed), (None, None))
        # a plan made before this check records nothing (None): refused unless mail is safe
        self.assertIn("planned before", SE.apply_refusal("stg", {"mail": "live", "jobs": "unknown"}, {"loans": None})[0])
        self.assertEqual(SE.apply_refusal("dev", {"mail": "disabled", "jobs": "unknown"}, {"loans": None}), (None, None))
        self.assertEqual(SE.apply_refusal("dev", {"mail": "unknown", "jobs": "unknown"}, {"loans": []}), (None, None))


class LintTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.r = Path(self.tmp.name)
        self.cwd = os.getcwd()
        os.chdir(self.r)

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def test_literal_address_and_bad_side_effects_value_are_lint_errors(self):
        envs = json.loads(json.dumps(TP.ENVS))
        envs["envs"]["stg"]["side_effects"] = {"mail": "maybe"}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        exp = TP.export(101, 102, "http://dev.internal")
        exp["Response"]["Data"]["SiteSettings"]["Notifications"] = [{"Id": 1, "Type": 1, "Address": "boss@example.co.jp"}]
        (self.r / "dev.json").write_text(json.dumps(exp), encoding="utf-8")
        self.assertEqual(pls.main(["unpack", "dev.json", "--env", "dev", "--site", "a"]), 0)
        rules = [(i["rule"], i["msg"]) for i in pls.lint(self.r)]
        self.assertIn("L-MAIL-01", {x for x, _ in rules})
        self.assertTrue(any(x == "L-ENV-02" and "stg" in m for x, m in rules))


class HttpSideEffectsTest(unittest.TestCase):
    setUp = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown
    plan = TH.HttpTest.plan

    def set_mail(self, state):
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["envs"]["dev"]["side_effects"] = {"mail": state}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")

    def full_plan(self, side_effects=None):
        plan, d = self.plan()
        for s in ("equipment", "loans"):
            plan["per_site"][s]["payload_file"] = f"payload-{s}.json"     # what mark-applied reads after apply
        if side_effects:
            plan["per_site"]["loans"]["side_effects"] = side_effects
        (d / "plan.json").write_text(json.dumps(plan), encoding="utf-8")

    def write_spec(self, steps):
        (self.r / "s.json").write_text(json.dumps([{"id": "T-1", "steps": steps}]), encoding="utf-8")

    def test_writing_tests_on_a_site_that_sends_mail_are_refused_until_mail_is_safe(self):
        self.fake.sites[TH.EQ]["SiteSettings"]["Notifications"] = NOTIFY
        self.write_spec([{"op": "create", "site": "${site:equipment}", "save": "e", "data": {"Title": "テスト"}}])
        self.assertEqual(pls.main(["test", "s.json", "--env", "dev", "--site", "equipment", "--out", "x.json"]), 2)
        self.assertEqual(self.fake.records, {})                               # nothing sent
        self.set_mail("sink")
        self.assertEqual(pls.main(["test", "s.json", "--env", "dev", "--site", "equipment", "--out", "x.json"]), 0)
        self.assertEqual(len(self.fake.records), 1)

    def test_read_only_tests_and_sites_without_mail_are_not_blocked(self):
        self.fake.sites[TH.EQ]["SiteSettings"]["Notifications"] = NOTIFY
        self.write_spec([{"op": "siteConfig", "expect": {"Notifications.0.Id": 1}}])
        self.assertEqual(pls.main(["test", "s.json", "--env", "dev", "--site", "equipment", "--out", "x.json"]), 0)
        self.write_spec([{"op": "create", "site": "${site:loans}", "save": "l", "data": {}}])     # loans sends no mail
        self.assertEqual(pls.main(["test", "s.json", "--env", "dev", "--site", "loans", "--out", "y.json"]), 0)

    def test_apply_of_a_release_changing_mail_elements_is_refused_while_mail_is_unknown(self):
        self.full_plan(["Notifications[1] added"])
        self.assertEqual(pls.main(["apply", "R-1", "--yes"]), 2)
        self.assertFalse(any(p.endswith("/updatesite") for p, _ in self.fake.calls))        # nothing written
        self.set_mail("disabled")
        pls.main(["apply", "R-1", "--yes"])
        self.assertTrue(any(p.endswith("/updatesite") for p, _ in self.fake.calls))

    def test_release_without_mail_changes_is_not_affected(self):
        self.full_plan()
        pls.main(["apply", "R-1", "--yes"])
        self.assertTrue(any(p.endswith("/updatesite") for p, _ in self.fake.calls))

    def test_plan_made_before_the_check_is_refused_while_mail_is_unknown(self):
        plan, d = self.plan()
        for s in ("equipment", "loans"):
            plan["per_site"][s].pop("side_effects")
            plan["per_site"][s]["payload_file"] = f"payload-{s}.json"
        (d / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
        self.assertEqual(pls.main(["apply", "R-1", "--yes"]), 2)
        self.assertFalse(any(p.endswith("/updatesite") for p, _ in self.fake.calls))

    def test_update_of_a_fixture_record_checks_every_site(self):
        self.fake.sites[TH.LO]["SiteSettings"]["Notifications"] = NOTIFY          # only loans sends mail
        self.fake.records[555] = {"site": TH.LO, "ResultId": 555, "Status": 100}
        self.write_spec([{"op": "update", "record": "$LOAN", "data": {}}])
        self.assertEqual(pls.main(["test", "s.json", "--env", "dev", "--site", "equipment", "--var", "LOAN=555", "--out", "x.json"]), 2)
        self.assertFalse(any(p.endswith("/update") for p, _ in self.fake.calls))

    # ---------------------------------------------------------- scheduled server scripts (jobs, ADR-0012)

    def set_effects(self, **kw):
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["envs"]["dev"]["side_effects"] = kw
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")

    def test_writing_tests_are_refused_while_jobs_are_unknown_and_the_project_declares_any(self):
        self.write_spec([{"op": "create", "site": "${site:equipment}", "save": "e", "data": {}}])
        self.assertEqual(pls.main(["test", "s.json", "--env", "dev", "--site", "equipment", "--out", "x.json"]), 0)  # no jobs
        write_job(self.r)
        self.fake.records.clear()
        self.assertEqual(pls.main(["test", "s.json", "--env", "dev", "--site", "equipment", "--out", "x.json"]), 2)
        self.assertEqual(self.fake.records, {})                               # nothing sent
        self.set_effects(jobs="live")                                         # a person knows they run: warning only
        self.assertEqual(pls.main(["test", "s.json", "--env", "dev", "--site", "equipment", "--out", "x.json"]), 0)
        self.set_effects(jobs="unknown")
        self.write_spec([{"op": "siteConfig", "expect": {}}])                 # read-only tests are never blocked
        self.assertEqual(pls.main(["test", "s.json", "--env", "dev", "--site", "equipment", "--out", "y.json"]), 0)

    def test_apply_of_a_release_changing_jobs_is_refused_while_jobs_are_unknown(self):
        self.full_plan()
        write_job(self.r)
        plan = json.loads((self.r / "releases/R-1/plan.json").read_text(encoding="utf-8"))
        plan["jobs"] = {"fingerprints": SE.declared_jobs(self.r), "changed": ["nightly added"], "deploy": "manual",
                        "manual_step": SE.manual_job_step("dev", ["nightly added"])}
        (self.r / "releases/R-1/plan.json").write_text(json.dumps(plan), encoding="utf-8")
        self.assertEqual(pls.main(["apply", "R-1", "--yes"]), 2)
        self.assertFalse(any(p.endswith("/updatesite") for p, _ in self.fake.calls))
        self.set_effects(jobs="disabled")
        pls.main(["apply", "R-1", "--yes"])
        self.assertTrue(any(p.endswith("/updatesite") for p, _ in self.fake.calls))

    def test_plan_without_jobs_record_is_refused_only_when_the_project_declares_jobs(self):
        self.full_plan()                                                      # no "jobs" key: planned before the check
        write_job(self.r)
        self.assertEqual(pls.main(["apply", "R-1", "--yes"]), 2)
        self.assertFalse(any(p.endswith("/updatesite") for p, _ in self.fake.calls))
        self.set_effects(jobs="disabled")
        pls.main(["apply", "R-1", "--yes"])
        self.assertTrue(any(p.endswith("/updatesite") for p, _ in self.fake.calls))

    def job_plan(self, over=None):
        self.full_plan()
        plan = json.loads((self.r / "releases/R-1/plan.json").read_text(encoding="utf-8"))
        plan["jobs"] = {"fingerprints": SE.declared_jobs(self.r), "changed": ["nightly added"], "deploy": "manual",
                        "manual_step": SE.manual_job_step("dev", ["nightly added"], "R-1"), **(over or {})}
        (self.r / "releases/R-1/plan.json").write_text(json.dumps(plan), encoding="utf-8")

    def test_apply_is_refused_when_git_jobs_changed_since_the_plan(self):
        write_job(self.r)
        self.set_effects(jobs="disabled")
        self.job_plan()
        write_job(self.r, body="context.Log('changed after the plan');")
        self.assertEqual(pls.main(["apply", "R-1", "--yes"]), 2)
        self.assertFalse(any(p.endswith("/updatesite") for p, _ in self.fake.calls))

    def test_apply_refuses_a_hand_broken_jobs_record(self):
        write_job(self.r)
        self.set_effects(jobs="disabled")
        for broken in ({"changed": "nightly added"}, {"changed": 5}, {"fingerprints": ["x"]}):
            self.job_plan(broken)
            self.assertEqual(pls.main(["apply", "R-1", "--yes"]), 2)
            self.assertFalse(any(p.endswith("/updatesite") for p, _ in self.fake.calls))
            (self.r / "releases/R-1/plan.json").unlink()
            for f in (self.r / "releases/R-1").iterdir():
                f.unlink()
            (self.r / "releases/R-1").rmdir()

    def test_sandbox_uses_the_riskier_of_its_copy_and_the_base(self):
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["envs"]["dev"]["side_effects"] = {"mail": "unknown", "jobs": "unknown"}     # changed after the sandbox
        sb = {"role": "dev", "sandbox_of": "dev", "sites": {}, "side_effects": {"mail": "sink", "jobs": "disabled"}}
        envs["envs"]["dev-x"] = sb
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        self.assertEqual(pls.env_effects(self.r, sb), {"mail": "unknown", "jobs": "unknown"})
        envs["envs"]["dev"]["side_effects"] = {"mail": "disabled", "jobs": "disabled"}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        self.assertEqual(pls.env_effects(self.r, dict(sb, side_effects={"jobs": "live"})), {"mail": "unknown", "jobs": "live"})

    def test_create_without_site_is_checked_on_the_command_site_not_run_on(self):
        self.fake.sites[TH.LO]["SiteSettings"]["Notifications"] = NOTIFY
        (self.r / "s.json").write_text(json.dumps([{"id": "T-1", "run_on": "${site:equipment}",
                                                    "steps": [{"op": "create", "save": "l", "data": {}}]}]), encoding="utf-8")
        self.assertEqual(pls.main(["test", "s.json", "--env", "dev", "--site", "loans", "--out", "x.json"]), 2)
        self.assertEqual(self.fake.records, {})


if __name__ == "__main__":
    unittest.main()
