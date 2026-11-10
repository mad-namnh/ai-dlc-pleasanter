"""A sandbox never plans a configuration that writes to a shared site of its base environment unless a person
accepted that exact place, and tests write only to the sites of their own environment (ADR-0011):
python -m unittest discover -s tools/pls/tests -v"""
import contextlib
import io
import json
import shutil
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent))
import pls  # noqa: E402
import test_http as TH  # noqa: E402

OTHER_APP = 555          # a site on the same server that environments.json does not list
SUMMARY = {"SiteId": "${site:loans}", "DestinationColumn": "NumA", "LinkColumn": "ClassA", "Type": "Count"}


class SandboxSharedWrites(unittest.TestCase):
    setUp = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown

    def envs(self):
        return json.loads((self.r / "environments.json").read_text(encoding="utf-8"))

    def unpack_equipment(self, **settings):
        data = dict(self.fake.sites[TH.EQ], Body="",
                    SiteSettings={"Links": [{"ColumnName": "ClassA", "SiteId": TH.LO}], **settings})
        pls.wj(self.r / "equipment.json", {"Response": {"Data": data}})
        self.assertEqual(pls.main(["unpack", "equipment.json", "--env", "dev", "--site", "equipment"]), 0)

    def sandbox_of_equipment(self):
        """Sandbox dev-nam copies `equipment`; `loans` stays the shared dev site, referenced by a link only."""
        pls.wj(self.r / "loans.json", {"Response": {"Data": dict(self.fake.sites[TH.LO], Body="")}})
        self.assertEqual(pls.main(["unpack", "loans.json", "--env", "dev", "--site", "loans"]), 0)
        self.unpack_equipment()
        pls.wj(self.r / "design/slot-ledger.json", {"loans": {}, "equipment": {}})
        ev = self.envs()
        ev["envs"]["dev"]["pleasanter"] = {"app": "1.5.2"}
        (self.r / "environments.json").write_text(json.dumps(ev), encoding="utf-8")
        self.assertEqual(pls.main(["sandbox", "create", "--name", "nam", "--sites", "equipment", "--parent", str(TH.FOLDER)]), 0)
        boot = next((self.r / "releases").glob("B-*-dev-nam"))
        self.assertEqual(pls.main(["bootstrap", boot.name, "--yes"]), 0)
        self.assertEqual(self.envs()["envs"]["dev-nam"]["sites"]["loans"].get("shared_from"), "dev")

    def add_summary(self, sid):
        f = self.r / "config/equipment/site.json"
        site = json.loads(f.read_text(encoding="utf-8"))
        site.setdefault("Summaries", []).append({"Id": sid, **SUMMARY})
        f.write_text(json.dumps(site, ensure_ascii=False), encoding="utf-8")

    def late_script(self, *names):
        self.unpack_equipment(ServerScripts=[{"Id": i, "Name": n, "AfterUpdate": True,
                                              "Body": "items.Update(%d, JSON.stringify({}));" % TH.LO}
                                             for i, n in enumerate(names, 1)])

    def run_pls(self, *args):
        """(exit code, printed text). The text tells a shared-write refusal from any other refusal reason."""
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = pls.main(list(args))
        return code, out.getvalue()

    def plans(self):
        return sorted(p.name for p in (self.r / "releases").glob("R-*"))

    def test_baseline_a_sandbox_that_only_reads_the_shared_site_is_planned(self):
        self.sandbox_of_equipment()
        self.assertEqual(pls.main(["sandbox", "refresh", "--name", "nam"]), 0)

    def test_summary_into_a_shared_site_added_after_create_is_refused(self):
        self.sandbox_of_equipment()
        self.add_summary(1)
        code, text = self.run_pls("sandbox", "refresh", "--name", "nam")
        self.assertEqual(code, 1)
        self.assertIn("SHARED equipment: may write to loans (Summaries[1])", text)
        self.assertEqual(self.plans(), [])                                    # no payload written

    def test_server_script_referencing_a_shared_site_added_after_create_is_refused(self):
        self.sandbox_of_equipment()
        self.late_script("late")
        model = pls.read_tree(self.r / "config/equipment")
        self.assertIn("${site:loans}", json.dumps(model["scripts"]))          # the reference is logical in git
        self.assertEqual(pls.main(["sandbox", "refresh", "--name", "nam"]), 1)
        self.assertEqual(self.plans(), [])

    def test_accepting_records_the_places_and_a_new_place_is_refused_again(self):
        self.sandbox_of_equipment()
        self.late_script("late")
        self.assertEqual(pls.main(["sandbox", "refresh", "--name", "nam", "--allow-shared-writes"]), 0)
        self.assertEqual(self.envs()["envs"]["dev-nam"]["shared_writes"], {"equipment": {"loans": ["ServerScripts/late"]}})
        for d in (self.r / "releases").glob("R-*"):       # release ids are per second: keep the next plan id free
            shutil.rmtree(d)
        self.late_script("late", "later")
        code, text = self.run_pls("sandbox", "refresh", "--name", "nam")     # the earlier decision does not cover it
        self.assertEqual(code, 1)
        self.assertIn("(ServerScripts/later)", text)
        self.assertEqual(self.plans(), [])

    def test_release_plan_of_a_sandbox_runs_the_same_check(self):
        self.sandbox_of_equipment()
        self.add_summary(1)
        sid = self.envs()["envs"]["dev-nam"]["sites"]["equipment"]["id"]
        pls.wj(self.r / "sb.json", {"Response": {"Data": dict(self.fake.sites[sid], Body="")}})
        code, text = self.run_pls("release-plan", "--env", "dev-nam", "--release", "R-X", "--export", "equipment=sb.json")
        self.assertEqual(code, 1)
        self.assertIn("SHARED equipment", text)
        self.assertFalse((self.r / "releases/R-X").exists())

    def test_create_with_the_flag_records_what_was_accepted(self):
        self.unpack_equipment(Summaries=[{"Id": 1, **SUMMARY, "SiteId": TH.LO}])
        self.assertEqual(pls.main(["sandbox", "create", "--name", "nam", "--sites", "equipment", "--parent", str(TH.FOLDER),
                                   "--allow-shared-writes"]), 0)
        self.assertEqual(self.envs()["envs"]["dev-nam"]["shared_writes"], {"equipment": {"loans": ["Summaries[1]"]}})


class TestsWriteOnlyToTheEnvironment(unittest.TestCase):
    setUp = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown

    def test_a_spec_creating_in_a_site_outside_the_environment_is_refused(self):
        self.fake.sites[OTHER_APP] = {"SiteId": OTHER_APP, "Title": "other", "ReferenceType": "Results",
                                      "UpdatedTime": "t0", "SiteSettings": {}}
        (self.r / "s.json").write_text(json.dumps([{"id": "T-1", "steps": [
            {"op": "create", "site": OTHER_APP, "save": "x", "data": {"Title": "stray"}}]}]), encoding="utf-8")
        self.assertEqual(pls.main(["test", "s.json", "--env", "dev", "--site", "equipment", "--out", "x.json"]), 2)
        self.assertEqual(self.fake.records, {})                               # nothing sent

    def test_a_spec_on_the_sites_of_its_environment_still_runs(self):
        (self.r / "s.json").write_text(json.dumps([{"id": "T-2", "steps": [
            {"op": "create", "site": "${site:loans}", "save": "l", "data": {"Title": "ok"}}]}]), encoding="utf-8")
        self.assertEqual(pls.main(["test", "s.json", "--env", "dev", "--site", "equipment", "--out", "y.json"]), 0)
        self.assertEqual(len(self.fake.records), 1)


if __name__ == "__main__":
    unittest.main()
