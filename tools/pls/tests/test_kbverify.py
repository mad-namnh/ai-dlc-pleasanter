"""Executable KB verification (ADR-0009 part 2, BR8):  python -m unittest discover -s tools/pls/tests -v"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent))
import pls  # noqa: E402
import pls_kbverify as KV  # noqa: E402
import test_http as TH  # noqa: E402

REAL_KB = HERE.parents[3] / "skills" / "pls-kb-pleasanter"
PROBE_FOLDER = 950
OK = {"entry": "D1", "site": {"ReferenceType": "Results", "SiteSettings": {"Columns": [{"ColumnName": "ClassA"}]}},
      "expect_stored": {"Columns[ColumnName=ClassA].ColumnName": "ClassA"},
      "tests": [{"id": "D1", "steps": [{"op": "create", "save": "r", "data": {"Title": "kbprobe", "ClassHash": {"ClassA": "$admin_uid"}}},
                                        {"op": "get", "record": "$r", "expect": {"ClassHash.ClassA": "$admin_uid"}}]}]}


def kb_dir(probes):
    t = tempfile.TemporaryDirectory()
    d = Path(t.name) / "skills/pls-kb-pleasanter/references/probes"
    d.mkdir(parents=True)
    (d.parent / "behaviours.md").write_text("| D1 | x |\n| D2 | y |\n| D9 | z |\n", encoding="utf-8")
    for name, p in probes.items():
        (d / f"{name}.json").write_text(json.dumps(p), encoding="utf-8")
    return t


class PureTest(unittest.TestCase):
    def test_paths_with_selectors(self):
        s = {"Columns": [{"ColumnName": "Status", "DefaultInput": "100"}, {"ColumnName": "ClassA"}], "Views": [{"Name": "v"}]}
        self.assertEqual(KV.get_path(s, "Columns[ColumnName=Status].DefaultInput"), "100")
        self.assertIsNone(KV.get_path(s, "Columns[ColumnName=ClassA].DefaultInput"))
        self.assertEqual(KV.get_path(s, "Views.0.Name"), "v")

    def test_framework_probes_load_and_match_the_index_both_ways(self):
        probes = KV.load_probes(REAL_KB)
        names = {p["_name"] for p in probes}
        index = json.loads((REAL_KB / "references/probes/index.json").read_text(encoding="utf-8"))["entries"]
        for p in probes:
            self.assertIn(p["_name"], index[p["entry"]]["probes"])
        for entry, v in index.items():
            for n in v["probes"]:
                self.assertIn(n, names, f"{entry}: {n}")

    def test_unsafe_probes_are_refused(self):
        cases = [
            {"site": {"ReferenceType": "Issues", "SiteSettings": {"Processes": [{"Name": "p", "Notifications": [{"Id": 1}]}]}}},
            {"site": {"ReferenceType": "Results", "SiteSettings": {"ServerScripts": [{"Name": "s", "Body": "x"}]}}},
            dict(OK, tests=[{"id": "x", "steps": [{"op": "create", "site": 44709, "save": "r", "data": {}}]}]),
            dict(OK, tests=[{"id": "x", "vars": {"r": 12345}, "steps": [{"op": "get", "record": "$r"}]}]),
            dict(OK, tests=[{"id": "x", "steps": [{"op": "get", "record": "$other"}]}]),
            dict(OK, tests=[{"id": "x", "steps": [{"op": "delete", "record": "$r"}]}]),
        ]
        for c in cases:
            p = dict({"entry": "D1"}, **c)
            with self.assertRaises(ValueError):
                KV.check_probe(json.loads(json.dumps(p)))

    def test_admin_principal_must_be_a_user(self):
        self.assertEqual(KV.admin_uid({"admin": "User,7"}), "7")
        for bad in ({}, {"admin": "Group,375"}, {"admin": "1"}, {"admin": "User,"}):
            with self.assertRaises(ValueError):
                KV.admin_uid(bad)


class CliTest(unittest.TestCase):
    setUp = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown

    def use_kb(self, probes):
        t = kb_dir(probes)
        orig = pls.FRAMEWORK
        pls.FRAMEWORK = Path(t.name)
        self.addCleanup(lambda: (setattr(pls, "FRAMEWORK", orig), t.cleanup()))
        self.fake.sites[PROBE_FOLDER] = {"SiteId": PROBE_FOLDER, "Title": "probes", "ReferenceType": "Sites", "UpdatedTime": "t0",
                                         "SiteSettings": {}}

    def set_env(self, parent=PROBE_FOLDER, admin="User,7"):
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["envs"]["dev"]["values"] = {"kb_probe_parent": parent}
        envs["envs"]["dev"]["principals"] = {"admin": admin}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")

    def writes(self, n=0):
        return [p for p, _ in self.fake.calls[n:] if p.endswith(("/createsite", "/updatesite", "/create", "/update"))]

    def test_probe_folder_must_be_a_folder_of_its_own(self):
        self.use_kb({"D1-ok": OK})
        for parent in (None, 0, TH.FOLDER, TH.EQ):                       # missing, zero, the app's folder, an app site
            self.set_env(parent=parent)
            self.assertEqual(pls.main(["kb-verify", "--env", "dev", "--yes"]), 2)
        self.set_env(admin="Group,375")
        self.assertEqual(pls.main(["kb-verify", "--env", "dev", "--yes"]), 2)
        self.assertEqual(self.writes(), [])

    def test_runs_reuses_and_reports_per_entry(self):
        self.use_kb({"D1-ok": OK, "D2-wrong": {"entry": "D2", "site": {"ReferenceType": "Results", "SiteSettings": {}}, "expect_save": 500}})
        self.set_env()
        self.assertEqual(pls.main(["kb-verify", "--env", "dev", "--yes"]), 1)
        report = next((self.r / "ops/kb-verify").glob("*-dev.md")).read_text(encoding="utf-8")
        self.assertIn("| D1 | pass |", report)
        self.assertIn("| D2 | fail |", report)
        self.assertIn("D9", report)
        created = sum(p.endswith("/createsite") for p, _ in self.fake.calls)
        pls.main(["kb-verify", "--env", "dev", "--yes"])
        self.assertEqual(sum(p.endswith("/createsite") for p, _ in self.fake.calls), created)   # own sites reused

    def test_state_pointing_at_a_real_site_never_writes_it(self):
        self.use_kb({"D1-ok": OK})
        self.set_env()
        st = self.r / ".pls/kb-probes-dev.json"
        st.write_text(json.dumps({"url": self.url, "parent": PROBE_FOLDER, "sites": {"D1-ok": TH.LO}}), encoding="utf-8")
        n = len(self.fake.calls)
        self.assertEqual(pls.main(["kb-verify", "--env", "dev", "--yes"]), 2)              # error, nothing written
        self.assertFalse(any(p == f"/api/items/{TH.LO}/updatesite" for p in self.writes(n)))
        self.assertEqual(self.fake.sites[TH.LO]["Title"], "lo")

    def test_failed_control_makes_the_probe_inconclusive(self):
        self.use_kb({"D2-control": {"entry": "D2", "site": {"ReferenceType": "Results", "SiteSettings": {}}, "expect_save": 500},
                     "D2-claim": {"entry": "D2", "site": {"ReferenceType": "Results", "SiteSettings": {}}, "control": "D2-control"}})
        self.set_env()
        pls.main(["kb-verify", "--env", "dev", "--yes"])
        data = json.loads(next((self.r / "ops/kb-verify").glob("*-dev.json")).read_text(encoding="utf-8"))
        self.assertEqual({p["probe"]: p["status"] for p in data["probes"]}, {"D2-claim": "inconclusive", "D2-control": "fail"})


if __name__ == "__main__":
    unittest.main()
