"""Standing permission for dev writes (ADR-0024): recorded once in the person's words, it replaces the typed
confirmation of `apply`, `bootstrap` and `migrate` on an environment whose role is dev — and nowhere else. Fake
Pleasanter on 127.0.0.1 only."""
import contextlib
import io
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pls  # noqa: E402
import pls_profile_records as PR  # noqa: E402
import test_http as TH  # noqa: E402
import test_apply_recovery_and_readback as TR  # noqa: E402
import test_migrate_over_http as TM  # noqa: E402


class StandingPermissionTest(unittest.TestCase):
    setUp_http = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown
    plan = TH.HttpTest.plan
    bootstrap_plan = TR.RecoveryTest.bootstrap_plan
    migration = TM.MigrateTest.migration

    def setUp(self):
        self.setUp_http()
        (self.r / "CLAUDE.md").write_text("| Approvers | Nam (all gates) |\n", encoding="utf-8")

    def allow(self, value="on", env="dev", approver="Nam"):
        return pls.main(["profile", "set", "dev-writes", value, "--env", env, "--approver", approver,
                         "--quote", f"dev-writes {value}: the agent may write to my {env}"])

    def ready_plan(self, rel):
        plan, d = self.plan(rel)
        for site in plan["sites"]:
            plan["per_site"][site]["payload_file"] = f"payload-{site}.json"
        (d / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
        return d

    def apply(self, rel):
        n, out = len(self.fake.calls), io.StringIO()
        with contextlib.redirect_stdout(out):
            code = pls.main(["apply", rel])                                     # no --yes, no terminal
        writes = [p for p, _ in self.fake.calls[n:] if p.endswith("/updatesite")]
        return code, writes, out.getvalue()

    def set_envs(self, fn):
        p = self.r / "environments.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
        fn(doc["envs"])
        p.write_text(json.dumps(doc), encoding="utf-8")

    def test_without_a_record_apply_on_dev_needs_the_person(self):
        self.ready_plan("R-1")
        code, writes, out = self.apply("R-1")
        self.assertEqual((code, writes), (1, []))
        self.assertIn("not confirmed", out)

    def test_the_recorded_permission_confirms_apply_on_dev_and_is_named_in_the_release(self):
        d = self.ready_plan("R-1")
        self.assertEqual(self.allow(), 0)
        code, writes, out = self.apply("R-1")
        self.assertEqual(len(writes), 2)
        self.assertIn("confirmed by the standing permission for writes to dev: gates/profile/", out)
        log = json.loads((d / "apply-log.json").read_text(encoding="utf-8"))
        self.assertTrue(log["confirmed"].startswith("standing permission (gates/profile/"), log["confirmed"])
        self.assertIn("Nam", log["confirmed"])

    def test_a_revoked_permission_asks_the_person_again(self):
        self.ready_plan("R-1")
        self.assertEqual(self.allow("on"), 0)
        self.assertEqual(self.allow("off"), 0)
        self.assertEqual(self.apply("R-1")[:2], (1, []))

    def test_it_never_covers_stg_or_prod(self):
        self.set_envs(lambda e: e.update(stg=dict(e["dev"], role="stg"), prd=dict(e["dev"], role="prod")))
        for env in ("stg", "prd"):
            with self.assertRaisesRegex(pls.Fail, "only to an environment whose role is dev"):
                self.allow(env=env)
        self.assertEqual(self.allow(), 0)                                        # recorded while dev was dev …
        self.set_envs(lambda e: e["dev"].update(role="stg"))                     # … then relabelled by hand
        self.assertIsNone(PR.dev_writes(self.r, "dev"))

    def test_recording_refuses_an_environment_whose_file_role_is_not_dev(self):
        self.assertEqual(pls.main(["profile", "set", "role", "dev", "--env", "dev", "--approver", "Nam",
                                   "--quote", "dev is our dev"]), 0)
        self.set_envs(lambda e: e["dev"].update(role="stg"))                     # file says stg, the record dev
        with self.assertRaisesRegex(pls.Fail, "only to an environment whose role is dev"):
            self.allow()                                                         # would never take effect

    def test_a_role_record_other_than_dev_wins_over_the_file(self):
        self.assertEqual(self.allow(), 0)
        self.assertEqual(pls.main(["profile", "set", "role", "stg", "--env", "dev", "--approver", "Nam",
                                   "--quote", "dev is really our staging"]), 0)
        self.set_envs(lambda e: e["dev"].update(role="dev"))                     # file edited back to dev by hand
        self.assertIsNone(PR.dev_writes(self.r, "dev"))

    def test_a_sandbox_needs_its_own_record(self):
        self.set_envs(lambda e: e.update({"dev-nam": dict(e["dev"], sandbox_of="dev")}))
        self.assertEqual(self.allow(), 0)
        self.assertIsNone(PR.dev_writes(self.r, "dev-nam"))
        self.assertEqual(self.allow(env="dev-nam"), 0)
        self.assertIsNotNone(PR.dev_writes(self.r, "dev-nam"))

    def test_only_apply_bootstrap_and_migrate_are_covered(self):
        self.assertEqual(self.allow(), 0)
        for cmd in ("apply", "bootstrap", "migrate"):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertTrue(pls._confirm_write(self.r, cmd, "dev", "R-1", False, "w").startswith("standing permission"))
        for cmd in ("principals", "test-users", "test", "kb-verify"):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertIsNone(pls._confirm_write(self.r, cmd, "dev", "R-1", False, "w"), cmd)

    def test_a_damaged_record_falls_back_to_the_person(self):
        self.assertEqual(self.allow(), 0)
        bad = self.r / "gates/profile/2026-01-01-broken.json"
        bad.write_text("{ not json", encoding="utf-8")
        self.assertIsNone(PR.dev_writes(self.r, "dev"))

    def test_recording_needs_an_approver_a_value_and_an_environment(self):
        with self.assertRaisesRegex(pls.Fail, "not an approver"):
            self.allow(approver="Somebody")
        with self.assertRaisesRegex(pls.Fail, "`on` or `off`"):
            self.allow(value="yes")
        with self.assertRaisesRegex(pls.Fail, "--env must name"):
            self.allow(env="nowhere")
        with self.assertRaisesRegex(pls.Fail, "--env must name"):                     # no --env at all
            pls.main(["profile", "set", "dev-writes", "on", "--approver", "Nam", "--quote", "q"])

    def test_an_unreadable_environments_file_refuses_the_record(self):
        (self.r / "environments.json").write_text("{ half-saved", encoding="utf-8")
        with self.assertRaisesRegex(pls.Fail, "environments.json is not readable"):
            self.allow()

    def test_bootstrap_and_migrate_run_under_the_permission_and_record_it(self):
        self.assertEqual(self.allow(), 0)
        d = self.bootstrap_plan()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(pls.main(["bootstrap", "B-1"]), 0)                         # no --yes, no terminal
        self.assertNotIn("confirmed", json.loads((d / "bootstrap.json").read_text(encoding="utf-8")))   # G4-covered file
        runs = json.loads((d / "bootstrap-log.json").read_text(encoding="utf-8"))["runs"]
        self.assertEqual(len(runs), 1)
        self.assertTrue(runs[0]["confirmed"].startswith("standing permission (gates/profile/"), runs)
        self.plan("R-1")
        self.migration()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(pls.main(["migrate", "R-1"]), 0)
        run = json.loads((self.r / "releases/R-1/plan.json").read_text(encoding="utf-8"))["migrations_run"][-1]
        self.assertEqual(run["status"], "migrated")
        self.assertTrue(run["confirmed"].startswith("standing permission (gates/profile/"), run)

    def test_a_partial_stg_bootstrap_is_resumed_under_the_same_g4(self):
        import pls_gate as GT
        import test_gate as TG
        TG.StgWriteTest.stg(self)
        d = self.r / "releases/B-1"
        d.mkdir(parents=True)
        self.set_envs(lambda e: e["stg"]["sites"].update({"x1": {"title": "X1"}, "x2": {"title": "X2"}}))
        steps = [{"op": "createsite", "site": s, "parent_id": TH.FOLDER,
                  "payload": {"Title": s, "ReferenceType": "Results", "SiteSettings": {}}} for s in ("x1", "x2")]
        (d / "bootstrap.json").write_text(json.dumps({"release": "B-1", "env": "stg", "parent_id": TH.FOLDER,
                                                      "steps": steps, "status": "planned"}), encoding="utf-8")
        GT.record(self.r, "G4", "approved", "Nam", "G4 approved", [], ["B-1"], "2026-11-08")
        TR.RecoveryTest.slow(self, "/createsite")                                       # x1 times out: outcome unknown
        conns = json.loads((self.r / ".pls/connections.json").read_text(encoding="utf-8"))
        conns["stg"].update(url=self.url, timeout=1)
        (self.r / ".pls/connections.json").write_text(json.dumps(conns), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(pls.main(["bootstrap", "B-1", "--yes"]), 1)
            self.fake.hang_on = None
            self.assertEqual(pls.main(["bind", "--env", "stg", "--release", "B-1", "--created",
                                       f"x1={max(self.fake.sites)}"]), 0)
            self.assertEqual(pls.main(["bootstrap", "B-1", "--yes"]), 0)                 # same G4, nothing re-approved
        runs = json.loads((d / "bootstrap-log.json").read_text(encoding="utf-8"))["runs"]
        self.assertEqual([x["confirmed"] for x in runs], ["--yes", "--yes"])

    def test_only_apply_bootstrap_and_migrate_call_the_standing_permission(self):
        import re
        src = (Path(pls.__file__)).read_text(encoding="utf-8")
        calls = re.findall(r'_confirm_write\(r, "([a-z-]+)"', src)
        self.assertEqual(len(calls), src.count("_confirm_write(") - 1)                  # every call matched (not the def)
        self.assertEqual(sorted(calls), ["apply", "bootstrap", "migrate"])
        self.assertEqual(pls.STANDING_PERMISSION_COMMANDS, ("apply", "bootstrap", "migrate"))

    def test_a_record_by_someone_who_is_not_an_approver_does_not_count(self):
        self.assertEqual(self.allow(), 0)
        (self.r / "CLAUDE.md").write_text("| Approvers | Taro (all gates) |\n", encoding="utf-8")   # Nam is no longer one
        self.assertIsNone(PR.dev_writes(self.r, "dev"))
        self.assertTrue(any("not an approver" in i["msg"] for i in PR.lint(self.r)))
        (self.r / "CLAUDE.md").write_text("| Approvers | Nam (all gates) |\n", encoding="utf-8")
        forged = self.r / "gates/profile/2099-01-01-dev-writes-dev-forged.json"         # hand-written, not by pls
        forged.write_text(json.dumps({"kind": "profile", "field": "dev-writes", "value": "on", "env": "dev-nam",
                                      "approver": "Mallory", "quote": "x", "at": "2026-01-01T00:00:00+00:00"}),
                          encoding="utf-8")
        self.set_envs(lambda e: e.update({"dev-nam": dict(e["dev"], sandbox_of="dev")}))
        self.assertIsNone(PR.dev_writes(self.r, "dev-nam"))

    def test_a_withdrawal_at_the_same_instant_wins(self):
        base = {"kind": "profile", "field": "dev-writes", "env": "dev", "approver": "Nam", "quote": "q",
                "at": "2026-01-01T00:00:00+00:00"}
        d = self.r / "gates/profile"
        d.mkdir(parents=True)
        for name, value in (("a-on", "on"), ("b-off", "off"), ("c-on", "on")):
            (d / f"2026-01-01-{name}.json").write_text(json.dumps(dict(base, value=value)), encoding="utf-8")
        self.assertIsNone(PR.dev_writes(self.r, "dev"))

    def test_an_empty_quote_is_refused(self):
        with self.assertRaisesRegex(pls.Fail, "own words"):
            pls.main(["profile", "set", "dev-writes", "on", "--env", "dev", "--approver", "Nam", "--quote", "  "])

    def test_an_unknown_field_is_refused(self):
        import pls_gate as GT
        with self.assertRaisesRegex(GT.GateError, "field is one of"):
            PR.set_field(self.r, "nonsense", "x", "Nam", "q")


if __name__ == "__main__":
    unittest.main()
