"""`pls migrate`: the data migration of a data-impacting release goes through the guarded HTTP transport (ADR-0004,
ADR-0014 TB-7) — write guard, G4 bound to the migration folder on non-dev, mail / job checks, typed confirmation,
a record before the call, no re-run of a migrated or uncertain folder, and apply only after the migration.
Fake Pleasanter on 127.0.0.1 only."""
import json
import re
import unittest

import pls
import pls_gate as GT
import pls_http as H
import test_gate as TG
import test_http as TH

MIG = "migrations/m1"


class MigrateTest(unittest.TestCase):
    setUp = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown
    plan = TH.HttpTest.plan
    stg = TG.StgWriteTest.stg

    def bulk(self, n=0):
        return [p for p, _ in self.fake.calls[n:] if p.endswith("/bulkupsert")]

    def writes(self, n=0):
        return [p for p, _ in self.fake.calls[n:] if re.search(r"/(updatesite|createsite|bulkupsert|create|update|delete)$", p)]

    def migration(self, release="R-1", **m):
        doc = {"site": "equipment", "keys": ["ClassA"],
               "data": [{"ClassA": "E-1", "ClassB": "new"}, {"ClassA": "E-2", "ClassB": "new"}],
               "rollback": {"data": [{"ClassA": "E-1", "ClassB": "old"}]}}
        doc.update(m)
        d = self.r / MIG
        (d / "backup").mkdir(parents=True, exist_ok=True)
        (d / "backup/records.json").write_text(json.dumps({"records": []}), encoding="utf-8")
        (d / "dry-run.md").write_text("dry run on a copy: 2 updated\n", encoding="utf-8")
        (d / "migration.json").write_text(json.dumps(doc), encoding="utf-8")
        p = self.r / "releases" / release / "plan.json"
        plan = json.loads(p.read_text(encoding="utf-8"))
        plan.update(classification="data-impacting", migration=[MIG])
        for s in plan["sites"]:
            plan["per_site"][s]["payload_file"] = f"payload-{s}.json"
        p.write_text(json.dumps(plan), encoding="utf-8")
        self.fake.records[1] = {"site": TH.EQ, "ResultId": 1, "ClassA": "E-1", "ClassB": "old"}

    def plan_json(self, release="R-1"):
        return json.loads((self.r / "releases" / release / "plan.json").read_text(encoding="utf-8"))

    def test_migrate_then_apply_on_dev(self):
        self.plan()
        self.migration()
        n = len(self.fake.calls)
        self.assertEqual(pls.main(["apply", "R-1", "--yes"]), 2)                 # ADR-0004 order: data first
        self.assertEqual(self.writes(n), [])
        self.assertEqual(pls.main(["migrate", "R-1", "--yes"]), 0)
        self.assertEqual(len(self.bulk(n)), 1)                                     # one call, never retried
        self.assertEqual(self.fake.records[1]["ClassB"], "new")
        run = self.plan_json()["migrations_run"]
        self.assertEqual([(x["dir"], x["direction"], x["status"], x["records"]) for x in run], [(MIG, "forward", "migrated", 2)])
        n = len(self.fake.calls)
        self.assertEqual(pls.main(["migrate", "R-1", "--yes"]), 2)               # never sent twice
        self.assertEqual(self.bulk(n), [])
        pls.main(["apply", "R-1", "--yes"])
        self.assertTrue([p for p in self.writes(n) if p.endswith("/updatesite")])

    def test_rollback_sends_only_the_data_a_person_prepared(self):
        self.plan()
        self.migration()
        self.assertEqual(pls.main(["migrate", "R-1", "--rollback", "--yes"]), 2)   # nothing migrated yet
        pls.main(["migrate", "R-1", "--yes"])
        self.assertEqual(pls.main(["migrate", "R-1", "--rollback", "--yes"]), 0)
        self.assertEqual(self.fake.records[1]["ClassB"], "old")
        self.assertEqual([x["direction"] for x in self.plan_json()["migrations_run"]], ["forward", "rollback"])

    def test_data_pls_would_have_to_guess_is_refused_before_any_call(self):
        cases = {"mapping only": {"data": None, "mapping": {"ClassB": {"old": "new"}}},
                 "duplicate key": {"data": [{"ClassA": "E-1"}, {"ClassA": "E-1"}]},
                 "record without key": {"data": [{"ClassB": "x"}]},
                 "no keys": {"keys": []},
                 "shared or unknown site": {"site": "nowhere"}}
        self.plan()
        for label, m in cases.items():
            with self.subTest(label):
                self.migration(**m)
                n = len(self.fake.calls)
                self.assertEqual(pls.main(["migrate", "R-1", "--yes"]), 2)
                self.assertEqual(self.writes(n), [])
        self.migration(rollback="restore from backup")                            # not explicit data
        pls.main(["migrate", "R-1", "--yes"])
        self.assertEqual(pls.main(["migrate", "R-1", "--rollback", "--yes"]), 2)

    def test_guards_allow_write_prod_and_missing_migration_files(self):
        self.plan()
        self.migration()
        (self.r / MIG / "dry-run.md").unlink()
        self.assertEqual(pls.main(["migrate", "R-1", "--yes"]), 2)               # ADR-0004 folder incomplete
        (self.r / MIG / "dry-run.md").write_text("ok\n", encoding="utf-8")
        c = json.loads((self.r / ".pls/connections.json").read_text(encoding="utf-8"))
        c["dev"]["allow_write"] = False
        (self.r / ".pls/connections.json").write_text(json.dumps(c), encoding="utf-8")
        self.assertEqual(pls.main(["migrate", "R-1", "--yes"]), 2)
        p = self.r / "releases/R-1/plan.json"
        p.write_text(json.dumps(dict(self.plan_json(), env="prod")), encoding="utf-8")
        self.assertEqual(pls.main(["migrate", "R-1", "--yes"]), 2)
        self.assertEqual(self.bulk(), [])

    def test_mail_unknown_on_a_mailing_site_is_refused(self):
        self.plan()
        self.migration()
        self.fake.sites[TH.EQ]["SiteSettings"]["Notifications"] = [{"Id": 1, "Type": 1, "Address": "x@example.com"}]
        n = len(self.fake.calls)
        self.assertEqual(pls.main(["migrate", "R-1", "--yes"]), 2)               # side_effects.mail is unknown
        self.assertEqual(self.bulk(n), [])

    def test_stg_needs_g4_and_the_g4_covers_the_migration_folder(self):
        self.stg()
        R = "R-20261108-01"
        self.migration(R)
        n = len(self.fake.calls)
        self.assertEqual(pls.main(["migrate", R, "--yes"]), 2)                   # no G4
        GT.record(self.r, "G4", "approved", "Nam", "G4 approved with the migration", [], [R], "2026-11-08")
        m = json.loads((self.r / MIG / "migration.json").read_text(encoding="utf-8"))
        m["data"][0]["ClassB"] = "changed after G4"
        (self.r / MIG / "migration.json").write_text(json.dumps(m), encoding="utf-8")
        self.assertEqual(pls.main(["migrate", R, "--yes"]), 2)                   # content differs from what G4 approved
        self.assertEqual(self.bulk(n), [])
        GT.record(self.r, "G4", "approved", "Nam", "G4 approved again after seeing the new data", [], [R], "2026-11-08")
        self.assertEqual(pls.main(["migrate", R, "--yes"]), 0)
        self.assertEqual(len(self.bulk(n)), 1)


class OutcomeTest(unittest.TestCase):
    """How one bulkupsert answer becomes a status (no server needed)."""
    class Stub:
        def __init__(self, result):
            self.result = result

        def bulk_upsert(self, site_id, keys, data):
            if isinstance(self.result, Exception):
                raise self.result
            return self.result

    def test_statuses(self):
        for result, status in (((200, "2 件更新しました。"), "migrated"), ((400, "複数存在します"), "failed"),
                               ((500, "boom"), "uncertain"), (H.UncertainOutcome("timed out"), "uncertain"),
                               (H.TransportError("cannot reach"), "failed")):
            with self.subTest(status=status, result=str(result)):
                self.assertEqual(H.migrate(self.Stub(result), 1, ["ClassA"], [{"ClassA": "x"}])["status"], status)

    def test_an_uncertain_run_blocks_a_re_run(self):
        import pls_migrate as MI
        plan = {"status": "planned", "migration": [MIG], "migrations_run": [{"dir": MIG, "direction": "forward", "status": "uncertain"}]}
        self.assertIn("compares them with backup", MI.state_problem(plan, MIG, False))
        self.assertEqual(MI.pending(plan), [MIG])


if __name__ == "__main__":
    unittest.main()
