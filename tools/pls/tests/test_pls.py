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
        self.assertEqual(pls.main(["plan", str(edited), "--env", "stg", "--site", "a", "--release", "R2",
                                   "--accept-drift", "ops/drift/decision.md"]), 0)

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

    def test_classify(self):
        d = [{"path": "settings.Columns[ClassB]", "kind": "removed", "before": {}, "after": None}]
        self.assertEqual(pls.classify(d)["classification"], "data-impacting")
        d = [{"path": "settings.Columns[ClassE].ChoicesText", "kind": "changed", "before": "a\nb", "after": "a\nb\nc"}]
        self.assertEqual(pls.classify(d)["classification"], "config-only")
        d = [{"path": "settings.Columns[ClassE].ChoicesText", "kind": "changed", "before": "a\nb", "after": "a"}]
        self.assertEqual(pls.classify(d)["classification"], "data-impacting")


if __name__ == "__main__":
    unittest.main()
