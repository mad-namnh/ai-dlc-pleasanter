"""KB probes with a server script or a test user's key (ADR-0025): run only on dev with mail to a sink or disabled,
under a role's own test-user key, and leave the probe site without the script and with the administrator alone —
also when the probe fails. Fake Pleasanter on 127.0.0.1 only."""
import copy
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent))
import pls  # noqa: E402
import pls_kbverify as KV  # noqa: E402
import test_http as TH  # noqa: E402
import test_kbverify as TK  # noqa: E402

SCRIPT = {"Id": 1, "Name": "probe", "BeforeUpdate": True, "Body": "if (model.Status === 900) { context.Error('x'); }"}
GUARDED = {"entry": "D1", "site": {"ReferenceType": "Results", "SiteSettings": {"ServerScripts": [SCRIPT]}},
           "roles": {"staff": 1},
           "tests": [{"id": "D1", "steps": [{"op": "create", "save": "r", "data": {"Title": "kbprobe"}},
                                            {"op": "create", "as_key": "staff", "data": {"Title": "x"}, "expectHttp": 403}]}],
           "teardown": {"SiteSettings": {}}}


def probe(**kw):
    p = copy.deepcopy(GUARDED)
    p.update(kw)
    return p


class GuardedProbeFileTest(unittest.TestCase):
    def refused(self, p, msg):
        with self.assertRaisesRegex(ValueError, msg):
            KV.check_probe(json.loads(json.dumps(p)))

    def test_a_guarded_probe_with_its_teardown_is_accepted(self):
        KV.check_probe(probe())
        for body in ("var a = [1, 2]; var b = a[0];", "model['ClassA'] = 'x';", "var itemsCount = 1;"):
            p = probe()
            p["site"]["SiteSettings"]["ServerScripts"][0]["Body"] = body          # plain code stays allowed
            KV.check_probe(p)

    def test_rules_the_file_alone_decides(self):
        for body in ("items.Get(1);", "notifications.x();", "httpClient.Get('u');", "\\u0069tems.Update(1);",
                     "\\x69tems", "globalThis['ite' + 'ms'];", "this['items'];", "eval('x');", "new Function('x');",
                     "require('x');", "var g = this; g['ite' + 'ms'].Update(1, {});",
                     "(function(){ return this })()['http' + 'Client'];",
                     "[].constructor.constructor('return 1')();", "String.fromCharCode(105, 116);", "x[k];",
                     "Reflect.get(x, 'y');"):
            p = probe()
            p["site"]["SiteSettings"]["ServerScripts"][0]["Body"] = body
            self.refused(p, "stays on its own record")
        self.refused(probe(teardown={"SiteSettings": {"ServerScripts": [SCRIPT]}}),
                     "server scripts are allowed only|teardown must not")
        self.refused(probe(teardown=None), "needs a teardown")
        self.refused(probe(roles={"staff": 0}), "permission value")
        self.refused(probe(roles={"Staff!": 1}), "role name")
        self.refused(probe(roles=None), "not declared in roles")
        nested = probe()
        nested["site"]["SiteSettings"]["Processes"] = [{"Name": "p", "ServerScripts": [SCRIPT]}]
        self.refused(nested, "only at the top level")
        self.refused(probe(site={"ReferenceType": "Results", "SiteSettings": {"ServerScripts": [SCRIPT],
                                                                               "Notifications": [{"Id": 1}]}}), "mail")
        self.refused(probe(roles={}), "roles must be an object")
        self.refused(probe(roles=["staff"]), "roles must be an object")
        self.refused(probe(site={"ReferenceType": "Results", "SiteSettings": {"ServerScripts": ["x"]}}),
                     "object with a Body")

    def test_the_guarded_check_on_its_own_refuses_a_script_in_the_teardown(self):
        import pls_kbverify_guarded as KG                                   # also when called without check_probe
        with self.assertRaisesRegex(ValueError, "teardown must not contain ServerScripts"):
            KG.check(probe(teardown={"SiteSettings": {"ServerScripts": [SCRIPT]}}))


class GuardedProbeRunTest(unittest.TestCase):
    setUp_http = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown
    use_kb = TK.CliTest.use_kb
    writes = TK.CliTest.writes

    def setUp(self):
        self.setUp_http()
        self.set_dev(values={"kb_probe_parent": TK.PROBE_FOLDER}, principals={"admin": "User,7", "staff": "Group,374"},
                     side_effects={"mail": "sink", "jobs": "disabled"})
        self.key_ref("file:test-users/dev-staff.key")
        (self.r / ".pls/test-users").mkdir()
        (self.r / ".pls/test-users/dev-staff.key").write_text("K-STAFF\n", encoding="utf-8")

    def key_ref(self, ref):
        p = self.r / ".pls/connections.json"
        c = json.loads(p.read_text(encoding="utf-8"))
        c["dev"]["keys"]["staff"] = ref
        p.write_text(json.dumps(c), encoding="utf-8")

    def set_dev(self, **kw):
        p = self.r / "environments.json"
        envs = json.loads(p.read_text(encoding="utf-8"))
        envs["envs"]["dev"].update(kw)
        p.write_text(json.dumps(envs), encoding="utf-8")

    def run_kb(self):
        return pls.main(["kb-verify", "--env", "dev", "--yes"])

    def result(self):
        data = json.loads(next((self.r / "ops/kb-verify").glob("*-dev.json")).read_text(encoding="utf-8"))
        return {p["probe"]: (p["status"], " ".join(p["log"])) for p in data["probes"]}

    def spy(self):
        """Record what kb-verify sends: the probe site created, every updatesite body, the delete calls."""
        self.sent, self.created = [], []
        orig = self.fake.handle

        def handle(path, body):
            code, js = orig(path, body)
            if path.endswith("/createsite") and code == 200:
                self.created.append(js["Id"])
            if path.endswith("/updatesite"):
                self.sent.append(copy.deepcopy(body))
            return code, js
        self.fake.handle = handle

    def state_sites(self):
        return json.loads((self.r / ".pls/kb-probes-dev.json").read_text(encoding="utf-8"))["sites"]

    def assert_deleted(self):
        sid = self.created[-1]
        self.assertIn((f"/api/items/{sid}/deletesite", "admin"), self.fake.calls)
        self.assertNotIn(sid, self.fake.sites)                               # gone, and getsite said so
        self.assertNotIn("D1-guarded", self.state_sites())                   # the next run makes a new site
        last = self.sent[-1]                                                 # harmless before the delete
        self.assertNotIn("ServerScripts", last["SiteSettings"])
        return sid, last

    def test_runs_with_the_script_and_the_role_then_deletes_the_site(self):
        self.use_kb({"D1-guarded": probe()})
        self.spy()
        self.assertEqual(self.run_kb(), 0, self.result())
        self.assertEqual(self.result()["D1-guarded"][0], "pass")
        self.assertEqual(self.sent[0]["SiteSettings"]["ServerScripts"][0]["Body"], SCRIPT["Body"])
        self.assertEqual(self.sent[0]["Permissions"], ["User,7,511", "Group,374,1"])
        sid, last = self.assert_deleted()
        self.assertIn((f"/api/items/{sid}/create", "staff"), self.fake.calls)    # the role's own key
        self.assertEqual(last["Permissions"], ["User,7,511"])

    def test_the_site_is_deleted_also_when_the_probe_fails(self):
        p = probe()
        p["tests"][0]["steps"][1]["expectHttp"] = 200                     # the role's create is refused: a failure
        self.use_kb({"D1-guarded": p})
        self.spy()
        self.assertEqual(self.run_kb(), 1)
        self.assertEqual(self.result()["D1-guarded"][0], "fail")
        self.assert_deleted()

    def test_an_unexpected_error_still_deletes_the_site(self):
        from unittest import mock
        import pls_http as H
        self.use_kb({"D1-guarded": probe()})
        self.spy()
        with mock.patch.object(H, "run_tests", side_effect=RuntimeError("crash")):
            with self.assertRaises(RuntimeError):
                self.run_kb()
        self.assert_deleted()

    def test_a_refused_delete_leaves_the_site_harmless_and_the_probe_in_error(self):
        self.use_kb({"D1-guarded": probe()})
        self.spy()
        self.fake.refuse_deletesite = True
        self.assertEqual(self.run_kb(), 2)
        status, log = self.result()["D1-guarded"]
        self.assertEqual(status, "error")
        self.assertIn("deletesite → HTTP 403", log)
        sid = self.created[-1]
        self.assertNotIn("ServerScripts", self.fake.sites[sid]["SiteSettings"])
        self.assertEqual(self.fake.sites[sid]["Permissions"], ["User,7,511"])
        self.assertEqual(self.state_sites()["D1-guarded"], sid)             # reused, never a second site

    def test_a_delete_that_answers_200_but_keeps_the_site_is_not_believed(self):
        self.use_kb({"D1-guarded": probe()})
        self.spy()
        self.fake.keep_deleted_site = True
        self.assertEqual(self.run_kb(), 2)
        status, log = self.result()["D1-guarded"]
        self.assertEqual(status, "error")
        self.assertIn("getsite still finds it", log)
        self.assertIn(self.created[-1], self.fake.sites)

    def after(self, when, then):
        """Wrap the fake: after a request for which when(path, body) holds, run then(site id)."""
        orig = self.fake.handle

        def handle(path, body):
            out = orig(path, body)
            if when(path, body):
                then(int(path.strip("/").split("/")[2]))
            return out
        self.fake.handle = handle

    def test_an_unclear_answer_after_the_delete_is_never_believed(self):
        self.use_kb({"D1-guarded": probe()})
        self.spy()
        self.fake.keep_deleted_site = True
        orig = self.fake.handle
        deleted = []

        def handle(path, body):
            if path.endswith("/deletesite"):
                deleted.append(path)
            elif deleted and path.endswith("/getsite"):
                return 500, {"Message": "busy"}                             # 5xx right after the delete
            return orig(path, body)
        self.fake.handle = handle
        self.assertEqual(self.run_kb(), 2)
        status, log = self.result()["D1-guarded"]
        self.assertEqual(status, "error")
        self.assertIn("only 404 counts", log)
        self.assertEqual(self.state_sites()["D1-guarded"], self.created[-1])   # not forgotten: no second site later

    def test_a_failed_teardown_is_an_error_and_the_site_is_still_deleted(self):
        self.use_kb({"D1-guarded": probe()})
        self.spy()
        orig = self.fake.handle

        def handle(path, body):
            if path.endswith("/updatesite") and "ServerScripts" not in body["SiteSettings"]:
                return 500, {"Message": "boom"}                             # only the teardown fails
            return orig(path, body)
        self.fake.handle = handle
        self.assertEqual(self.run_kb(), 2)
        status, log = self.result()["D1-guarded"]
        self.assertEqual(status, "error")
        self.assertIn("teardown failed", log)
        self.assertNotIn(self.created[-1], self.fake.sites)

    def test_a_site_that_is_no_longer_the_probes_own_is_never_deleted(self):
        self.use_kb({"D1-guarded": probe()})
        self.spy()
        self.after(lambda path, body: path.endswith("/updatesite") and "ServerScripts" not in body["SiteSettings"],
                   lambda sid: self.fake.sites[sid].update(ParentId=TH.FOLDER))     # moved to the app's folder
        self.assertEqual(self.run_kb(), 2)
        status, log = self.result()["D1-guarded"]
        self.assertEqual(status, "error")
        self.assertIn("not this probe's site", log)
        self.assertFalse(any(p.endswith("/deletesite") for p, _ in self.fake.calls))
        self.assertIn(self.created[-1], self.fake.sites)

    def test_a_role_key_file_holding_the_operators_key_is_refused(self):
        self.use_kb({"D1-guarded": probe()})
        (self.r / ".pls/test-users/dev-staff.key").write_text("K-ADMIN\n", encoding="utf-8")
        self.assert_not_run("same key as the operator's default key")

    def test_a_script_only_probe_deletes_its_site_without_touching_permissions(self):
        p = probe(roles=None)
        p["tests"][0]["steps"] = p["tests"][0]["steps"][:1]
        self.use_kb({"D1-guarded": p})
        self.spy()
        self.assertEqual(self.run_kb(), 0, self.result())
        _, last = self.assert_deleted()
        self.assertTrue(all("Permissions" not in b for b in self.sent))   # never touched: inherits the probe folder

    def assert_not_run(self, msg):
        n = len(self.fake.calls)
        self.assertEqual(self.run_kb(), 2)
        status, log = self.result()["D1-guarded"]
        self.assertEqual(status, "error")
        self.assertIn(msg, log)
        self.assertEqual(self.writes(n), [])

    def test_mail_that_may_reach_people_stops_the_probe_before_any_write(self):
        self.use_kb({"D1-guarded": probe()})
        for mail in ("live", "unknown"):
            self.set_dev(side_effects={"mail": mail, "jobs": "disabled"})
            self.assert_not_run("sink or is disabled")

    def test_only_the_test_users_own_key_file(self):
        self.use_kb({"D1-guarded": probe()})
        self.key_ref("file:staff.key")                                      # a person's key, not the test user's
        self.assert_not_run("not the test user's key file")
        self.key_ref("file:test-users/dev-staff.key")
        (self.r / ".pls/test-users/dev-staff.key").unlink()
        self.assert_not_run("not the test user's key file")

    def test_a_role_not_bound_to_a_group_stops_the_probe(self):
        self.use_kb({"D1-guarded": probe()})
        self.set_dev(principals={"admin": "User,7"})
        self.assert_not_run("not bound to a group")

    def test_a_state_file_naming_another_site_is_never_torn_down(self):
        self.use_kb({"D1-guarded": probe()})
        (self.r / ".pls/kb-probes-dev.json").write_text(json.dumps(
            {"url": self.url, "parent": TK.PROBE_FOLDER, "sites": {"D1-guarded": TH.LO}}), encoding="utf-8")
        before = copy.deepcopy(self.fake.sites[TH.LO])
        n = len(self.fake.calls)
        self.assertEqual(self.run_kb(), 2)
        self.assertEqual(self.writes(n), [])
        self.assertEqual(self.fake.sites[TH.LO], before)


if __name__ == "__main__":
    unittest.main()
