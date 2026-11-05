"""Tests for the HTTP transport (ADR-0008) against a fake Pleasanter server — no network needed.
python -m unittest discover -s tools/pls/tests -v"""
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pls  # noqa: E402
import pls_http as H  # noqa: E402

FOLDER, EQ, LO = 900, 901, 902
KEYS = {"K-ADMIN": "admin", "K-STAFF": "staff"}


class Fake:
    def __init__(self):
        self.sites = {
            FOLDER: {"SiteId": FOLDER, "Title": "folder", "ReferenceType": "Sites", "UpdatedTime": "t0", "SiteSettings": {}},
            EQ: {"SiteId": EQ, "Title": "eq", "ReferenceType": "Results", "UpdatedTime": "t0", "SiteSettings": {}},
            LO: {"SiteId": LO, "Title": "lo", "ReferenceType": "Issues", "UpdatedTime": "t0",
                 "SiteSettings": {"Processes": [{"Id": 1, "Name": "return", "CurrentStatus": 100, "ChangedStatus": 900}]}},
        }
        self.records, self.next_id, self.calls = {}, 1000, []
        self.fail_update_on = None

    def handle(self, path, body):
        who = KEYS.get(body.get("ApiKey"))
        self.calls.append((path, who))
        if not who:
            return 401, {"Message": "unauthorized"}
        parts = path.strip("/").split("/")          # api items {id} {action}
        iid, act = int(parts[2]), parts[3]
        if act == "getsite":
            if iid not in self.sites or (who == "staff" and iid == LO):
                return 404, {"Message": "not found"}
            return 200, {"StatusCode": 200, "Response": {"Data": self.sites[iid]}}
        if act == "updatesite":
            if who != "admin":
                return 403, {}
            if self.fail_update_on == iid:
                return 500, {"Message": "boom"}
            s = self.sites[iid]
            s.update({k: body[k] for k in ("Title", "ReferenceType", "SiteSettings")})
            s["UpdatedTime"] = f"t{len(self.calls)}"
            return 200, {"Message": "updated"}
        if act == "createsite":
            self.next_id += 1
            self.sites[self.next_id] = {"SiteId": self.next_id, "Title": body["Title"], "ReferenceType": body["ReferenceType"],
                                        "UpdatedTime": "t0", "SiteSettings": {}}
            return 200, {"Id": self.next_id}
        if act == "create":
            if who == "staff":
                return (404 if iid == LO else 403), {"Message": "この操作を行うための権限がありません。"}
            self.next_id += 1
            self.records[self.next_id] = {"site": iid, "ResultId": self.next_id, "Status": 100, **{k: v for k, v in body.items() if k not in ("ApiKey", "ApiVersion")}}
            return 200, {"Id": self.next_id}
        if act == "get":
            if iid in self.sites:
                if who == "staff" and iid == LO:
                    return 404, {}
                data = [r for r in self.records.values() if r["site"] == iid]
                return 200, {"Response": {"Data": data, "TotalCount": len(data)}}
            rec = self.records.get(iid)
            if not rec or (who == "staff" and rec["site"] == LO):
                return 404, {}
            return 200, {"Response": {"Data": [rec]}}
        if act == "delete":
            rec = self.records.get(iid)
            if not rec or (who == "staff" and rec["site"] == LO):
                return 404, {}
            if who == "staff":
                return 403, {}
            del self.records[iid]
            return 200, {}
        if act == "update":
            rec = self.records.get(iid)
            if not rec or (who == "staff" and rec["site"] == LO):
                return 404, {}
            if who == "staff":
                return 403, {}
            if "ProcessId" in body:
                if rec["Status"] != 100:
                    return 400, {"Message": "要求が不正です。"}
                rec["Status"] = 900
            return 200, {}
        return 400, {}


def serve(fake):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])) or b"{}")
            code, js = fake.handle(self.path, body)
            data = json.dumps(js).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *a):
            pass
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


class HttpTest(unittest.TestCase):
    def setUp(self):
        self.fake = Fake()
        self.srv = serve(self.fake)
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        self.tmp = tempfile.TemporaryDirectory()
        self.r = Path(self.tmp.name)
        envs = {"managed_sites": ["equipment", "loans"], "envs": {
            "dev": {"role": "dev", "parent_id": FOLDER, "sites": {"equipment": {"id": EQ, "title": "dev_E"}, "loans": {"id": LO, "title": "dev_L"}}},
            "prod": {"role": "prod", "sites": {"equipment": {"id": EQ}}}}}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        (self.r / ".pls").mkdir()
        conns = {"dev": {"url": self.url, "keys": {"admin": "env:T_ADMIN", "staff": "file:staff.key"}, "allow_write": True},
                 "prod": {"url": self.url, "keys": {"admin": "env:T_ADMIN"}, "allow_write": True}}
        (self.r / ".pls/connections.json").write_text(json.dumps(conns), encoding="utf-8")
        (self.r / ".pls/staff.key").write_text("K-STAFF\n", encoding="utf-8")
        os.environ["T_ADMIN"] = "K-ADMIN"
        self.cwd = os.getcwd()
        os.chdir(self.r)

    def tearDown(self):
        os.chdir(self.cwd)
        self.srv.shutdown()
        self.tmp.cleanup()
        os.environ.pop("T_ADMIN", None)

    def plan(self, rel="R-1"):
        d = self.r / "releases" / rel
        d.mkdir(parents=True)
        steps = [{"op": "updatesite", "site": s, "site_id": i, "payload_file": f"payload-{s}.json", "expect_updated_time": "t0"}
                 for s, i in (("equipment", EQ), ("loans", LO))]
        plan = {"release": rel, "env": "dev", "status": "planned", "sites": ["equipment", "loans"], "classification": "config-only",
                "per_site": {"equipment": {"site_id": EQ}, "loans": {"site_id": LO}}, "steps": steps,
                "rollback": [{"op": "updatesite", "site": s, "site_id": i, "payload_file": f"rollback-{s}.json"} for s, i in (("loans", LO), ("equipment", EQ))]}
        (d / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
        for s in ("equipment", "loans"):
            (d / f"payload-{s}.json").write_text(json.dumps({"Title": f"new {s}", "ReferenceType": "Results", "SiteSettings": {"X": 1}}), encoding="utf-8")
            (d / f"rollback-{s}.json").write_text(json.dumps({"Title": f"old {s}", "ReferenceType": "Results", "SiteSettings": {}}), encoding="utf-8")
        return plan, d

    def test_keys_resolve_from_env_and_file_never_literal(self):
        conn = H.load_connection(self.r, "dev")
        self.assertEqual(H.resolve_key(conn, "admin"), "K-ADMIN")
        self.assertEqual(H.resolve_key(conn, "staff"), "K-STAFF")
        conn["keys"]["bad"] = "K-LITERAL"
        with self.assertRaises(H.TransportError):
            H.resolve_key(conn, "bad")
        os.environ.pop("T_ADMIN")
        with self.assertRaises(H.TransportError):
            H.resolve_key(conn, "admin")

    def test_write_guard(self):
        conn = H.load_connection(self.r, "prod")
        with self.assertRaises(H.TransportError):
            H.assert_writable({"role": "prod"}, conn, "prod")
        with self.assertRaises(H.TransportError):
            H.assert_writable({"role": "dev"}, {"allow_write": False}, "dev")
        H.assert_writable({"role": "stg"}, {"allow_write": True}, "stg")

    def test_apply_release_ok_and_rollback_on_failure(self):
        plan, d = self.plan()
        files = {f.name: json.loads(f.read_text()) for f in d.glob("*-*.json")}
        c = H.Client(self.url, "K-ADMIN")
        self.fake.fail_update_on = LO
        res = H.apply_release(c, plan, files)
        self.assertEqual(res["status"], "rolled-back")
        self.assertEqual(self.fake.sites[EQ]["Title"], "old equipment")       # restored in reverse order
        self.assertIn("restore loans", " ".join(res["log"]))
        self.fake.fail_update_on = None
        for s in (EQ, LO):
            self.fake.sites[s]["UpdatedTime"] = "t0"
        self.assertEqual(H.apply_release(c, plan, files)["status"], "applied-unverified")
        self.assertEqual(self.fake.sites[LO]["Title"], "new loans")

    def test_apply_refused_when_live_changed(self):
        plan, d = self.plan()
        self.fake.sites[LO]["UpdatedTime"] = "someone-else"
        files = {f.name: json.loads(f.read_text()) for f in d.glob("*-*.json")}
        res = H.apply_release(H.Client(self.url, "K-ADMIN"), plan, files)
        self.assertEqual(res["status"], "refused")
        self.assertEqual(self.fake.sites[EQ]["Title"], "eq")                   # nothing written

    def test_cli_apply_needs_confirmation(self):
        self.plan()
        import builtins
        orig = builtins.input
        builtins.input = lambda *_: "wrong"
        try:
            self.assertEqual(pls.main(["apply", "R-1"]), 1)
        finally:
            builtins.input = orig
        self.assertEqual(self.fake.sites[EQ]["Title"], "eq")

    def test_cli_apply_refused_for_prod(self):
        plan, d = self.plan()
        plan["env"] = "prod"
        (d / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
        self.assertEqual(pls.main(["apply", "R-1", "--yes"]), 2)
        self.assertEqual(self.fake.sites[EQ]["Title"], "eq")

    def test_bootstrap_creates_and_binds(self):
        d = self.r / "releases/B-1"
        d.mkdir(parents=True)
        envs = json.loads((self.r / "environments.json").read_text())
        envs["envs"]["dev"]["sites"]["extra"] = {"title": "dev_X"}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        (d / "bootstrap.json").write_text(json.dumps({"release": "B-1", "env": "dev", "parent_id": FOLDER, "steps": [
            {"op": "createsite", "site": "extra", "parent_id": FOLDER, "payload": {"Title": "dev_X", "ReferenceType": "Results", "SiteSettings": {}}}]}), encoding="utf-8")
        self.assertEqual(pls.main(["bootstrap", "B-1", "--yes"]), 0)
        self.assertTrue(json.loads((self.r / "environments.json").read_text())["envs"]["dev"]["sites"]["extra"]["id"])

    def test_role_tests_use_each_roles_key(self):
        specs = [
            {"id": "T-1", "steps": [{"op": "create", "site": "${site:equipment}", "save": "e", "data": {"Title": "a"}},
                                    {"op": "create", "site": "${site:loans}", "save": "l", "data": {"ClassHash": {"ClassA": "$e"}}},
                                    {"op": "get", "record": "$l", "expect": {"ClassHash.ClassA": "$e", "Status": 100}},
                                    {"op": "list", "site": "${site:equipment}", "contains": ["$e"]},
                                    {"op": "exec", "record": "$l", "process": "return", "expectHttp": 200},
                                    {"op": "exec", "record": "$l", "process": "return", "expectHttp": 400},
                                    {"op": "editPage", "record": "$l", "button": "返却", "present": False}]},
        ]
        (self.r / "admin.json").write_text(json.dumps(specs, ensure_ascii=False), encoding="utf-8")
        self.assertEqual(pls.main(["test", "admin.json", "--env", "dev", "--site", "loans", "--out", "res1.json"]), 0)
        res = json.loads((self.r / "res1.json").read_text(encoding="utf-8"))
        self.assertEqual(res["tests"][0]["status"], "pass-api-only")
        e = next(i for i, r in self.fake.records.items() if r["site"] == EQ)
        l = next(i for i, r in self.fake.records.items() if r["site"] == LO)
        staff = [{"id": "T-2", "as_key": "staff", "vars": {"e": "<fixture>"}, "steps": [
            {"op": "get", "record": "$e", "expect": {"Title": "a"}},
            {"op": "get", "record": "$l", "expectHttp": 404},
            {"op": "list", "site": "${site:loans}", "expectHttp": 404},
            {"op": "create", "site": "${site:equipment}", "expectHttp": 403, "data": {"Title": "x"}},
            {"op": "update", "record": "$e", "expectHttp": 403, "data": {}}]}]
        (self.r / "staff.json").write_text(json.dumps(staff), encoding="utf-8")
        self.assertEqual(pls.main(["test", "staff.json", "--env", "dev", "--site", "equipment", "--out", "res2.json",
                                   "--var", f"e={e}", "--var", f"l={l}"]), 0)
        self.assertIn(("/api/items/%d/get" % e, "staff"), self.fake.calls)    # really sent with the staff key
        res = json.loads((self.r / "res2.json").read_text(encoding="utf-8"))
        self.assertEqual(res["tests"][0]["status"], "pass")
        self.assertEqual(res["tests"][0]["as"], "staff")

    def test_role_tests_refused_when_two_roles_share_a_key(self):
        (self.r / ".pls/staff.key").write_text("K-ADMIN", encoding="utf-8")
        (self.r / "s.json").write_text(json.dumps([{"id": "T-9", "as_key": "staff", "steps": [
            {"op": "create", "site": "${site:equipment}", "expectHttp": 403, "data": {}}]}]), encoding="utf-8")
        self.assertEqual(pls.main(["test", "s.json", "--env", "dev", "--site", "equipment", "--out", "x.json"]), 2)
        self.assertEqual(self.fake.records, {})                                # nothing sent

    def test_step_level_key_creates_fixture_as_admin_then_checks_as_staff(self):
        (self.r / "s.json").write_text(json.dumps([{"id": "T-8", "as_key": "staff", "steps": [
            {"op": "create", "as_key": "admin", "site": "${site:equipment}", "save": "e", "data": {"Title": "fx"}},
            {"op": "get", "record": "$e", "expect": {"Title": "fx"}},
            {"op": "delete", "record": "$e", "expectHttp": 403}]}]), encoding="utf-8")
        self.assertEqual(pls.main(["test", "s.json", "--env", "dev", "--site", "equipment", "--out", "y.json"]), 0)
        self.assertEqual(len(self.fake.records), 1)

    def test_numbers_compare_by_value(self):
        self.assertTrue(H._check(1.0, 1))
        self.assertTrue(H._check(0.0, 0))
        self.assertFalse(H._check(1.0, 0))
        self.assertFalse(H._check(True, 1))

    def test_unreachable_host_is_a_clear_error(self):
        c = H.Client("http://127.0.0.1:9", "K-ADMIN", timeout=2)
        with self.assertRaises(H.TransportError):
            c.export_site(EQ)


    def test_tests_refused_without_allow_write(self):                  # TD-14b
        c = json.loads((self.r / ".pls/connections.json").read_text())
        c["dev"]["allow_write"] = False
        (self.r / ".pls/connections.json").write_text(json.dumps(c), encoding="utf-8")
        (self.r / "s.json").write_text(json.dumps([{"id": "T-1", "steps": [{"op": "create", "site": "${site:equipment}", "save": "e", "data": {}}]}]), encoding="utf-8")
        self.assertEqual(pls.main(["test", "s.json", "--env", "dev", "--site", "equipment", "--out", "x.json"]), 2)
        self.assertEqual(self.fake.records, {})

    def test_unfilled_fixture_is_refused_before_sending(self):          # TD-14c
        (self.r / "s.json").write_text(json.dumps([{"id": "T-2", "vars": {"e": "<item>"}, "steps": [
            {"op": "get", "record": "$e", "expect": {}}]}]), encoding="utf-8")
        self.assertEqual(pls.main(["test", "s.json", "--env", "dev", "--site", "equipment", "--out", "x.json"]), 2)
        self.assertEqual(self.fake.calls, [])

    def test_exec_as_a_role_that_cannot_read_the_site(self):           # TD-14d: process ids read with the default key
        (self.r / "s.json").write_text(json.dumps([{"id": "T-3", "as_key": "staff", "steps": [
            {"op": "create", "as_key": "admin", "site": "${site:loans}", "save": "l", "data": {}},
            {"op": "exec", "record": "$l", "process": "return", "expectHttp": 404}]}]), encoding="utf-8")
        self.assertEqual(pls.main(["test", "s.json", "--env", "dev", "--site", "loans", "--out", "z.json"]), 0)
        res = json.loads((self.r / "z.json").read_text(encoding="utf-8"))
        self.assertEqual(res["tests"][0]["status"], "pass", res)


if __name__ == "__main__":
    unittest.main()
