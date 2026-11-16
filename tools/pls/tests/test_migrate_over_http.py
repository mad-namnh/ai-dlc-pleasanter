"""`pls migrate`: the data migration of a data-impacting release goes through the guarded HTTP transport (ADR-0004,
ADR-0014 TB-7) — write guard, G4 bound to the migration folder on non-dev, mail / job checks, typed confirmation,
a record before the call, no re-run of a migrated or uncertain folder, and apply only after the migration.
Fake Pleasanter on 127.0.0.1 only."""
import contextlib
import io
import json
import re
import unittest
from unittest import mock

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

    def test_nothing_to_convert_on_an_empty_site_sends_nothing_and_lets_apply_run(self):
        # a data-impacting setting change (e.g. a renamed status) on a site that holds no record yet
        self.plan()
        self.migration(nothing_to_convert=True, data=[])
        self.assertEqual(pls.migration_problems(self.r, [MIG]), [])
        self.fake.records.clear()                                                  # the site is empty
        n = len(self.fake.calls)
        self.assertEqual(pls.main(["migrate", "R-1", "--yes"]), 0)
        self.assertEqual(self.writes(n), [])                                       # read only
        self.assertEqual(pls.main(["migrate", "R-1", "--rollback", "--yes"]), 2)   # nothing sent → nothing to roll back
        run = self.plan_json()["migrations_run"]
        self.assertEqual([(x["status"], x["records"]) for x in run], [("migrated", 0)])
        self.assertEqual((run[0]["nothing_to_convert"], run[0]["records_read"]), (True, 0))   # apply re-reads from this
        pls.main(["apply", "R-1", "--yes"])
        self.assertTrue([p for p in self.writes(n) if p.endswith("/updatesite")])

    def test_apply_refuses_when_a_record_appeared_after_a_nothing_to_convert_migration(self):
        # the emptiness read by migrate can go stale before apply: apply reads the site again and writes nothing
        self.plan()
        self.migration(nothing_to_convert=True, data=[])
        self.fake.records.clear()
        self.assertEqual(pls.main(["migrate", "R-1", "--yes"]), 0)
        self.fake.records[2] = {"site": TH.EQ, "ResultId": 2, "ClassA": "E-2", "ClassB": "new"}   # created in between
        n = len(self.fake.calls)
        self.assertEqual(pls.main(["apply", "R-1", "--yes"]), 2)
        self.assertEqual(self.writes(n), [])
        self.assertEqual(self.plan_json()["status"], "planned")

    def ntc_migrated(self):
        self.plan()
        self.migration(nothing_to_convert=True, data=[])
        self.fake.records.clear()
        self.assertEqual(pls.main(["migrate", "R-1", "--yes"]), 0)

    def test_apply_refuses_when_the_checked_site_is_not_in_the_release(self):
        self.ntc_migrated()
        p = self.r / "releases/R-1/plan.json"
        plan = self.plan_json()
        plan["migrations_run"][-1]["site"] = "elsewhere"
        p.write_text(json.dumps(plan), encoding="utf-8")
        n = len(self.fake.calls)
        self.assertEqual(pls.main(["apply", "R-1", "--yes"]), 2)
        self.assertEqual(self.writes(n), [])

    def test_apply_refuses_when_the_re_check_cannot_read_the_site(self):
        self.ntc_migrated()
        n = len(self.fake.calls)
        with mock.patch.object(H.Client, "backup_records", side_effect=H.TransportError("HTTP 500")):
            self.assertEqual(pls.main(["apply", "R-1", "--yes"]), 2)
        self.assertEqual(self.writes(n), [])
        self.assertEqual(self.plan_json()["status"], "planned")

    def test_a_failed_or_unfinished_emptiness_read_may_run_again(self):
        self.plan()
        self.migration(nothing_to_convert=True, data=[])
        self.fake.records.clear()
        with mock.patch.object(H.Client, "backup_records", side_effect=H.TransportError("HTTP 500")):
            self.assertEqual(pls.main(["migrate", "R-1", "--yes"]), 1)
        self.assertEqual(self.plan_json()["migrations_run"][-1]["status"], "failed")
        p = self.r / "releases/R-1/plan.json"                                     # a crash after the record, before the read
        plan = self.plan_json()
        plan["migrations_run"][-1].update(status="migrating")
        p.write_text(json.dumps(plan), encoding="utf-8")
        self.assertEqual(pls.main(["migrate", "R-1", "--yes"]), 0)                 # nothing was sent: no dead end
        self.assertEqual(self.plan_json()["migrations_run"][-1]["status"], "migrated")

    def two_folders(self, bom=False):
        self.plan()
        self.migration()                                                           # m1 sends data to equipment
        d2 = self.r / "migrations/m2"
        (d2 / "backup").mkdir(parents=True)
        (d2 / "backup/records.json").write_text(json.dumps({"records": []}), encoding="utf-8")
        (d2 / "dry-run.md").write_text("loans holds no record: nothing to convert\n", encoding="utf-8")
        (d2 / "migration.json").write_text(("\ufeff" if bom else "") + json.dumps({"site": "loans", "nothing_to_convert": True,
                                                                                    "data": []}), encoding="utf-8")
        p = self.r / "releases/R-1/plan.json"
        plan = self.plan_json()
        plan["migration"] = [MIG, "migrations/m2"]
        p.write_text(json.dumps(plan), encoding="utf-8")
        self.assertEqual(pls.main(["migrate", "R-1", "--yes"]), 0)

    def test_rollback_skips_a_nothing_to_convert_folder_and_rolls_back_the_others(self):
        for bom in (False, True):
            with self.subTest(bom=bom):
                self.tearDown()
                self.setUp()
                self.two_folders(bom)
                n = len(self.fake.calls)
                self.assertEqual(pls.main(["migrate", "R-1", "--rollback", "--yes"]), 0)
                self.assertEqual(len(self.bulk(n)), 1)                            # m1's rollback data only
                self.assertEqual([(x["dir"], x["direction"]) for x in self.plan_json()["migrations_run"]][-1], (MIG, "rollback"))

    def test_rollback_follows_what_the_forward_run_did_not_the_folder_today(self):
        self.two_folders()
        (self.r / MIG / "migration.json").write_text(json.dumps({"site": "equipment", "nothing_to_convert": True, "data": []}),
                                                     encoding="utf-8")            # m1 sent data, then was edited
        n = len(self.fake.calls)
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(pls.main(["migrate", "R-1", "--rollback", "--yes"]), 2)  # never skipped silently
        self.assertIn(f"{MIG}: a nothing-to-convert migration sent no data", err.getvalue())
        self.assertEqual(self.bulk(n), [])

    def test_loading_a_nothing_to_convert_folder_for_rollback_is_refused(self):
        # migrate --rollback skips such folders before loading them; load itself still refuses (defence in depth)
        import pls_migrate as MI
        self.plan()
        self.migration(nothing_to_convert=True, data=[])
        with self.assertRaisesRegex(MI.MigrateError, "nothing to roll back"):
            MI.load(self.r, MIG, True)

    def test_a_nothing_to_convert_folder_still_needs_its_backup_and_dry_run(self):
        self.plan()
        self.migration(nothing_to_convert=True, data=[])
        (self.r / MIG / "migration.json").write_text(json.dumps({"site": "equipment", "nothing_to_convert": True, "data": []}),
                                                     encoding="utf-8")                    # no keys, no rollback
        self.assertEqual(pls.migration_problems(self.r, [MIG]), [])
        (self.r / MIG / "dry-run.md").unlink()
        self.assertEqual(pls.migration_problems(self.r, [MIG]), [f"{MIG}/dry-run.md is missing"])

    def test_nothing_to_convert_is_refused_when_the_site_holds_records(self):
        self.plan()
        self.migration(nothing_to_convert=True, data=[])                          # the fake site holds one record
        n = len(self.fake.calls)
        self.assertEqual(pls.main(["migrate", "R-1", "--yes"]), 1)
        self.assertEqual(self.writes(n), [])
        self.assertEqual(self.plan_json()["migrations_run"][-1]["status"], "failed")
        self.assertEqual(pls.main(["apply", "R-1", "--yes"]), 2)                  # ADR-0004 order still holds
        self.assertEqual(self.writes(n), [])

    def test_empty_data_without_the_explicit_flag_is_still_refused(self):
        self.plan()
        self.migration(data=[])
        n = len(self.fake.calls)
        self.assertEqual(pls.main(["migrate", "R-1", "--yes"]), 2)
        self.assertEqual(self.writes(n), [])


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
