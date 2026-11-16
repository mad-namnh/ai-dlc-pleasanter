"""KB probes with further probe sites, updates of their own records and group variables (ADR-0026): a probe stays
inside the probe folder, its own sites and records and the roles it declares. Fake Pleasanter on 127.0.0.1 only."""
import copy
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent))
import pls_kbverify as KV  # noqa: E402
import test_kbverify as TK  # noqa: E402
import test_kbverify_guarded_probes as TG  # noqa: E402

LINE = {"ReferenceType": "Results",
        "SiteSettings": {"Columns": [{"ColumnName": "ClassB", "ChoicesText": "[[${probe_site:main}]]"}],
                         "Links": [{"ColumnName": "ClassB", "SiteId": "${probe_site:main}",
                                    "Lookups": [{"From": "NumA", "To": "NumB"}]}]}}
MULTI = {"entry": "D1",
         "site": {"ReferenceType": "Results", "SiteSettings": {"Columns": [{"ColumnName": "NumA"}]}},
         "sites": {"line": copy.deepcopy(LINE)},
         "expect_stored": {"Columns[ColumnName=NumA].ColumnName": "NumA"},
         "tests": [{"id": "D1", "steps": [
             {"op": "create", "save": "m", "data": {"Title": "master", "NumHash": {"NumA": 1000}}},
             {"op": "create", "site": "line", "save": "l", "data": {"Title": "line", "ClassHash": {"ClassB": "$m"}}},
             {"op": "update", "record": "$m", "data": {"NumHash": {"NumA": 1200}}},
             {"op": "list", "site": "line", "contains": ["$l"], "excludes": ["$m"]}]}]}


def multi(**kw):
    p = copy.deepcopy(MULTI)
    p.update(kw)
    return p


def guarded_multi():
    p = multi(roles={"staff": 2}, teardown={"SiteSettings": {}})
    p["sites"]["line"]["teardown"] = {"SiteSettings": {}}
    p["tests"][0]["steps"][0]["data"]["ClassHash"] = {"ClassD": "$group_staff"}
    p["tests"][0]["steps"].append({"op": "update", "as_key": "staff", "record": "$l", "data": {"Title": "x"},
                                   "expectHttp": 403})
    return p


class ProbeFileTest(unittest.TestCase):
    def ok(self, p):
        KV.check_probe(json.loads(json.dumps(p)))

    def refused(self, p, msg):
        with self.assertRaisesRegex(ValueError, msg):
            KV.check_probe(json.loads(json.dumps(p)))

    def steps(self, *steps):
        p = multi()
        p["tests"][0]["steps"] = MULTI["tests"][0]["steps"][:2] + list(steps)
        return p

    def test_a_multi_site_probe_with_updates_of_its_own_records_is_accepted(self):
        self.ok(multi())
        self.ok(guarded_multi())
        self.ok(self.steps({"op": "list", "site": "main", "contains": ["$m"]}))

    def test_update_only_on_a_record_the_probe_created(self):
        self.refused(self.steps({"op": "update", "data": {"Title": "x"}}), "needs a record created earlier")
        self.refused(self.steps({"op": "update", "record": "$other", "data": {}}), "must be a record created earlier")
        self.refused(self.steps({"op": "get"}), "needs a record created earlier")
        self.refused(self.steps({"op": "delete", "record": "$m"}), "not allowed")

    def test_a_step_names_only_the_probes_own_sites_and_only_to_create_or_list(self):
        self.refused(self.steps({"op": "create", "site": "other", "data": {}}), "only the probe's own sites")
        self.refused(self.steps({"op": "create", "site": 44709, "data": {}}), "only the probe's own sites")
        self.refused(self.steps({"op": "get", "site": "line", "record": "$l"}), "only create")
        self.refused(self.steps({"op": "update", "site": "line", "record": "$l", "data": {}}), "only create")
        p = multi()
        p["tests"][0]["site"] = "line"                                       # never on a spec
        self.refused(p, "not allowed in probes")
        p = multi()
        p["tests"][0]["run_on"] = "line"
        self.refused(p, "not allowed in probes")

    def test_site_references_and_further_sites_are_checked(self):
        p = multi()
        p["sites"]["line"]["SiteSettings"]["Links"][0]["SiteId"] = "${probe_site:elsewhere}"
        self.refused(p, "only main and the probe's sites")
        p = multi()
        p["expect_stored"] = {"x": "${probe_site:elsewhere}"}               # expectations are checked too
        self.refused(p, "only main and the probe's sites")
        p["expect_stored"] = {"x": "${probe_site:line}"}
        self.ok(p)
        self.refused(multi(sites={"main": LINE}), "not 'main'")
        self.refused(multi(sites={"Line!": LINE}), "a key of a-z")
        self.refused(multi(sites={}), "sites must be an object")
        self.refused(multi(sites={"line": {"SiteSettings": {}}}), "ReferenceType")
        for extra in ({"ServerScripts": [TG.SCRIPT]}, {"Notifications": [{"Id": 1}]},
                      {"Processes": [{"Name": "p", "Reminders": [{"Id": 1}]}]}):
            p = multi()
            p["sites"]["line"]["SiteSettings"].update(extra)
            self.refused(p, "must not send mail")

    def test_group_variables_only_for_declared_roles(self):
        p = guarded_multi()
        p["tests"][0]["steps"][0]["data"]["ClassHash"] = {"ClassD": "$group_manager"}
        self.refused(p, r"\$group_manager")
        p = multi()
        p["tests"][0]["steps"][0]["data"]["ClassHash"] = {"ClassD": "$group_staff"}
        self.refused(p, r"\$group_staff")

    def test_a_guarded_probe_needs_a_teardown_for_every_site(self):
        p = guarded_multi()
        del p["sites"]["line"]["teardown"]
        self.refused(p, "teardown for every site")
        p = guarded_multi()
        p["sites"]["line"]["teardown"] = {"SiteSettings": {"ServerScripts": [TG.SCRIPT]}}
        self.refused(p, "must not send mail|must not contain ServerScripts")
        import pls_kbverify_guarded as KG                                   # also when called without check_probe
        with self.assertRaisesRegex(ValueError, "sites.line: the teardown must not contain ServerScripts"):
            KG.check(p)

    def test_a_record_name_never_stands_for_an_id_the_probe_did_not_create(self):
        for name in ("admin_uid", "today", "lastweek", "group_staff"):     # kb-verify's own variables
            self.refused(self.steps({"op": "create", "save": name, "data": {}},
                                    {"op": "update", "record": f"${name}", "data": {"Title": "x"}}),
                         "name of a kb-verify variable")
        self.refused(self.steps({"op": "create", "save": "z", "data": {}, "expectHttp": 403},   # refused: no record
                                {"op": "update", "record": "$z", "data": {}}), "must be a record created earlier")
        p = multi()
        p["tests"].append({"id": "second", "steps": [{"op": "update", "record": "$m", "data": {}}]})
        self.refused(p, "must be a record created earlier")                  # saves do not cross specs

    def test_a_step_site_that_is_not_a_name_is_refused(self):
        self.refused(self.steps({"op": "create", "site": ["main"], "data": {}}), "only the probe's own sites")

    def test_a_probe_file_name_with_a_double_underscore_is_refused(self):
        for name in ("D1-x__line", "D1-x_", "_D1-x"):                    # `X_` + key `k` would equal `X` + key `_k`
            t = TK.kb_dir({name: multi()})
            self.addCleanup(t.cleanup)
            with self.assertRaisesRegex(ValueError, "must not contain '__'"):
                KV.load_probes(Path(t.name) / "skills/pls-kb-pleasanter")
        for key in ("_line", "line_", "li__ne"):
            self.refused(multi(sites={key: LINE}), "single inner _")

    def test_exec_data_carries_no_variables(self):
        p = guarded_multi()
        p["tests"][0]["steps"].append({"op": "exec", "record": "$m", "process": "p",
                                       "data": {"ClassHash": {"ClassD": "$group_staff"}}})
        self.refused(p, "exec data is sent as written")

    def test_the_runner_refuses_a_record_this_spec_did_not_create(self):
        import pls_http as H
        calls = []

        class C:
            def export_site(self, sid):
                return {"Response": {"Data": {"SiteSettings": {}}}}

            def call(self, path, body=None):
                calls.append(path)
                return 200, {"Id": 501}, ""
        spec = {"id": "x", "vars": {"admin_uid": "7"}, "steps": [
            {"op": "update", "record": "$admin_uid", "data": {"Title": "x"}}]}
        res = H.run_tests(lambda role: C(), 900, [spec], "dev", confine=True)
        self.assertEqual(res["tests"][0]["status"], "error")
        self.assertEqual(calls, [])                                          # nothing sent
        spec["steps"] = [{"op": "create", "save": "r", "data": {}}, {"op": "update", "record": "$r", "data": {}}]
        res = H.run_tests(lambda role: C(), 900, [spec], "dev", confine=True)
        self.assertEqual(res["tests"][0]["status"], "pass")
        self.assertEqual(calls, ["/api/items/900/create", "/api/items/501/update"])

    def test_site_substitution(self):
        ids = {"main": 11, "line": 12}
        self.assertEqual(KV.substitute_sites({"SiteId": "${probe_site:line}", "t": "[[${probe_site:main}]]", "n": 3},
                                             ids), {"SiteId": 12, "t": "[[11]]", "n": 3})


class MultiSiteRunTest(unittest.TestCase):
    """Runs on the guarded fixture (dev, mail sink, role staff bound to group 374 with its own test-user key)."""
    G = TG.GuardedProbeRunTest
    setUp_http, setUp, tearDown = G.setUp_http, G.setUp, G.tearDown
    use_kb, writes, key_ref, set_dev = G.use_kb, G.writes, G.key_ref, G.set_dev
    run_kb, result, spy, state_sites = G.run_kb, G.result, G.spy, G.state_sites

    def site_by_title(self, title):
        return next(s for s in self.fake.sites.values() if s.get("Title") == title)

    def test_an_unguarded_probe_creates_substitutes_and_reuses_its_sites(self):
        self.use_kb({"D1-multi": multi()})
        self.spy()
        self.assertEqual(self.run_kb(), 0, self.result())
        main, line = self.site_by_title("zz_kbprobe_D1-multi"), self.site_by_title("zz_kbprobe_D1-multi__line")
        self.assertEqual((main["ParentId"], line["ParentId"]), (TK.PROBE_FOLDER, TK.PROBE_FOLDER))
        ls = line["SiteSettings"]
        self.assertEqual(ls["Columns"][0]["ChoicesText"], f"[[{main['SiteId']}]]")
        self.assertEqual(ls["Links"][0]["SiteId"], main["SiteId"])          # an int where it is the whole value
        rec = next(r for r in self.fake.records.values() if r["Title"] == "line")
        self.assertEqual(rec["site"], line["SiteId"])                        # the step's site is the probe's own
        m = next(i for i, r in self.fake.records.items() if r["Title"] == "master")
        self.assertIn((f"/api/items/{m}/update", "admin"), self.fake.calls)
        self.assertEqual(self.state_sites(), {"D1-multi": main["SiteId"], "D1-multi__line": line["SiteId"]})
        created = len(self.created)
        self.assertEqual(self.run_kb(), 0)
        self.assertEqual(len(self.created), created)                         # both sites reused
        self.assertFalse(any(p.endswith("/deletesite") for p, _ in self.fake.calls))

    def test_a_guarded_probe_grants_tears_down_and_deletes_every_site(self):
        self.use_kb({"D1-multi": guarded_multi()})
        self.spy()
        self.assertEqual(self.run_kb(), 0, self.result())
        self.assertEqual(len(self.created), 2)
        grants = [b["Permissions"] for b in self.sent if "Permissions" in b]
        self.assertEqual(grants, [["User,7,511", "Group,374,2"]] * 2 + [["User,7,511"]] * 2)
        for sid in self.created:
            self.assertIn((f"/api/items/{sid}/deletesite", "admin"), self.fake.calls)
            self.assertNotIn(sid, self.fake.sites)
        self.assertEqual(self.state_sites(), {})
        rec = next(r for r in self.fake.records.values() if r["Title"] == "master")
        self.assertEqual(rec["ClassHash"], {"ClassD": "374"})                # the role's group id
        line_rec = next(i for i, r in self.fake.records.items() if r["Title"] == "line")
        self.assertIn((f"/api/items/{line_rec}/update", "staff"), self.fake.calls)

    def test_a_failing_further_site_still_deletes_every_site(self):
        self.use_kb({"D1-multi": guarded_multi()})
        self.spy()
        orig = self.fake.handle

        def handle(path, body):
            if path.endswith("/updatesite") and body.get("Title") == "zz_kbprobe_D1-multi__line" \
                    and "Group,374,2" in (body.get("Permissions") or []):
                return 500, {"Message": "boom"}                             # the further site's save fails
            return orig(path, body)
        self.fake.handle = handle
        self.assertEqual(self.run_kb(), 1)
        status, log = self.result()["D1-multi"]
        self.assertEqual(status, "fail")
        self.assertIn("NG save line → HTTP 500", log)
        self.assertFalse(any(r["Title"] == "master" for r in self.fake.records.values()))   # no step ran
        for sid in self.created:
            self.assertNotIn(sid, self.fake.sites)

    def test_a_teardown_naming_a_site_never_created_still_deletes_the_main_site(self):
        p = guarded_multi()
        p["teardown"] = {"SiteSettings": {"Columns": [{"ColumnName": "ClassA", "ChoicesText": "[[${probe_site:line}]]"}]}}
        self.use_kb({"D1-multi": p})
        self.spy()
        orig = self.fake.handle

        def handle(path, body):
            if path.endswith("/createsite") and body.get("Title") == "zz_kbprobe_D1-multi__line":
                return 500, {"Message": "boom"}                             # the further site is never created
            return orig(path, body)
        self.fake.handle = handle
        self.assertEqual(self.run_kb(), 2)
        status, log = self.result()["D1-multi"]
        self.assertEqual(status, "error")
        self.assertIn("names a site not created", log)
        self.assertEqual(len(self.created), 1)
        self.assertNotIn(self.created[0], self.fake.sites)                   # deleted all the same

    def test_a_state_entry_of_a_further_site_that_is_not_its_own_stops_the_probe(self):
        self.use_kb({"D1-multi": guarded_multi()})
        (self.r / ".pls/kb-probes-dev.json").write_text(json.dumps(
            {"url": self.url, "parent": TK.PROBE_FOLDER, "sites": {"D1-multi__line": TG.TH.LO}}), encoding="utf-8")
        before = copy.deepcopy(self.fake.sites[TG.TH.LO])
        self.spy()
        self.assertEqual(self.run_kb(), 2)
        self.assertIn("not this probe's site", self.result()["D1-multi"][1])
        self.assertEqual(self.fake.sites[TG.TH.LO], before)                 # never written
        for sid in self.created:                                             # the main site it made is removed
            self.assertNotIn(sid, self.fake.sites)


if __name__ == "__main__":
    unittest.main()
