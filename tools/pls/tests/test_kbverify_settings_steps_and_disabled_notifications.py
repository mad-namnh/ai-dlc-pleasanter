"""KB probes that change their own site's settings, name a declared role's group or the operator in probe settings,
and hold disabled notifications (ADR-0027): only on the probe's own sites, never a script in a step, notifications
only disabled, to example.invalid and without credentials, and only where mail goes to a sink or is disabled.
Fake Pleasanter on 127.0.0.1 only."""
import copy
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent))
import pls_http as H  # noqa: E402
import pls_kbverify as KV  # noqa: E402
import pls_kbverify_guarded as KG  # noqa: E402
import test_kbverify_guarded_probes as TG  # noqa: E402

MAIL_OFF = {"Id": 1, "Type": 1, "Address": "zz@example.invalid, [Owner]", "Disabled": True}
SETTINGS = {"entry": "D1", "site": {"ReferenceType": "Results", "SiteSettings": {"Columns": [{"ColumnName": "NumA"}]}},
            "tests": [{"id": "D1", "steps": [
                {"op": "create", "save": "r", "data": {"Title": "kbprobe"}},
                {"op": "settings", "SiteSettings": {"Columns": [{"ColumnName": "NumA", "LabelText": "zz"}]}},
                {"op": "get", "record": "$r", "expect": {"Title": "kbprobe"}}]}]}


def probe(**kw):
    p = copy.deepcopy(SETTINGS)
    p.update(kw)
    return p


def with_step(step, **kw):
    p = probe(**kw)
    p["tests"][0]["steps"].insert(1, step)
    return p


class ProbeFileTest(unittest.TestCase):
    def ok(self, p):
        KV.check_probe(json.loads(json.dumps(p)))

    def refused(self, p, msg):
        with self.assertRaisesRegex(ValueError, msg):
            KV.check_probe(json.loads(json.dumps(p)))

    def test_a_settings_step_on_the_probes_own_sites_is_accepted(self):
        self.ok(probe())
        self.ok(with_step({"op": "settings_partial", "body": {"Processes": [{"Id": 1, "Name": "zz"}]}}))
        self.ok(with_step({"op": "settings_partial", "body": {"StatusControls": [{"Id": 1, "Status": 100}]}}))
        p = with_step({"op": "settings", "site": "line", "SiteSettings": {"GridPageSize": 50}},
                      sites={"line": {"ReferenceType": "Results", "SiteSettings": {}}})
        self.ok(p)

    def test_a_settings_step_names_only_the_probes_own_sites(self):
        self.refused(with_step({"op": "settings", "site": "other", "SiteSettings": {"GridPageSize": 1}}),
                     "only the probe's own sites")
        self.refused(with_step({"op": "settings", "site": 44709, "SiteSettings": {"GridPageSize": 1}}),
                     "only the probe's own sites")

    def test_a_settings_step_carries_no_script_and_is_not_empty(self):
        self.refused(with_step({"op": "settings", "SiteSettings": {"ServerScripts": [TG.SCRIPT]}}), "server scripts")
        self.refused(with_step({"op": "settings_partial", "body": {"ServerScripts": [TG.SCRIPT]}}),
                     "settings_partial body holds only Processes")
        self.refused(with_step({"op": "settings", "SiteSettings": {}}), "non-empty SiteSettings")
        self.refused(with_step({"op": "settings_partial"}), "non-empty body")

    def test_notifications_only_disabled_to_example_invalid_and_without_credentials(self):
        site = {"ReferenceType": "Results", "SiteSettings": {"Notifications": [MAIL_OFF]}}
        self.ok(probe(site=site, teardown={"SiteSettings": {}}))
        for item, msg in ((dict(MAIL_OFF, Disabled=False), "Disabled"),
                          ({k: v for k, v in MAIL_OFF.items() if k != "Disabled"}, "Disabled"),
                          (dict(MAIL_OFF, Address="boss@customer.co.jp"), "only example.invalid"),
                          (dict(MAIL_OFF, Type=2, Address="https://hooks.example/T0/B0/x"), "webhook-url"),
                          (dict(MAIL_OFF, Type=3, Address="", Token="abc"), "notification-token")):
            with self.subTest(item=item):
                s = copy.deepcopy(site)
                s["SiteSettings"]["Notifications"] = [item]
                self.refused(probe(site=s, teardown={"SiteSettings": {}}), msg)
        reminders = {"ReferenceType": "Results", "SiteSettings": {"Reminders": [
            {"Id": 1, "ReminderType": 1, "To": "x@example.invalid", "Disabled": True}]}}
        self.ok(probe(site=reminders, teardown={"SiteSettings": {}}))

    def test_no_target_outside_the_probe_in_a_notification(self):
        for item, msg in ((dict(MAIL_OFF, Type=9, Address="https://collector.example.test/x"), "a URL"),
                          (dict(MAIL_OFF, Address="[Owner],someone"), "recipient 'someone'"),
                          (dict(MAIL_OFF, Address="[Group12],[User5]"), r"recipient '\[Group12\]'"),
                          (dict(MAIL_OFF, CcAddress="[Dept3]"), r"recipient '\[Dept3\]'"),
                          (dict(MAIL_OFF, Body="see https://intranet.example.test"), "a URL")):
            with self.subTest(item=item):
                site = {"ReferenceType": "Results", "SiteSettings": {"Notifications": [item]}}
                self.refused(probe(site=site, teardown={"SiteSettings": {}}), msg)
        empty_hook = dict(MAIL_OFF, Type=2, Address="")                      # a webhook type without a target: shape only
        self.ok(probe(site={"ReferenceType": "Results", "SiteSettings": {"Notifications": [empty_hook]}},
                      teardown={"SiteSettings": {}}))
        self.refused(probe(site={"ReferenceType": "Results", "SiteSettings": {"Notifications": {"a": 1}}},
                           teardown={"SiteSettings": {}}), "must be a list of objects")

    def test_keys_are_compared_without_case_and_json_text_is_read(self):
        for site, msg in (({"Notifications": [dict(MAIL_OFF, disabled=False)]}, "differ only in case"),
                          ({"notifications": [dict(MAIL_OFF, Address="boss@customer.co.jp")]}, "only example.invalid"),
                          ({"Columns": [{"ColumnName": "ClassA", "ChoicesText": json.dumps({"ServerScripts": [1]})}]},
                           "ServerScripts")):
            with self.subTest(site=site):
                self.refused(probe(site={"ReferenceType": "Results", "SiteSettings": site},
                                   teardown={"SiteSettings": {}}), msg)
        self.refused(with_step({"op": "settings", "SiteSettings": {"serverScripts": [TG.SCRIPT]}}), "serverScripts")
        for site, msg in (({"notifications": [{"Id": 1, "Type": 3, "Token": "abc123", "Disabled": True}]}, "notification-token"),
                          ({"Notifications": [{"Id": 1, "Type": 3, "Disabled": True, "token": "abc123"}]}, "notification-token"),
                          ({"Notifications": [{"Id": 1, "Type": 9, "Address": "", "Disabled": True,
                                               "headers": '{"Authorization": "Bearer x"}'}]}, "credential-header"),
                          ({"Notifications": [{"Id": 1, "Type": 3, "Address": 12345, "Disabled": True}]}, "recipient '12345'")):
            with self.subTest(site=site):                                    # credentials and recipients without case
                self.refused(probe(site={"ReferenceType": "Results", "SiteSettings": site},
                                   teardown={"SiteSettings": {}}), msg)
        self.assertTrue(KG.is_guarded(probe(site={"ReferenceType": "Results",
                                                  "SiteSettings": {"notifications": [MAIL_OFF]}})))

    def test_a_partial_body_holds_only_a_settings_object(self):
        for body in ({"SiteSettings": json.dumps({"ServerScripts": [{"Body": "x"}]})},
                     {"Permissions": ["User,1,511"], "ParentId": 0},
                     {"SiteSettings": {"GridPageSize": 1}, "Title": "x"}):
            with self.subTest(body=body):
                self.refused(with_step({"op": "settings_partial", "body": body}), "settings_partial body|ServerScripts")
        for body in ({"SiteSettings": {"GridPageSize": 50}}, {"Processes": {"Id": 1}}, {"Styles": [{"Id": 1}]},
                     {"Processes": [{"Id": 1, "Notifications": [{"Id": 1, "Type": 2, "Address": "https://a.test/x",
                                                                  "Disabled": True}]}]}):
            with self.subTest(body=body):                                    # only the lists the route upserts
                self.refused(with_step({"op": "settings_partial", "body": body}), "settings_partial body|a URL")

    def test_an_unknown_probe_site_in_a_settings_step_refuses_the_file(self):
        self.refused(with_step({"op": "settings", "SiteSettings": {"Summaries": [{"SiteId": "${probe_site:zz}"}]}}),
                     r"names \['zz'\]")

    def test_a_settings_step_may_not_enable_a_notification(self):
        p = with_step({"op": "settings", "SiteSettings": {"Notifications": [dict(MAIL_OFF, Disabled=False)]}},
                      teardown={"SiteSettings": {}})
        self.refused(p, "Disabled")
        self.ok(with_step({"op": "settings", "SiteSettings": {"Notifications": [MAIL_OFF]}},
                          teardown={"SiteSettings": {}}))

    def test_a_teardown_never_holds_a_notification(self):
        self.refused(probe(site={"ReferenceType": "Results", "SiteSettings": {"Notifications": [MAIL_OFF]}},
                           teardown={"SiteSettings": {"Notifications": [MAIL_OFF]}}), "must not send mail")

    def test_a_probe_with_notifications_is_guarded_and_needs_a_teardown(self):
        p = probe(site={"ReferenceType": "Results", "SiteSettings": {"Notifications": [MAIL_OFF]}})
        self.assertTrue(KG.is_guarded(p))
        self.refused(p, "needs a teardown")
        self.assertTrue(KG.is_guarded(with_step({"op": "settings", "SiteSettings": {"Reminders": [
            {"Id": 1, "To": "a@example.invalid", "Disabled": True}]}})))
        self.assertFalse(KG.is_guarded(probe()))

    def test_group_and_operator_variables_in_probe_settings(self):
        site = {"ReferenceType": "Results",
                "SiteSettings": {"Views": [{"Id": 1, "ColumnFilterHash": {"Owner": "$admin_uid"}}]}}
        self.ok(probe(site=site))
        grp = {"ReferenceType": "Results", "SiteSettings": {"Views": [{"Id": 1, "Groups": ["$group_staff"]}]}}
        self.refused(probe(site=grp), r"\$group_staff in probe site settings")
        self.ok(probe(site=grp, roles={"staff": 1}, teardown={"SiteSettings": {}}))
        self.refused(with_step({"op": "settings", "SiteSettings": {"Views": [{"Id": 1, "Groups": ["$group_boss"]}]}},
                               roles={"staff": 1}, teardown={"SiteSettings": {}}), r"\$group_boss")

    def test_pls_test_cannot_run_a_settings_step(self):
        class Client:
            def export_site(self, _sid):
                return {"Response": {"Data": {"SiteSettings": {}}}}
        for op in KV.SETTINGS_OPS:
            res = H.run_tests(lambda _role: Client(), 1, [{"id": "t", "steps": [{"op": op, "SiteSettings": {"X": 1}}]}], "dev")
            self.assertEqual(res["tests"][0]["status"], "error")
            self.assertIn(f"unknown op {op}", res["tests"][0]["log"][-1])

    def test_no_principal_is_named_by_id(self):
        for where, settings in (("site", {"Processes": [{"Id": 1, "Name": "p", "Users": [5]}]}),
                                ("site", {"StatusControls": [{"Id": 1, "Groups": ["374"]}]}),
                                ("site", {"Views": [{"Id": 1, "depts": [3]}]})):
            with self.subTest(settings=settings):
                self.refused(probe(site={"ReferenceType": "Results", "SiteSettings": settings}), "principals named by id")
        self.refused(with_step({"op": "settings_partial", "body": {"Processes": [
            {"Id": 1, "Name": "p", "Permission": {"Users": [{"Id": 5}]}}]}}), "principals named by id")
        self.ok(probe(site={"ReferenceType": "Results", "SiteSettings": {"Processes": [
            {"Id": 1, "Name": "p", "Groups": ["$group_staff"], "Users": ["$admin_uid"]}]}},
            roles={"staff": 1}, teardown={"SiteSettings": {}}))

    def test_no_principal_is_named_in_other_shapes(self):
        """Ids in a scalar Users / Groups / Depts, a permission entry as text, a view filter on a user column, and any of
        these inside JSON text are refused too; statuses and other filters are not principals."""
        view = lambda h: {"Views": [{"Id": 1, "ColumnFilterHash": h}]}                     # noqa: E731
        for settings in ({"Processes": [{"Id": 1, "Name": "p", "Users": 5}]},
                         {"Views": [{"Id": 1, "Groups": "374"}]},
                         {"Processes": [{"Id": 1, "Name": "p", "Permission": "User,5,511"}]},
                         {"Exports": [{"Id": 1, "Header": ["Group,3,31"]}]},
                         view({"Owner": "[\"5\"]"}),
                         view({"manager": ["7"]}),
                         view({"Updator": 9}),
                         {"Columns": [{"ColumnName": "ClassD", "ChoicesText": "[[Users*]]"}], **view({"ClassD": "[\"12\"]"})},
                         {"Columns": [{"ColumnName": "ClassD", "ChoicesText": "[[Groups]]"}], **view({"ClassD": "12"})},
                         {"Processes": [{"Id": 1, "Name": "p", "View": "{\"Users\": [5]}"}]},
                         {"Views": [{"Id": 1, "ColumnFilterHash": "{\"Owner\": \"[\\\"5\\\"]\"}"}]},
                         view({"Owner": 5.0}),
                         {"Views": [{"Id": 1, "Users": {"5": 1}}]},
                         {"Processes": [{"Id": 1, "Name": "p", "Permission": "User,5,511,1"}]},
                         {"Processes": [{"Id": 1, "Name": "p", "Note": "User,5,511;Group,3"}]},
                         {"columns": [{"columnname": "ClassD", "choicestext": "[[Users*]]"}], **view({"ClassD": "[\"12\"]"})},
                         {"Columns": "[{\"ColumnName\": \"ClassD\", \"ChoicesText\": \"[[Depts]]\"}]",
                          **view({"ClassD": "[\"12\"]"})}):
            with self.subTest(settings=settings):
                self.refused(probe(site={"ReferenceType": "Results", "SiteSettings": settings}), "principals named by id")
        self.refused(with_step({"op": "settings", "SiteSettings": view({"Creator": "[\"3\"]"})}), "principals named by id")
        self.refused(probe(teardown={"SiteSettings": {"Views": [{"Id": 1, "Users": "Dept,2"}]}}), "teardown names principals")
        # not principals: a status filter, a plain column, a scalar variable, a label text with a comma
        self.ok(probe(site={"ReferenceType": "Results", "SiteSettings": {
            "Columns": [{"ColumnName": "ClassA", "ChoicesText": "a\nb"}],
            "Views": [{"Id": 1, "Name": "User, 5 rows", "ColumnFilterHash": {"Status": "[\"100\"]", "ClassA": "[\"1\"]"}}],
            "Processes": [{"Id": 1, "Name": "p", "Users": "$admin_uid"}]}}, teardown={"SiteSettings": {}}))

    def test_a_teardown_names_no_principal_and_cleanup_saves_no_settings(self):
        self.refused(probe(teardown={"SiteSettings": {"Processes": [{"Id": 1, "Users": [5]}]}}), "teardown names principals")
        self.refused(probe(teardown={"SiteSettings": {"Views": [{"Id": 1, "Groups": ["$group_staff"]}]}}, roles={"staff": 1}),
                     "teardown names principals")
        p = probe(sites={"line": {"ReferenceType": "Results", "SiteSettings": {},
                                  "teardown": {"SiteSettings": {"StatusControls": [{"Id": 1, "Groups": [7]}]}}}})
        self.refused(p, "principals")
        self.refused(probe(cleanup=[{"op": "settings", "SiteSettings": {"GridPageSize": 1}}]), "cleanup steps never save")

    def test_variables_are_replaced_as_whole_values_only(self):
        got = KV.substitute_vars({"a": "$admin_uid", "b": ["$group_staff"], "c": "x $admin_uid", "d": "$today"},
                                 {"admin_uid": "7", "group_staff": "374"})
        self.assertEqual(got, {"a": 7, "b": [374], "c": "x $admin_uid", "d": "$today"})


class ProbeRunTest(unittest.TestCase):
    """The guarded-probe environment: dev, mail to a sink, role staff bound to group 374, its own key."""
    setUp = TG.GuardedProbeRunTest.setUp
    setUp_http = TG.GuardedProbeRunTest.setUp_http
    tearDown = TG.GuardedProbeRunTest.tearDown
    use_kb = TG.GuardedProbeRunTest.use_kb
    writes = TG.GuardedProbeRunTest.writes
    key_ref = TG.GuardedProbeRunTest.key_ref
    set_dev = TG.GuardedProbeRunTest.set_dev
    run_kb = TG.GuardedProbeRunTest.run_kb
    result = TG.GuardedProbeRunTest.result
    spy = TG.GuardedProbeRunTest.spy
    state_sites = TG.GuardedProbeRunTest.state_sites

    def assert_deleted(self):
        sid = self.created[-1]
        self.assertIn((f"/api/items/{sid}/deletesite", "admin"), self.fake.calls)
        self.assertNotIn(sid, self.fake.sites)
        return sid, self.sent[-1]

    def partial_answers(self, code=200):
        self.partial = []
        orig = self.fake.handle

        def handle(path, body):
            if path.endswith("/updatesitesettings"):                    # route of 1.5.2.0; body shape not read
                self.fake.calls.append((path, "admin"))
                self.partial.append({k: v for k, v in body.items() if k not in ("ApiKey", "ApiVersion")})
                return code, {"Message": "updated" if code == 200 else "bad"}
            return orig(path, body)
        self.fake.handle = handle

    def test_a_settings_step_saves_the_probes_own_site_with_variables_replaced(self):
        p = with_step({"op": "settings", "SiteSettings": {"Views": [{"Id": 1, "Groups": ["$group_staff"],
                                                                     "ColumnFilterHash": {"Owner": "$admin_uid"}}],
                                                          "Notifications": [MAIL_OFF]}},
                      roles={"staff": 1}, teardown={"SiteSettings": {}})
        self.use_kb({"D1-settings": p})
        self.spy()
        self.assertEqual(self.run_kb(), 0, self.result())
        status, log = self.result()["D1-settings"]
        self.assertEqual(status, "pass", log)
        self.assertIn("ok  settings → HTTP 200", log)
        step_save = self.sent[1]                                             # first save, then the settings step
        view = step_save["SiteSettings"]["Views"][0]
        self.assertEqual((view["Groups"], view["ColumnFilterHash"]["Owner"]), ([374], 7))
        self.assertEqual(step_save["SiteSettings"]["Notifications"], [MAIL_OFF])
        self.assertEqual(step_save["Title"], KV.TITLE.format("D1-settings"))
        sid, last = self.assert_deleted()                                    # guarded: teardown, then deleted
        self.assertNotIn("Notifications", last["SiteSettings"])

    def test_a_partial_settings_step_calls_updatesitesettings_on_the_probe_site(self):
        self.use_kb({"D1-partial": with_step({"op": "settings_partial", "body": {"Processes": [{"Id": 1, "Name": "zz"}]},
                                              "expectHttp": 200})})
        self.spy()
        self.partial_answers()
        self.assertEqual(self.run_kb(), 0, self.result())
        sid = self.created[-1]
        self.assertIn((f"/api/items/{sid}/updatesitesettings", "admin"), self.fake.calls)
        self.assertEqual(self.partial, [{"Processes": [{"Id": 1, "Name": "zz"}]}])
        self.assertIn("ok  settings_partial → HTTP 200", self.result()["D1-partial"][1])

    def test_a_refused_settings_step_fails_the_probe(self):
        self.use_kb({"D1-partial": with_step({"op": "settings_partial", "body": {"Processes": [{"Id": 1, "Name": "zz"}]}})})
        self.partial_answers(400)
        self.assertEqual(self.run_kb(), 1)
        status, log = self.result()["D1-partial"]
        self.assertEqual(status, "fail")
        self.assertIn("NG  settings_partial → HTTP 400 (expected 200) bad", log)

    def test_a_settings_step_never_writes_a_site_that_is_not_the_probes(self):
        self.use_kb({"D1-settings": probe()})
        self.spy()
        orig = self.fake.handle

        def handle(path, body):                                              # the site changed hands before the step
            if path.endswith("/getsite") and self.sent:
                code, js = orig(path, body)
                if code == 200:
                    js = copy.deepcopy(js)
                    js["Response"]["Data"]["Title"] = "someone else's site"
                return code, js
            return orig(path, body)
        self.fake.handle = handle
        before = len(self.sent)
        self.run_kb()
        status, log = self.result()["D1-settings"]
        self.assertEqual(status, "error")                                    # a refusal is not evidence against the KB
        self.assertIn("is not this probe's site", log)
        self.assertEqual(len(self.sent), before + 1)                          # the first save only, no step save

    def test_notifications_run_only_where_mail_goes_to_a_sink_or_is_disabled(self):
        self.set_dev(side_effects={"mail": "live", "jobs": "disabled"})
        p = probe(site={"ReferenceType": "Results", "SiteSettings": {"Notifications": [MAIL_OFF]}},
                  teardown={"SiteSettings": {}})
        self.use_kb({"D1-notice": p})
        self.spy()
        self.run_kb()
        status, log = self.result()["D1-notice"]
        self.assertEqual(status, "error")
        self.assertIn("(disabled) notification", log)
        self.assertEqual(self.sent, [])                                      # nothing written for it


class ReadBackTest(unittest.TestCase):
    """A probe reads its site back after a settings step (siteConfig, list selectors) and names the ids it sent in
    expect_stored ($admin_uid / $group_<role>) — ADR-0027."""

    for _n in ("setUp", "setUp_http", "tearDown", "use_kb", "writes", "key_ref", "set_dev", "run_kb", "result", "spy",
               "state_sites"):
        locals()[_n] = getattr(TG.GuardedProbeRunTest, _n)

    def test_site_config_after_a_settings_step_and_ids_in_expectations(self):
        p = with_step({"op": "siteConfig", "expect": {"Columns[ColumnName=NumA].LabelText": "zz",
                                                      "Views[Id=1].ColumnFilterHash.Owner": "$admin_uid"}},
                      roles={"staff": 1}, teardown={"SiteSettings": {}})
        p["tests"][0]["steps"].insert(1, {"op": "settings", "SiteSettings": {
            "Columns": [{"ColumnName": "NumA", "LabelText": "zz"}],
            "Views": [{"Id": 1, "ColumnFilterHash": {"Owner": "$admin_uid"}}]}})
        p["site"]["SiteSettings"]["Views"] = [{"Id": 2, "Groups": ["$group_staff"]}]
        p["expect_stored"] = {"Views[Id=2].Groups": ["$group_staff"]}
        self.use_kb({"D1-read": p})
        self.assertEqual(self.run_kb(), 0, self.result())
        status, log = self.result()["D1-read"]
        self.assertEqual(status, "pass", log)
        self.assertIn("ok  SiteSettings.Columns[ColumnName=NumA].LabelText", log)
        self.assertIn("ok stored Views[Id=2].Groups = [374]", log)


class ObserveTest(unittest.TestCase):
    def test_an_observed_probe_never_decides_its_entry(self):
        rows = [{"entry": "D9", "probe": "a", "status": "observed", "log": []}]
        self.assertEqual(KV.entry_results(rows), {"D9": "observed"})
        rows.append({"entry": "D9", "probe": "b", "status": "pass", "log": []})
        self.assertEqual(KV.entry_results(rows), {"D9": "pass"})
        rows.append({"entry": "D9", "probe": "c", "status": "fail", "log": []})
        self.assertEqual(KV.entry_results(rows), {"D9": "fail"})
        self.assertIn("0/1 entries verified", KV.report("dev", None, rows[:1], [], "2026-11-17"))


class ObserveRunTest(unittest.TestCase):
    for _n in ("setUp", "setUp_http", "tearDown", "use_kb", "writes", "key_ref", "set_dev", "run_kb", "result", "spy",
               "state_sites"):
        locals()[_n] = getattr(TG.GuardedProbeRunTest, _n)

    def test_an_observe_probe_with_a_failing_check_ends_observed(self):
        p = probe(observe=True)
        p["tests"][0]["steps"][2]["expect"] = {"Title": "something else"}       # the check fails: still recorded
        self.use_kb({"D1-obs": p})
        self.run_kb()                                    # exit 1: an observed entry is not a verified one
        status, log = self.result()["D1-obs"]
        self.assertEqual(status, "observed")
        self.assertIn("NG  Title", log)


class PlsTestSiteConfigTest(unittest.TestCase):
    """`pls test` keeps its documented siteConfig behaviour (test-spec.md): positional paths, literal values."""

    def test_no_selector_and_no_variable_outside_kb_verify(self):
        class Client:
            def export_site(self, _sid):
                return {"Response": {"Data": {"SiteSettings": {"Columns": [{"ColumnName": "NumA", "LabelText": "x"}],
                                                               "Code": "$x"}}}}
        spec = {"id": "t", "vars": {"x": "12"}, "steps": [{"op": "siteConfig", "expect": {
            "Columns.0.LabelText": "x", "Code": "$x", "Columns[ColumnName=NumA].LabelText": None}}]}
        res = H.run_tests(lambda _r: Client(), 1, [spec], "dev")
        self.assertEqual(res["tests"][0]["status"], "pass", res["tests"][0]["log"])


if __name__ == "__main__":
    unittest.main()
