"""Unit tests for pls (stdlib only):  python -m unittest discover -s tools/pls/tests -v"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pls  # noqa: E402

ENVS = {"managed_sites": ["a"], "envs": {
    "dev": {"role": "dev", "sites": {"a": {"id": 101, "title": "dev_A"}, "b": {"id": 102, "title": "dev_B"}},
            "values": {"URL": "http://dev.internal"}},
    "stg": {"role": "stg", "sites": {"a": {"id": 201, "title": "stg_A"}, "b": {"id": 202, "title": "stg_B"}},
            "values": {"URL": "http://stg.internal"}}}}


def export(site_id, b_id, url, extra_cols=(), scripts=None):
    cols = [{"ColumnName": "ClassA", "LabelText": "No"}, {"ColumnName": "ClassB", "ChoicesText": f"[[{b_id}]]"}] + list(extra_cols)
    ss = {"Version": 1.017, "Columns": cols, "Links": [{"SiteId": b_id, "ColumnName": "ClassB"}],
          "ServerScripts": scripts if scripts is not None else
          [{"Id": 1, "Name": "env", "Shared": True, "Body": f"var U = '{url}';"},
           {"Id": 2, "Name": "s1", "BeforeCreate": True, "Body": f"items.Get({b_id}, '{{}}');"}]}
    return {"StatusCode": 200, "Response": {"Data": {"SiteId": site_id, "Title": "x", "ReferenceType": "Results",
                                                      "Body": "", "UpdatedTime": "t", "SiteSettings": ss}}}


class PlsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.r = Path(self.tmp.name)
        (self.r / "environments.json").write_text(json.dumps(ENVS), encoding="utf-8")
        self.cwd = os.getcwd()
        os.chdir(self.r)

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def unpack_dev(self, **kw):
        exp = self.r / "dev.json"
        exp.write_text(json.dumps(export(101, 102, "http://dev.internal", **kw)), encoding="utf-8")
        self.assertEqual(pls.main(["unpack", str(exp), "--env", "dev", "--site", "a"]), 0)
        return exp

    def test_unpack_uses_references_and_pack_resolves_per_env(self):
        self.unpack_dev()
        site = json.loads((self.r / "config/a/site.json").read_text(encoding="utf-8"))
        self.assertEqual(site["Links"][0]["SiteId"], "${site:b}")
        self.assertEqual(site["Columns"][1]["ChoicesText"], "[[${site:b}]]")
        self.assertIn("${env:URL}", (self.r / "config/a/server-scripts/env.js").read_text(encoding="utf-8"))
        p = pls.payload(pls.read_tree(self.r / "config/a"), ENVS["envs"]["stg"], "a")
        self.assertEqual(p["Title"], "stg_A")
        self.assertEqual(p["SiteSettings"]["Links"][0]["SiteId"], 202)
        self.assertEqual(p["SiteSettings"]["Columns"][1]["ChoicesText"], "[[202]]")
        self.assertIn("items.Get(202", p["SiteSettings"]["ServerScripts"][1]["Body"])
        self.assertIn("http://stg.internal", p["SiteSettings"]["ServerScripts"][0]["Body"])

    def test_pack_dev_reproduces_export(self):
        exp = self.unpack_dev()
        p = pls.payload(pls.read_tree(self.r / "config/a"), ENVS["envs"]["dev"], "a")
        self.assertEqual(p["SiteSettings"], json.loads(exp.read_text())["Response"]["Data"]["SiteSettings"])

    def test_drift_detects_ui_change(self):
        self.unpack_dev()
        changed = export(201, 202, "http://stg.internal",
                         extra_cols=[{"ColumnName": "ClassZ", "LabelText": "added in UI"}])
        (self.r / "stg.json").write_text(json.dumps(changed), encoding="utf-8")
        self.assertEqual(pls.main(["drift", str(self.r / "stg.json"), "--env", "stg", "--site", "a"]), 1)

    def test_no_drift_across_envs_when_equal(self):
        self.unpack_dev()
        (self.r / "stg.json").write_text(json.dumps(export(201, 202, "http://stg.internal")), encoding="utf-8")
        self.assertEqual(pls.main(["drift", str(self.r / "stg.json"), "--env", "stg", "--site", "a"]), 0)

    def test_lint_rules(self):
        scripts = [{"Id": 1, "Name": "env", "Shared": True, "Body": "const U = 'x';"},
                   {"Id": 2, "Name": "s1", "Body": "var k = 'sk-ant-abcdefghijklmnop'; items.Get(202, '{}');"}]
        self.unpack_dev(scripts=scripts)
        rules = sorted({i["rule"] for i in pls.lint(self.r)})
        # 202 is a stg id → not converted by dev unpack → hard-coded reference
        self.assertEqual(rules, ["L-LAD-01", "L-REF-01", "L-SCR-01", "L-SEC-01"])

    def test_slot_ledger(self):
        self.unpack_dev()
        (self.r / "design").mkdir()
        (self.r / "design/slot-ledger.json").write_text(json.dumps({"a": {"ClassA": {"status": "allocated"}}}), encoding="utf-8")
        msgs = [i["msg"] for i in pls.lint(self.r) if i["rule"] == "L-SLOT-01"]
        self.assertTrue(any("ClassB" in m for m in msgs))

    def test_canon_and_lint(self):
        self.unpack_dev()
        p = self.r / "config/a/site.json"
        site = json.loads(p.read_text(encoding="utf-8"))
        site["Processes"] = [{"Id": 1, "Name": "x", "ScreenType": 20, "View": {"ColumnFilterHash": {}},
                              "DataChanges": [{"Id": 1, "Type": "InputValue", "ColumnName": "ClassA", "Value": "v"}],
                              "Notifications": [{"Id": 1, "Type": 1, "Address": "[Manager]"}]}]
        p.write_text(json.dumps(site), encoding="utf-8")
        self.assertIn("L-CAN-01", {i["rule"] for i in pls.lint(self.r)})
        self.assertEqual(pls.main(["canon", "--site", "a"]), 0)
        self.assertNotIn("L-CAN-01", {i["rule"] for i in pls.lint(self.r)})
        proc = json.loads(p.read_text(encoding="utf-8"))["Processes"][0]
        self.assertNotIn("ScreenType", proc)
        self.assertEqual(proc["View"]["ApiDataType"], 0)
        self.assertEqual(proc["Notifications"][0]["MediaType"], "application/json")
        self.assertFalse(proc["DataChanges"][0]["ValueFormulaIsDisplayError"])

    def _stg_export_from_payload(self, rel, mutate=None):
        pl = json.loads((self.r / "releases" / rel / "payload.json").read_text(encoding="utf-8"))
        if mutate:
            mutate(pl["SiteSettings"])
        return {"StatusCode": 200, "Response": {"Data": {"SiteId": 201, "Title": pl["Title"], "ReferenceType": pl["ReferenceType"],
                                                          "Body": pl.get("Body", ""), "SiteName": "", "SiteGroupName": "",
                                                          "SiteSettings": pl["SiteSettings"]}}}

    def test_release_lifecycle_drift_against_last_release(self):
        self.unpack_dev()
        stg_before = self.r / "stg-before.json"
        stg_before.write_text(json.dumps(export(201, 202, "http://stg.internal")), encoding="utf-8")
        self._ledger({"ClassA": "No", "ClassB": "", "ClassC": "new in git"})
        # first release: nothing applied yet → plan allowed
        self.assertEqual(pls.main(["plan", str(stg_before), "--env", "stg", "--site", "a", "--release", "R1"]), 0)
        # mark-applied refuses when live != payload
        wrong = self.r / "wrong.json"
        wrong.write_text(json.dumps(self._stg_export_from_payload("R1", lambda s: s["Columns"].pop())), encoding="utf-8")
        self.assertEqual(pls.main(["mark-applied", "R1", str(wrong)]), 1)
        live = self.r / "stg-live.json"
        live.write_text(json.dumps(self._stg_export_from_payload("R1")), encoding="utf-8")
        self.assertEqual(pls.main(["mark-applied", "R1", str(live)]), 0)
        # git moves on (unreleased change) → NOT drift, because the baseline is the last release
        p = self.r / "config/a/site.json"
        site = json.loads(p.read_text(encoding="utf-8"))
        site["Columns"].append({"ColumnName": "ClassC", "LabelText": "new in git"})
        p.write_text(json.dumps(site), encoding="utf-8")
        self.assertEqual(pls.main(["drift", str(live), "--env", "stg", "--site", "a"]), 0)
        # customer edits stg in the UI (adds a choice) → drift; reverting it is data-impacting; plan refused
        def add_choice(s):
            [c for c in s["Columns"] if c["ColumnName"] == "ClassA"][0]["ChoicesText"] = "X\nY"
        edited = self.r / "stg-edited.json"
        edited.write_text(json.dumps(self._stg_export_from_payload("R1", add_choice)), encoding="utf-8")
        self.assertEqual(pls.main(["drift", str(edited), "--env", "stg", "--site", "a"]), 1)
        diffs, text = pls.drift_report(self.r, ENVS["envs"]["stg"], "stg", "a", json.loads(edited.read_text()), None)
        self.assertIn("Reverting this drift would be: data-impacting", text)
        self.assertEqual(pls.main(["plan", str(edited), "--env", "stg", "--site", "a", "--release", "R2"]), 1)
        # planning over the accepted drift would remove the customer's choice → data-impacting → migration required
        args = ["plan", str(edited), "--env", "stg", "--site", "a", "--release", "R2", "--accept-drift", "ops/drift/decision.md"]
        self.assertEqual(pls.main(args), 1)
        self._migration("mig")
        self.assertEqual(pls.main(args + ["--migration", "mig"]), 0)

    def _ledger(self, slots):
        (self.r / "design").mkdir(exist_ok=True)
        (self.r / "design/slot-ledger.json").write_text(json.dumps(
            {"a": {k: {"label": v, "status": "allocated", "zone": "madlab"} for k, v in slots.items()}}), encoding="utf-8")

    def _stg_live(self, extra_cols=(), editor=None):
        ex = export(201, 202, "http://stg.internal", extra_cols=extra_cols)
        if editor is not None:
            ex["Response"]["Data"]["SiteSettings"]["EditorColumnHash"] = {"General": editor}
        p = self.r / "stg-live-slots.json"
        p.write_text(json.dumps(ex), encoding="utf-8")
        return p

    def test_slots_clean(self):
        self.unpack_dev()
        self._ledger({"ClassA": "No", "ClassB": ""})
        self.assertEqual(pls.slot_collisions(*self._models(self._stg_live())), [])
        self.assertEqual(pls.main(["plan", str(self._stg_live()), "--env", "stg", "--site", "a", "--release", "R1"]), 0)

    def _models(self, live_path):
        e = ENVS["envs"]["stg"]
        live = pls.logical(json.loads(live_path.read_text(encoding="utf-8")), e)
        git = pls.read_tree(self.r / "config/a")
        led = json.loads((self.r / "design/slot-ledger.json").read_text(encoding="utf-8"))["a"]
        return live["settings"], git["settings"], led

    def test_slots_collision_blocks_plan(self):
        # customer added NumD in the UI on stg; git also defines NumD → deploying would overwrite it (A2)
        self.unpack_dev()
        p = self.r / "config/a/site.json"
        site = json.loads(p.read_text(encoding="utf-8"))
        site["Columns"].append({"ColumnName": "NumD", "LabelText": "git use"})
        p.write_text(json.dumps(site), encoding="utf-8")
        self._ledger({"ClassA": "No", "ClassB": ""})
        live = self._stg_live(extra_cols=[{"ColumnName": "NumD", "LabelText": "顧客の項目"}])
        kinds = {c["kind"] for c in pls.slot_collisions(*self._models(live))}
        self.assertEqual(kinds, {"collision"})
        self.assertEqual(pls.main(["plan", str(live), "--env", "stg", "--site", "a", "--release", "R1"]), 1)
        self.assertFalse((self.r / "releases/R1/plan.json").exists())

    def test_slots_editor_only_and_repurposed(self):
        # NumE enabled only by placing it on the editor (no Columns entry, D8); ClassA relabelled on the target
        self.unpack_dev()
        self._ledger({"ClassA": "No", "ClassB": ""})
        live = self._stg_live(editor=["ClassA", "ClassB", "NumE"])
        ex = json.loads(live.read_text(encoding="utf-8"))
        [c for c in ex["Response"]["Data"]["SiteSettings"]["Columns"] if c["ColumnName"] == "ClassA"][0]["LabelText"] = "別用途"
        live.write_text(json.dumps(ex), encoding="utf-8")
        found = {(c["slot"], c["kind"]) for c in pls.slot_collisions(*self._models(live))}
        self.assertEqual(found, {("NumE", "unledgered-live"), ("ClassA", "repurposed")})

    def test_slots_missing_ledger_refuses_plan(self):
        self.unpack_dev()
        self.assertEqual(pls.main(["plan", str(self._stg_live()), "--env", "stg", "--site", "a", "--release", "R1"]), 1)

    # ---------------------------------------------------------- multi-site release plan (A3)

    def _two_sites(self):
        """config/a references site b (Links + script); config/b references nothing."""
        self.unpack_dev()
        b = {"StatusCode": 200, "Response": {"Data": {"SiteId": 102, "Title": "dev_B", "ReferenceType": "Results", "Body": "",
             "UpdatedTime": "t0", "SiteSettings": {"Version": 1.017, "Columns": [{"ColumnName": "ClassA", "LabelText": "Code"}]}}}}
        p = self.r / "dev-b.json"
        p.write_text(json.dumps(b), encoding="utf-8")
        self.assertEqual(pls.main(["unpack", str(p), "--env", "dev", "--site", "b"]), 0)
        (self.r / "design").mkdir(exist_ok=True)
        (self.r / "design/slot-ledger.json").write_text(json.dumps({
            "a": {"ClassA": {"label": "No", "status": "allocated"}, "ClassB": {"label": "", "status": "allocated"}},
            "b": {"ClassA": {"label": "Code", "status": "allocated"}}}), encoding="utf-8")
        sa = self.r / "stg-a.json"
        sa.write_text(json.dumps(export(201, 202, "http://stg.internal")), encoding="utf-8")
        bs = json.loads(json.dumps(b)); bs["Response"]["Data"].update(SiteId=202, Title="stg_B", UpdatedTime="t-stg-b")
        sb = self.r / "stg-b.json"
        sb.write_text(json.dumps(bs), encoding="utf-8")
        return sa, sb

    def test_order_sites_and_cycles(self):
        self.assertEqual(pls.order_sites({"a": {"b"}, "b": set(), "c": {"a"}}), (["b", "a", "c"], []))
        self.assertEqual(pls.order_sites({"a": {"b"}, "b": {"a"}, "c": set()}), (["c", "a", "b"], ["a", "b"]))

    def test_release_plan_orders_by_dependency_and_reverses_rollback(self):
        sa, sb = self._two_sites()
        self.assertEqual(pls.main(["release-plan", "--env", "stg", "--release", "R1", "--export", f"a={sa}", "--export", f"b={sb}"]), 0)
        rel = self.r / "releases/R1"
        plan = json.loads((rel / "plan.json").read_text(encoding="utf-8"))
        self.assertEqual(plan["sites"], ["b", "a"])                      # a references b → b first
        self.assertEqual([x["site"] for x in plan["rollback"]], ["a", "b"])
        self.assertEqual(plan["per_site"]["a"]["depends_on"], ["b"])
        self.assertEqual(plan["per_site"]["b"]["snapshot_updated_time"], "t-stg-b")
        for f in ("payload-a.json", "payload-b.json", "rollback-a.json", "rollback-b.json", "raw-diff-a.md", "raw-diff-b.md"):
            self.assertTrue((rel / f).exists(), f)
        pa = json.loads((rel / "payload-a.json").read_text(encoding="utf-8"))
        self.assertIn("202", json.dumps(pa))                              # ${site:b} resolved to stg id
        self.assertNotIn("${site:", json.dumps(pa))

    def test_release_plan_writes_nothing_if_one_site_fails(self):
        sa, sb = self._two_sites()
        bad = json.loads(sb.read_text(encoding="utf-8"))
        bad["Response"]["Data"]["SiteSettings"]["Columns"].append({"ColumnName": "NumZ", "LabelText": "customer"})
        sb.write_text(json.dumps(bad), encoding="utf-8")
        self.assertEqual(pls.main(["release-plan", "--env", "stg", "--release", "R1", "--export", f"a={sa}", "--export", f"b={sb}"]), 1)
        self.assertFalse((self.r / "releases/R1").exists())

    def test_release_plan_mark_applied_and_drift_per_site(self):
        sa, sb = self._two_sites()
        self.assertEqual(pls.main(["release-plan", "--env", "stg", "--release", "R1", "--export", f"a={sa}", "--export", f"b={sb}"]), 0)
        rel = self.r / "releases/R1"
        lives = {}
        for site, sid in (("a", 201), ("b", 202)):
            pl = json.loads((rel / f"payload-{site}.json").read_text(encoding="utf-8"))
            p = self.r / f"live-{site}.json"
            p.write_text(json.dumps({"Response": {"Data": dict(pl, SiteId=sid)}}), encoding="utf-8")
            lives[site] = p
        self.assertEqual(pls.main(["mark-applied", "R1", "--export", f"a={lives['a']}"]), 1)   # every site required
        self.assertEqual(pls.main(["mark-applied", "R1", "--export", f"a={lives['a']}", "--export", f"b={lives['b']}"]), 0)
        self.assertEqual(json.loads((rel / "plan.json").read_text(encoding="utf-8"))["status"], "applied")
        # drift baseline for each site is that site's payload in the multi-site release
        self.assertEqual(pls.main(["drift", str(lives["b"]), "--env", "stg", "--site", "b"]), 0)
        self.assertEqual(pls.main(["drift", str(lives["a"]), "--env", "stg", "--site", "a"]), 0)

    def _migration(self, name, files=("migration.json", "backup", "dry-run.md")):
        d = self.r / name
        d.mkdir(exist_ok=True)
        if "migration.json" in files:
            (d / "migration.json").write_text(json.dumps({"site": "a", "keys": ["ClassA"], "rollback": "bulkupsert backup/"}), encoding="utf-8")
        if "backup" in files:
            (d / "backup").mkdir(exist_ok=True)
            (d / "backup/records.json").write_text("[]", encoding="utf-8")
        if "dry-run.md" in files:
            (d / "dry-run.md").write_text("dry run ok", encoding="utf-8")
        return d

    def test_migration_problems(self):
        self.assertTrue(pls.migration_problems(self.r, None))
        self._migration("m1", files=("migration.json",))
        probs = pls.migration_problems(self.r, "m1")
        self.assertTrue(any("backup" in p for p in probs) and any("dry-run" in p for p in probs))
        self._migration("m2")
        self.assertEqual(pls.migration_problems(self.r, "m2"), [])

    # ---------------------------------------------------------- permissions (C3, D15)

    def _with_perms(self, ex, inherit, entries):
        ex["Response"]["Data"].update(InheritPermission=inherit, Permissions=entries)
        return ex

    def test_permissions_unpack_refs_pack_resolves_and_lint(self):
        envs = json.loads(json.dumps(ENVS))
        envs["envs"]["dev"]["principals"] = {"admins": "Group,2"}
        envs["envs"]["stg"]["principals"] = {"admins": "Group,7"}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        exp = self.r / "dev.json"
        exp.write_text(json.dumps(self._with_perms(export(101, 102, "http://dev.internal"), 101, ["Group,2,511", "User,99,1"])), encoding="utf-8")
        self.assertEqual(pls.main(["unpack", str(exp), "--env", "dev", "--site", "a"]), 0)
        perms = json.loads((self.r / "config/a/permissions.json").read_text(encoding="utf-8"))
        self.assertEqual(perms["inherit"], "${site:a}")
        self.assertIn("${principal:admins},511", perms["entries"])
        self.assertTrue(any(i["rule"] == "L-PERM-01" and "User,99" in i["msg"] for i in pls.lint(self.r)))
        # unmapped principal cannot be packed for another environment
        with self.assertRaises(pls.Fail):
            pls.payload(pls.read_tree(self.r / "config/a"), envs["envs"]["stg"], "a")
        perms["entries"] = ["${principal:admins},511"]
        (self.r / "config/a/permissions.json").write_text(json.dumps(perms), encoding="utf-8")
        p = pls.payload(pls.read_tree(self.r / "config/a"), envs["envs"]["stg"], "a")
        self.assertEqual((p["InheritPermission"], p["Permissions"]), (201, ["Group,7,511"]))

    def test_permissions_not_managed_means_not_compared_and_not_sent(self):
        self.unpack_dev()                                  # export without permission keys → no permissions.json
        self.assertFalse((self.r / "config/a/permissions.json").exists())
        p = pls.payload(pls.read_tree(self.r / "config/a"), ENVS["envs"]["stg"], "a")
        self.assertNotIn("Permissions", p)                 # omitted → live permissions untouched (D15)
        live = self.r / "stg-perm.json"
        live.write_text(json.dumps(self._with_perms(export(201, 202, "http://stg.internal"), 201, ["User,1,511"])), encoding="utf-8")
        self._ledger({"ClassA": "No", "ClassB": ""})
        self.assertEqual(pls.main(["plan", str(live), "--env", "stg", "--site", "a", "--release", "R1"]), 0)
        self.assertEqual(json.loads((self.r / "releases/R1/plan.json").read_text(encoding="utf-8"))["classification"]["classification"], "config-only")

    def test_permission_change_is_permission_impacting(self):
        envs = json.loads(json.dumps(ENVS))
        for k, v in (("dev", "Group,2"), ("stg", "Group,7")):
            envs["envs"][k]["principals"] = {"admins": v}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        exp = self.r / "dev.json"
        exp.write_text(json.dumps(self._with_perms(export(101, 102, "http://dev.internal"), 101, ["Group,2,511"])), encoding="utf-8")
        pls.main(["unpack", str(exp), "--env", "dev", "--site", "a"])
        live = self.r / "stg-perm.json"
        live.write_text(json.dumps(self._with_perms(export(201, 202, "http://stg.internal"), 201, ["Group,7,31"])), encoding="utf-8")
        diffs = pls.flat_diff(pls.same_meta(pls.logical(json.loads(live.read_text()), envs["envs"]["stg"]), pls.read_tree(self.r / "config/a")),
                              pls.read_tree(self.r / "config/a"))
        self.assertEqual(pls.classify(diffs)["classification"], "permission-impacting")

    def test_last_applied_release_compares_instants_not_strings(self):
        # Escaped in slice 1.5: R-01 applied_at "…T09:19:30+09:00" (00:19 UTC) sorted after
        # R-02 "…T01:48:06+00:00" as strings, so drift kept using the older release as baseline.
        for rel, ts in (("R-01", "2026-11-05T09:19:30+09:00"), ("R-02", "2026-11-05T01:48:06+00:00")):
            d = self.r / "releases" / rel
            d.mkdir(parents=True)
            (d / "plan.json").write_text(json.dumps({"release": rel, "env": "stg", "site": "a",
                                                     "status": "applied", "applied_at": ts}), encoding="utf-8")
        got = [p["release"] for _, p in pls.releases_for(self.r, "stg", "a", "applied")]
        self.assertEqual(got, ["R-01", "R-02"])

    def test_classify_summary_change_is_data_impacting(self):
        d = [{"path": "settings.Summaries[1]", "kind": "added", "before": None, "after": {"Type": "Total"}}]
        c = pls.classify(d)
        self.assertEqual(c["classification"], "data-impacting")
        self.assertIn("D16", c["data_impacting"][0])

    def test_classify(self):
        d = [{"path": "settings.Columns[ClassB]", "kind": "removed", "before": {}, "after": None}]
        self.assertEqual(pls.classify(d)["classification"], "data-impacting")
        d = [{"path": "settings.Columns[ClassE].ChoicesText", "kind": "changed", "before": "a\nb", "after": "a\nb\nc"}]
        self.assertEqual(pls.classify(d)["classification"], "config-only")
        d = [{"path": "settings.Columns[ClassE].ChoicesText", "kind": "changed", "before": "a\nb", "after": "a"}]
        self.assertEqual(pls.classify(d)["classification"], "data-impacting")


if __name__ == "__main__":
    unittest.main()
