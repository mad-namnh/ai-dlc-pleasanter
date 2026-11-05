"""Sandboxes, harvest and semantic merge (ADR-0011, BR6):  python -m unittest discover -s tools/pls/tests -v"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent))
import pls  # noqa: E402
import pls_merge as MG  # noqa: E402
import test_http as TH  # noqa: E402


def col(name, label):
    return {"ColumnName": name, "LabelText": label}


class MergeTest(unittest.TestCase):
    def test_independent_additions_merge(self):
        o = {"Columns": [col("ClassA", "顧客")], "GridColumns": ["ClassA"], "Version": 1.017}
        a = {"Columns": [col("ClassA", "顧客"), col("ClassB", "担当")], "GridColumns": ["ClassA", "ClassB"], "Version": 1.017}
        b = {"Columns": [col("ClassA", "顧客"), col("NumA", "金額")], "GridColumns": ["ClassA", "NumA"], "Version": 1.017}
        c = []
        m = MG.merge(o, a, b, conflicts=c)
        self.assertEqual(c, [])
        self.assertEqual([x["ColumnName"] for x in m["Columns"]], ["ClassA", "ClassB", "NumA"])
        self.assertEqual(m["GridColumns"], ["ClassA", "ClassB", "NumA"])

    def test_same_element_changed_differently_is_a_conflict(self):
        o = {"Columns": [col("ClassA", "顧客")]}
        c = []
        m = MG.merge(o, {"Columns": [col("ClassA", "得意先")]}, {"Columns": [col("ClassA", "取引先")]}, conflicts=c)
        self.assertEqual(len(c), 1)
        self.assertIn("Columns[ClassA].LabelText", c[0])
        self.assertEqual(m["Columns"][0]["LabelText"], "得意先")                       # ours kept

    def test_removal_and_change_on_different_elements(self):
        o = {"Views": [{"Id": 1, "Name": "a"}, {"Id": 2, "Name": "b"}], "FilterColumns": ["ClassA", "ClassB"]}
        a = {"Views": [{"Id": 1, "Name": "a2"}, {"Id": 2, "Name": "b"}], "FilterColumns": ["ClassA", "ClassB"]}
        b = {"Views": [{"Id": 1, "Name": "a"}], "FilterColumns": ["ClassA"]}             # theirs removed view 2 and ClassB
        c = []
        m = MG.merge(o, a, b, conflicts=c)
        self.assertEqual(c, [])
        self.assertEqual(m["Views"], [{"Id": 1, "Name": "a2"}])
        self.assertEqual(m["FilterColumns"], ["ClassA"])

    def test_removed_on_one_side_changed_on_the_other_is_a_conflict(self):
        o = {"Processes": [{"Name": "return", "ChangedStatus": 900}]}
        c = []
        m = MG.merge(o, {"Processes": []}, {"Processes": [{"Name": "return", "ChangedStatus": 950}]}, conflicts=c)
        self.assertEqual(len(c), 1)
        self.assertEqual(m["Processes"][0]["ChangedStatus"], 950)

    def test_both_sides_adding_the_same_element_differently_or_reusing_an_id_conflict(self):
        o = {"Processes": [{"Id": 1, "Name": "return"}]}
        c = []
        MG.merge(o, {"Processes": o["Processes"] + [{"Id": 2, "Name": "a"}]},
                 {"Processes": o["Processes"] + [{"Id": 2, "Name": "b"}]}, path="", conflicts=c)
        self.assertTrue(any("Id 2 used twice" in x for x in c), c)
        c = []
        MG.merge({"Views": []}, {"Views": [{"Id": 3, "GridColumns": ["A"]}]}, {"Views": [{"Id": 3, "GridColumns": ["B"]}]}, conflicts=c)
        self.assertTrue(any("added differently" in x for x in c), c)

    def test_reordering_by_one_side_is_kept(self):
        c = []
        m = MG.merge({"GridColumns": ["A", "B"]}, {"GridColumns": ["A", "B", "Z"]}, {"GridColumns": ["B", "A"]}, conflicts=c)
        self.assertEqual((m["GridColumns"], c), (["B", "Z", "A"], []))   # theirs order; ours Z stays after B
        m = MG.merge({"GridColumns": ["A", "B", "C"]}, {"GridColumns": ["B", "A", "C"]}, {"GridColumns": ["A", "C", "B"]}, conflicts=c)
        self.assertEqual(len(c), 1)                                                     # both reordered differently

    def test_conflicts_are_visible_in_the_file(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            for n, label in (("o", "顧客"), ("a", "得意先"), ("b", "取引先")):
                pls.wj(t / n, {"Columns": [col("ClassA", label)]})
            self.assertEqual(pls.merge_site_files(str(t / "o"), str(t / "a"), str(t / "b")), 1)
            merged = json.loads((t / "a").read_text(encoding="utf-8"))
            self.assertIn("_pls_conflicts", merged)
            with self.assertRaises(pls.Fail):                                          # pack refuses it
                pls.payload({"meta": {}, "settings": merged, "scripts": {}}, {"sites": {"a": {"id": 1}}}, "a")

    def test_real_git_merge_with_the_driver(self):
        with tempfile.TemporaryDirectory() as t:
            r = Path(t)

            def git(*a):
                return subprocess.run(["git", *a], cwd=r, capture_output=True, text=True, encoding="utf-8")
            git("init", "-q")
            git("config", "user.email", "t@example.com")
            git("config", "user.name", "t")
            (r / "environments.json").write_text(json.dumps({"envs": {}, "managed_sites": []}), encoding="utf-8")
            (r / "pls.py").write_text(f"import sys\nsys.path.insert(0, {str(HERE.parents[1])!r})\nimport pls\n"
                                      "sys.exit(pls.main())\n", encoding="utf-8")
            site = r / "config/a/site.json"
            site.parent.mkdir(parents=True)
            pls.wj(site, {"Columns": [col("ClassA", "顧客")], "GridColumns": ["ClassA"]})
            cwd = os.getcwd()
            os.chdir(r)
            try:
                self.assertEqual(pls.main(["merge-install"]), 0)
            finally:
                os.chdir(cwd)
            git("add", "-A")
            git("commit", "-qm", "base")
            base = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
            git("checkout", "-qb", "dev1")
            pls.wj(site, {"Columns": [col("ClassA", "顧客"), col("ClassB", "担当")], "GridColumns": ["ClassA", "ClassB"]})
            git("commit", "-qam", "dev1 adds ClassB")
            git("checkout", "-q", base)
            git("checkout", "-qb", "dev2")
            pls.wj(site, {"Columns": [col("ClassA", "顧客"), col("NumA", "金額")], "GridColumns": ["ClassA", "NumA"]})
            git("commit", "-qam", "dev2 adds NumA")
            res = git("merge", "-q", "dev1", "-m", "merge")
            self.assertEqual(res.returncode, 0, res.stderr + res.stdout)                  # plain git would conflict
            merged = json.loads(site.read_text(encoding="utf-8"))
            self.assertEqual(sorted(x["ColumnName"] for x in merged["Columns"]), ["ClassA", "ClassB", "NumA"])


class SandboxTest(unittest.TestCase):
    setUp = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown

    def prepare(self):
        exp = self.r / "lo.json"
        pls.wj(exp, {"Response": {"Data": dict(self.fake.sites[TH.LO], Body="")}})
        self.assertEqual(pls.main(["unpack", str(exp), "--env", "dev", "--site", "loans"]), 0)
        pls.wj(self.r / "design/slot-ledger.json", {"loans": {}})
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["managed_sites"] = ["loans"]
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")

    def test_sandbox_lifecycle_never_touches_shared_dev(self):
        self.prepare()
        self.assertEqual(pls.main(["sandbox", "create", "--name", "nam", "--sites", "loans", "--parent", str(TH.FOLDER)]), 0)
        env = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))["envs"]["dev-nam"]
        self.assertEqual((env["role"], env["connection"], env["sites"]["loans"]["title"]), ("dev", "dev", "nam_dev_L"))
        boot = next((self.r / "releases").glob("B-*-dev-nam"))
        self.assertEqual(pls.main(["bootstrap", boot.name, "--yes"]), 0)                     # creates the copy only
        sid = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))["envs"]["dev-nam"]["sites"]["loans"]["id"]
        self.assertNotEqual(sid, TH.LO)
        self.assertEqual(pls.main(["sandbox", "refresh", "--name", "nam"]), 0)
        rel = next((self.r / "releases").glob("R-*-dev-nam"))
        n = len(self.fake.calls)
        pls.main(["apply", rel.name, "--yes"])          # the fake server drops a field on save → applied-differs (exit 1)
        updated = {p for p, _ in self.fake.calls[n:] if p.endswith("/updatesite")}
        self.assertEqual(updated, {f"/api/items/{sid}/updatesite"})                            # never the dev site
        self.assertEqual(pls.main(["sandbox", "drop", "--name", "nam"]), 0)
        self.assertNotIn("dev-nam", json.loads((self.r / "environments.json").read_text(encoding="utf-8"))["envs"])

    def test_shared_sites_and_stale_plans_are_never_written(self):
        self.prepare()
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["envs"]["dev-x"] = {"role": "dev", "connection": "dev", "sandbox_of": "dev", "parent_id": TH.FOLDER,
                                 "sites": {"loans": {"id": TH.LO, "title": "L", "shared_from": "dev"}}}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        exp = self.r / "lo.json"
        with self.assertRaises(pls.Fail):                                                   # release-plan refuses
            pls.main(["release-plan", "--env", "dev-x", "--release", "R-X", "--export", f"loans={exp}"])
        plan, d = self.plan("R-STALE")                                                       # a hand-written / stale plan
        plan["env"] = "dev-x"
        plan["sites"] = ["loans"]
        plan["per_site"] = {"loans": {"site_id": TH.LO, "side_effects": [], "payload_file": "payload-loans.json"}}
        (d / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
        n = len(self.fake.calls)
        self.assertEqual(pls.main(["apply", "R-STALE", "--yes"]), 2)
        self.assertFalse(any(p.endswith("/updatesite") for p, _ in self.fake.calls[n:]))

    plan = TH.HttpTest.plan

    def test_connection_alias_only_for_a_dev_sandbox(self):
        import pls_http as H
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["envs"]["dev-evil"] = {"role": "dev", "connection": "prod", "sites": {}}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        with self.assertRaises(H.TransportError):
            H.load_connection(self.r, "dev-evil")

    def test_sandbox_refuses_a_copy_that_writes_to_a_shared_site(self):
        self.prepare()
        exp = self.r / "eq.json"
        pls.wj(exp, {"Response": {"Data": dict(self.fake.sites[TH.EQ], Body="", SiteSettings={
            "Summaries": [{"Id": 1, "SiteId": TH.LO, "DestinationColumn": "NumA", "LinkColumn": "ClassA", "Type": "Count"}],
            "Links": [{"ColumnName": "ClassA", "SiteId": TH.LO}]})}})
        self.assertEqual(pls.main(["unpack", str(exp), "--env", "dev", "--site", "equipment"]), 0)
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["managed_sites"] = ["loans", "equipment"]
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        with self.assertRaises(pls.Fail):
            pls.main(["sandbox", "create", "--name", "nam", "--sites", "equipment", "--parent", str(TH.FOLDER)])
        self.assertEqual(pls.main(["sandbox", "create", "--name", "nam", "--sites", "equipment,loans", "--parent", str(TH.FOLDER)]), 0)

    def test_harvest_brings_ui_edits_into_git_and_refuses_unsaved_work(self):
        self.prepare()

        def git(*a):
            return subprocess.run(["git", *a], cwd=self.r, capture_output=True, text=True, encoding="utf-8")
        git("init", "-q")
        git("config", "user.email", "t@example.com")
        git("config", "user.name", "t")
        git("add", "config")
        git("commit", "-qm", "base")
        self.fake.sites[TH.LO]["SiteSettings"]["Columns"] = [col("ClassC", "UIで追加")]          # an edit made in the UI
        self.assertEqual(pls.main(["harvest", "--env", "dev", "--site", "loans"]), 0)
        site = json.loads((self.r / "config/loans/site.json").read_text(encoding="utf-8"))
        self.assertEqual(site["Columns"], [col("ClassC", "UIで追加")])
        self.assertFalse((self.r / "config/loans/permissions.json").exists() and
                         (self.r / "config/loans/permissions.json").read_text(encoding="utf-8").strip())   # never harvested
        with self.assertRaises(pls.Fail):                                                    # unsaved work in config/
            pls.main(["harvest", "--env", "dev", "--site", "loans"])


if __name__ == "__main__":
    unittest.main()
