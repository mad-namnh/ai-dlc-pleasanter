"""Refusals that had no test of their own (design review H1): each refuses, says why, and leaves nothing behind.

Planning: a payload that misses live keys (L-DEP-01), a missing slot ledger, drift from the last release and a
data-impacting change without a migration write no release folder. `mark-applied` and `jobs-verified` change no
record when they refuse. A payload without Title / ReferenceType / SiteSettings is never sent. A production
environment is never written by bootstrap, test, kb-verify or harvest.

The guards exist already, so these tests pass on the commit that adds them; each was shown to fail with its guard
switched off (see the plan folder of roadmap item P2-3).

    python -m unittest discover -s tools/pls/tests -v
"""
import contextlib
import io
import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pls  # noqa: E402
import pls_http as H  # noqa: E402
import pls_side_effects as SE  # noqa: E402
import test_http as TH  # noqa: E402
import test_pls as TP  # noqa: E402


def run(argv):
    """Run a pls command: (exit code, or the refusal as text; everything it printed)."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        try:
            rc = pls.main(argv)
        except (pls.Fail, H.TransportError) as ex:
            rc = f"{type(ex).__name__}: {ex}"
    return rc, out.getvalue()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


class PlanningRefusalsWriteNoRelease(unittest.TestCase):
    setUp, tearDown = TP.PlsTest.setUp, TP.PlsTest.tearDown
    unpack_dev, _two_sites = TP.PlsTest.unpack_dev, TP.PlsTest._two_sites

    def release_plan(self, sa, sb, release="R1"):
        return run(["release-plan", "--env", "stg", "--release", release, "--export", f"a={sa}", "--export", f"b={sb}"])

    def change_live_a(self, export_file, change):
        doc = read(export_file)
        change(doc["Response"]["Data"]["SiteSettings"])
        export_file.write_text(json.dumps(doc), encoding="utf-8")

    def assert_refused_and_nothing_written(self, result, why, release="R1"):
        rc, out = result
        self.assertEqual(rc, 1, out)
        self.assertIn(why, out)
        self.assertIn("release plan REFUSED", out)
        self.assertFalse((self.r / "releases" / release).exists(), "a refused plan left a release folder")

    def test_the_fixture_plans_when_nothing_is_wrong(self):                 # the refusals below are not the fixture's
        sa, sb = self._two_sites()
        rc, out = self.release_plan(sa, sb)
        self.assertEqual(rc, 0, out)
        self.assertTrue((self.r / "releases/R1/plan.json").exists())

    def test_payload_that_misses_a_live_key_is_refused(self):               # L-DEP-01 (I2: complete payload)
        sa, sb = self._two_sites()
        self.change_live_a(sa, lambda ss: ss.update(GridColumns=["ClassA"]))    # set in the UI, not in git
        self.assert_refused_and_nothing_written(self.release_plan(sa, sb), "a: REFUSED — L-DEP-01 payload misses ['GridColumns']")

    def test_missing_slot_ledger_is_refused_for_every_site(self):
        sa, sb = self._two_sites()
        (self.r / "design/slot-ledger.json").unlink()
        result = self.release_plan(sa, sb)
        self.assert_refused_and_nothing_written(result, "a: REFUSED — design/slot-ledger.json is missing (A2)")
        self.assertIn("b: REFUSED — design/slot-ledger.json is missing (A2)", result[1])

    def test_data_impacting_change_without_a_migration_is_refused(self):    # ADR-0004
        sa, sb = self._two_sites()
        self.change_live_a(sa, lambda ss: [c for c in ss["Columns"] if c["ColumnName"] == "ClassA"][0].update(ChoicesText="X\nY"))
        self.assert_refused_and_nothing_written(self.release_plan(sa, sb), "data-impacting change needs a migration (ADR-0004)")

    def applied_release(self):
        """R1 planned and marked as applied from exports that hold its payloads; returns the export files."""
        sa, sb = self._two_sites()
        self.assertEqual(self.release_plan(sa, sb)[0], 0)
        lives = {}
        for site, sid in (("a", 201), ("b", 202)):
            lives[site] = self.r / f"live-{site}.json"
            lives[site].write_text(json.dumps({"Response": {"Data": dict(read(self.r / f"releases/R1/payload-{site}.json"), SiteId=sid)}}),
                                   encoding="utf-8")
        self.exports = ["--export", f"a={lives['a']}", "--export", f"b={lives['b']}"]
        self.assertEqual(run(["mark-applied", "R1", *self.exports])[0], 0)
        return lives

    def test_drift_from_the_last_release_is_refused(self):                  # I2, D11
        lives = self.applied_release()
        self.change_live_a(lives["a"], lambda ss: ss["Columns"].append({"ColumnName": "ClassZ", "LabelText": "added in the UI"}))
        self.assertEqual(run(["gate", "G3", "--approver", "Nam", "--release", "R2", "--quote", "G3 approved"])[0], 0)
        result = self.release_plan(lives["a"], lives["b"], "R2")
        self.assert_refused_and_nothing_written(result, "a: REFUSED — the environment drifted from its last release (I2, D11)", "R2")
        self.assertIn("settings.Columns[ClassZ]", result[1])

    def test_mark_applied_refuses_an_applied_release_and_an_unknown_status(self):
        self.applied_release()
        plan_file = self.r / "releases/R1/plan.json"
        before = plan_file.read_bytes()
        rc, out = run(["mark-applied", "R1", *self.exports])
        self.assertEqual(rc, 1)
        self.assertIn("NOT marked again: R1 is already recorded as applied", out)
        self.assertEqual(plan_file.read_bytes(), before)                     # applied_at is not stamped again
        plan = read(plan_file)
        plan["status"] = "superseded"                                        # not a status pls writes
        plan_file.write_text(json.dumps(plan), encoding="utf-8")
        rc, out = run(["mark-applied", "R1", *self.exports])
        self.assertEqual(rc, 1)
        self.assertIn("NOT marked: R1 has status 'superseded'", out)
        self.assertEqual(read(plan_file), plan)

    def test_jobs_verified_refuses_without_a_plan_without_job_changes_and_without_the_persons_words(self):
        rc, _ = run(["jobs-verified", "R9", "--by", "Nam", "--quote", "copied and checked"])
        self.assertEqual(rc, "Fail: releases/R9/plan.json not found")
        self.assertFalse((self.r / "releases/R9").exists())
        self.applied_release()                                               # R1 changes no scheduled script
        plan_file = self.r / "releases/R1/plan.json"
        before = plan_file.read_bytes()
        rc, _ = run(["jobs-verified", "R1", "--by", "Nam", "--quote", "copied and checked"])
        self.assertEqual(rc, "Fail: R1 records no scheduled-script changes — nothing to verify")
        self.assertEqual(plan_file.read_bytes(), before)

    def test_jobs_verified_needs_the_persons_own_words(self):               # I4
        sa, sb = self._two_sites()
        jobs = self.r / SE.JOBS_DIR
        jobs.mkdir(parents=True)
        (jobs / "nightly.js").write_text("const id = ${site:b};", encoding="utf-8")
        (jobs / SE.JOBS_INDEX).write_text(json.dumps([{"name": "nightly", "schedule": "毎日", "enabled": True}]), encoding="utf-8")
        self.assertEqual(self.release_plan(sa, sb)[0], 0)
        plan_file = self.r / "releases/R1/plan.json"
        plan = read(plan_file)
        self.assertTrue(plan["jobs"]["changed"])
        plan.update(status="applied", applied_at="2026-11-09T10:00:00+09:00")       # as mark-applied records it
        plan_file.write_text(json.dumps(plan), encoding="utf-8")
        rc, _ = run(["jobs-verified", "R1", "--by", "Nam", "--quote", "   "])
        self.assertEqual(rc, "Fail: --quote: the person's own words are required (I4)")
        self.assertNotIn("verified", read(plan_file)["jobs"])
        self.assertEqual(run(["jobs-verified", "R1", "--by", "Nam", "--quote", "copied and checked"])[0], 0)
        self.assertEqual(read(plan_file)["jobs"]["verified"]["quote"], "copied and checked")


class SingleSitePlanRefusals(unittest.TestCase):
    setUp, tearDown = TP.PlsTest.setUp, TP.PlsTest.tearDown
    unpack_dev, _ledger, _stg_live = TP.PlsTest.unpack_dev, TP.PlsTest._ledger, TP.PlsTest._stg_live
    _stg_export_from_payload = TP.PlsTest._stg_export_from_payload

    def test_mark_applied_refuses_the_export_of_another_site_and_a_second_marking(self):
        self.unpack_dev()
        self._ledger({"ClassA": "No", "ClassB": ""})
        self.assertEqual(run(["plan", str(self._stg_live()), "--env", "stg", "--site", "a", "--release", "R1"])[0], 0)
        plan_file = self.r / "releases/R1/plan.json"
        live = self._stg_export_from_payload("R1")
        other = json.loads(json.dumps(live))
        other["Response"]["Data"]["SiteId"] = 999                             # same content, another site
        (self.r / "other.json").write_text(json.dumps(other), encoding="utf-8")
        (self.r / "live.json").write_text(json.dumps(live), encoding="utf-8")
        rc, out = run(["mark-applied", "R1", str(self.r / "other.json")])
        self.assertEqual(rc, 1)
        self.assertIn("NOT marked: the export is site 999, the release is for site 201", out)
        self.assertEqual(read(plan_file)["status"], "planned")
        self.assertEqual(run(["mark-applied", "R1", str(self.r / "live.json")])[0], 0)
        before = plan_file.read_bytes()
        rc, out = run(["mark-applied", "R1", str(self.r / "live.json")])
        self.assertEqual(rc, 1)
        self.assertIn("NOT marked again: R1 is already recorded as applied", out)
        self.assertEqual(plan_file.read_bytes(), before)


class NothingIsSentWhenTheWriteIsRefused(unittest.TestCase):
    setUp, tearDown, plan = TH.HttpTest.setUp, TH.HttpTest.tearDown, TH.HttpTest.plan

    def writes(self, since=0):
        return [p for p, _ in self.fake.calls[since:] if re.search(r"/(updatesite|createsite|bulkupsert|create|update|delete)$", p)]

    def test_a_payload_without_title_type_or_settings_is_never_sent(self):   # I2: transport key-presence check
        client = H.Client(self.url, "K-ADMIN")
        whole = {"Title": "t", "ReferenceType": "Results", "SiteSettings": {}}
        for key in whole:
            with self.assertRaises(H.TransportError) as refused:
                client.apply(TH.EQ, {k: v for k, v in whole.items() if k != key})
            self.assertEqual(str(refused.exception), f"payload missing {key} (I2)")
        self.assertEqual(self.writes(), [])
        self.assertEqual(self.fake.sites[TH.EQ]["Title"], "eq")
        self.assertEqual(client.apply(TH.EQ, whole)[0], 200)                 # the complete payload is sent
        self.assertEqual(self.writes(), [f"/api/items/{TH.EQ}/updatesite"])

    def test_production_is_never_written_by_bootstrap_test_kb_verify_or_harvest(self):
        envs = read(self.r / "environments.json")
        envs["envs"]["prod"].update(parent_id=TH.FOLDER, values={"kb_probe_parent": 950})
        envs["envs"]["prod"]["sites"]["x1"] = {"title": "X1"}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        self.fake.sites[950] = {"SiteId": 950, "Title": "probes", "ReferenceType": "Sites", "UpdatedTime": "t0", "SiteSettings": {}}
        b = self.r / "releases/B-1"
        b.mkdir(parents=True)
        (b / "bootstrap.json").write_text(json.dumps({
            "release": "B-1", "env": "prod", "parent_id": TH.FOLDER, "status": "planned",
            "steps": [{"op": "createsite", "site": "x1", "parent_id": TH.FOLDER,
                       "payload": {"Title": "X1", "ReferenceType": "Results", "SiteSettings": {}}}]}), encoding="utf-8")
        (self.r / "s.json").write_text(json.dumps(
            [{"id": "T", "steps": [{"op": "create", "site": "${site:equipment}", "save": "e", "data": {}}]}]), encoding="utf-8")
        sites_before = json.dumps(self.fake.sites, sort_keys=True)
        not_prod = "REFUSED: writing to 'prod' needs environments.json role dev/stg (is 'prod')"
        for argv, why in ((["bootstrap", "B-1", "--yes"], not_prod),
                          (["test", "s.json", "--env", "prod", "--site", "equipment", "--out", "x.json", "--yes"], not_prod),
                          (["kb-verify", "--env", "prod", "--yes"], "only on a dev environment"),
                          (["harvest", "--env", "prod", "--site", "equipment"], "prod changes come through drift (P6)")):
            rc, out = run(argv)
            self.assertNotEqual(rc, 0, f"{argv}: {out}")
            self.assertIn(why, f"{rc} {out}", argv)                           # refused for being prod, not for a typo
        self.assertEqual(self.writes(), [])
        self.assertEqual(json.dumps(self.fake.sites, sort_keys=True), sites_before)
        self.assertEqual(self.fake.records, {})
        self.assertNotIn("id", read(self.r / "environments.json")["envs"]["prod"]["sites"]["x1"])   # nothing bound
        self.assertFalse((self.r / "config").exists())                        # harvest wrote no configuration


if __name__ == "__main__":
    unittest.main()
