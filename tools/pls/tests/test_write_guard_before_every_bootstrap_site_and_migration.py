"""The write guard is read again before every createsite of `bootstrap` and before every migration of `migrate`
(design review C1, TD-39): a change made while a command runs — `allow_write` turned off, the role changed, the G4
record gone on stg — stops the next write; what was already written stays recorded. Fake Pleasanter on 127.0.0.1."""
import contextlib
import io
import json
import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pls  # noqa: E402
import pls_gate as GT  # noqa: E402
import test_gate as TG  # noqa: E402
import test_http as TH  # noqa: E402
import test_apply_recovery_and_readback as TR  # noqa: E402
import test_migrate_over_http as TM  # noqa: E402


class GuardReadAgainTest(unittest.TestCase):
    setUp = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown
    plan = TH.HttpTest.plan
    bootstrap_plan = TR.RecoveryTest.bootstrap_plan
    migration = TM.MigrateTest.migration

    def after_first(self, suffix, change):
        """Run change() right after the first request whose path ends with suffix has been answered."""
        orig, done = self.fake.handle, []

        def handle(path, body):
            out = orig(path, body)
            if path.endswith(suffix) and not done:
                done.append(path)
                change()
            return out
        self.fake.handle = handle

    def set_conn(self, env, **kw):
        p = self.r / ".pls/connections.json"
        c = json.loads(p.read_text(encoding="utf-8"))
        c[env].update(kw)
        p.write_text(json.dumps(c), encoding="utf-8")

    def set_env(self, env, **kw):
        p = self.r / "environments.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
        doc["envs"][env].update(kw)
        p.write_text(json.dumps(doc), encoding="utf-8")

    def run_quiet(self, *args):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = pls.main(list(args))
        return code, out.getvalue()

    def creates(self):
        return [p for p, _ in self.fake.calls if p.endswith("/createsite")]

    # ---------------------------------------------------------------- bootstrap

    def test_bootstrap_stops_before_the_next_site_when_writes_are_turned_off(self):
        d = self.bootstrap_plan()
        self.after_first("/createsite", lambda: self.set_conn("dev", allow_write=False))
        code, out = self.run_quiet("bootstrap", "B-1", "--yes")
        self.assertEqual(code, 1)
        self.assertEqual(len(self.creates()), 1)                                    # x2 never sent
        self.assertIn("stopped before x2", out)
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        self.assertTrue(envs["envs"]["dev"]["sites"]["x1"].get("id"))               # x1 bound, not lost
        self.assertNotIn("uncertain", json.loads((d / "bootstrap.json").read_text(encoding="utf-8")))

    def test_bootstrap_stops_when_the_role_is_changed_to_prod(self):
        self.bootstrap_plan()
        self.after_first("/createsite", lambda: self.set_env("dev", role="prod"))
        code, out = self.run_quiet("bootstrap", "B-1", "--yes")
        self.assertEqual((code, len(self.creates())), (1, 1))
        self.assertIn("stopped before x2", out)
        self.assertNotIn("uncertain", json.loads((self.r / "releases/B-1/bootstrap.json").read_text(encoding="utf-8")))

    def test_a_stg_bootstrap_stops_when_its_g4_record_disappears(self):
        TG.StgWriteTest.stg(self)
        d = self.r / "releases/B-1"
        d.mkdir(parents=True)
        self.set_env("stg", sites=dict(json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
                                       ["envs"]["stg"]["sites"], x1={"title": "X1"}, x2={"title": "X2"}))
        steps = [{"op": "createsite", "site": s, "parent_id": TH.FOLDER,
                  "payload": {"Title": s, "ReferenceType": "Results", "SiteSettings": {}}} for s in ("x1", "x2")]
        (d / "bootstrap.json").write_text(json.dumps({"release": "B-1", "env": "stg", "parent_id": TH.FOLDER,
                                                      "steps": steps, "status": "planned"}), encoding="utf-8")
        GT.record(self.r, "G4", "approved", "Nam", "G4 approved", [], ["B-1"], "2026-11-08")
        self.after_first("/createsite", lambda: [f.unlink() for f in (self.r / "gates").glob("*G4*.json")])
        code, out = self.run_quiet("bootstrap", "B-1", "--yes")
        self.assertEqual((code, len(self.creates())), (1, 1))
        self.assertIn("stopped before x2", out)

    def test_a_bootstrap_with_the_guard_unchanged_creates_every_site(self):
        self.bootstrap_plan()
        code, _ = self.run_quiet("bootstrap", "B-1", "--yes")
        self.assertEqual((code, len(self.creates())), (0, 2))

    # ---------------------------------------------------------------- migrate

    def two_migrations(self):
        self.plan("R-1")
        self.migration()
        src, dst = self.r / TM.MIG, self.r / "migrations/m2"
        shutil.copytree(src, dst)
        p = self.r / "releases/R-1/plan.json"
        plan = json.loads(p.read_text(encoding="utf-8"))
        plan["migration"] = [TM.MIG, "migrations/m2"]
        p.write_text(json.dumps(plan), encoding="utf-8")

    def upserts(self):
        return [p for p, _ in self.fake.calls if p.endswith("/bulkupsert")]

    def test_migrate_stops_before_the_next_migration_when_writes_are_turned_off(self):
        self.two_migrations()
        self.after_first("/bulkupsert", lambda: self.set_conn("dev", allow_write=False))
        code, out = self.run_quiet("migrate", "R-1", "--yes")
        self.assertEqual(code, 1)
        self.assertEqual(len(self.upserts()), 1)                                     # m2 never sent
        self.assertIn("stopped before migrations/m2", out)
        runs = json.loads((self.r / "releases/R-1/plan.json").read_text(encoding="utf-8"))["migrations_run"]
        self.assertEqual([(x["dir"], x["status"]) for x in runs], [(TM.MIG, "migrated")])   # m1 recorded, m2 not started

    def test_migrate_with_the_guard_unchanged_runs_every_migration(self):
        self.two_migrations()
        code, _ = self.run_quiet("migrate", "R-1", "--yes")
        self.assertEqual((code, len(self.upserts())), (0, 2))

    def test_a_stopped_migrate_resumes_with_only_the_rest_and_apply_then_runs(self):
        self.two_migrations()
        self.after_first("/bulkupsert", lambda: self.set_conn("dev", allow_write=False))
        self.assertEqual(self.run_quiet("migrate", "R-1", "--yes")[0], 1)
        self.set_conn("dev", allow_write=True)
        code, out = self.run_quiet("migrate", "R-1", "--yes")
        self.assertEqual(code, 0, out)
        self.assertIn(f"{TM.MIG}: already migrated by an earlier run — skipped", out)
        self.assertEqual(len(self.upserts()), 2)                                     # m2 once, m1 never twice
        runs = json.loads((self.r / "releases/R-1/plan.json").read_text(encoding="utf-8"))["migrations_run"]
        self.assertEqual([(x["dir"], x["status"]) for x in runs], [(TM.MIG, "migrated"), ("migrations/m2", "migrated")])
        code, out = self.run_quiet("migrate", "R-1", "--yes")                       # everything done: refused
        self.assertEqual(len(self.upserts()), 2)
        self.assertEqual(code, 2)
        n = len(self.fake.calls)
        self.run_quiet("apply", "R-1", "--yes")
        self.assertTrue([p for p, _ in self.fake.calls[n:] if p.endswith("/updatesite")])   # no longer pending

    def runs(self, *entries):
        p = self.r / "releases/R-1/plan.json"
        plan = json.loads(p.read_text(encoding="utf-8"))
        plan["migrations_run"] = [{"dir": d, "direction": w, "status": s, "site": "equipment", "records": 2,
                                   "finished_at": "t1"} for d, w, s in entries]
        p.write_text(json.dumps(plan), encoding="utf-8")

    def test_a_rolled_back_folder_is_never_skipped_as_done(self):
        self.two_migrations()
        self.runs((TM.MIG, "forward", "migrated"), (TM.MIG, "rollback", "migrated"), ("migrations/m2", "forward", "failed"))
        code, out = self.run_quiet("migrate", "R-1", "--yes")
        self.assertEqual((code, len(self.upserts())), (2, 0))                    # refused, nothing sent
        self.assertNotIn("next: pls apply", out)

    def test_forward_then_rollback_then_forward_is_refused_without_pointing_to_apply(self):
        self.plan("R-1")
        self.migration()
        self.runs((TM.MIG, "forward", "migrated"), (TM.MIG, "rollback", "migrated"))
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code, out = self.run_quiet("migrate", "R-1", "--yes")
        self.assertEqual((code, len(self.upserts())), (2, 0))
        self.assertNotIn("next: pls apply", out + err.getvalue())

    def test_a_failed_migration_is_sent_again_after_the_data_is_fixed_and_the_done_one_is_not(self):
        self.two_migrations()
        self.runs((TM.MIG, "forward", "migrated"), ("migrations/m2", "forward", "failed"))
        code, out = self.run_quiet("migrate", "R-1", "--yes")
        self.assertEqual((code, len(self.upserts())), (0, 1), out)
        self.assertIn(f"{TM.MIG}: already migrated by an earlier run — skipped", out)

    def test_migrate_stops_when_the_role_is_changed_to_prod(self):
        self.two_migrations()
        self.after_first("/bulkupsert", lambda: self.set_env("dev", role="prod"))
        code, _ = self.run_quiet("migrate", "R-1", "--yes")
        self.assertEqual((code, len(self.upserts())), (1, 1))

    def stg_two_migrations(self):
        TG.StgWriteTest.stg(self)
        p = self.r / "releases/R-20261108-01/plan.json"
        self.migration(release="R-20261108-01")
        shutil.copytree(self.r / TM.MIG, self.r / "migrations/m2")
        plan = json.loads(p.read_text(encoding="utf-8"))
        plan["migration"] = [TM.MIG, "migrations/m2"]
        p.write_text(json.dumps(plan), encoding="utf-8")
        GT.record(self.r, "G4", "approved", "Nam", "G4 approved", [], ["R-20261108-01"], "2026-11-08")

    def test_a_stg_migrate_runs_every_migration_under_its_g4(self):
        self.stg_two_migrations()
        code, out = self.run_quiet("migrate", "R-20261108-01", "--yes")
        self.assertEqual((code, len(self.upserts())), (0, 2), out)               # recording runs keeps G4 valid

    def test_a_stg_migrate_stops_when_its_g4_record_disappears(self):
        self.stg_two_migrations()
        self.after_first("/bulkupsert", lambda: [f.unlink() for f in (self.r / "gates").glob("*G4*.json")])
        code, out = self.run_quiet("migrate", "R-20261108-01", "--yes")
        self.assertEqual((code, len(self.upserts())), (1, 1))
        self.assertIn("stopped before migrations/m2", out)

    def test_a_stg_bootstrap_with_its_g4_creates_every_site(self):
        TG.StgWriteTest.stg(self)
        d = self.r / "releases/B-1"
        d.mkdir(parents=True)
        self.set_env("stg", sites=dict(json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
                                       ["envs"]["stg"]["sites"], x1={"title": "X1"}, x2={"title": "X2"}))
        steps = [{"op": "createsite", "site": s, "parent_id": TH.FOLDER,
                  "payload": {"Title": s, "ReferenceType": "Results", "SiteSettings": {}}} for s in ("x1", "x2")]
        (d / "bootstrap.json").write_text(json.dumps({"release": "B-1", "env": "stg", "parent_id": TH.FOLDER,
                                                      "steps": steps, "status": "planned"}), encoding="utf-8")
        GT.record(self.r, "G4", "approved", "Nam", "G4 approved", [], ["B-1"], "2026-11-08")
        code, out = self.run_quiet("bootstrap", "B-1", "--yes")
        self.assertEqual((code, len(self.creates())), (0, 2), out)


if __name__ == "__main__":
    unittest.main()
