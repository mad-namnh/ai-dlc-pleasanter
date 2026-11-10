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
        self.drop_on_save = None
        self.fail_restore_on = None

    def handle(self, path, body):
        who = KEYS.get(body.get("ApiKey"))
        self.calls.append((path, who))
        if not who:
            return 401, {"Message": "unauthorized"}
        if path in ("/api/groups/get", "/api/users/get"):
            col = (body.get("View") or {}).get("ColumnFilterHash") or {}
            rows = [{"GroupId": 374, "GroupName": "zz_demo_総務"}, {"GroupId": 3740, "GroupName": "zz_demo_総務2"},
                    {"GroupId": 375, "GroupName": "zz_demo_社員"}] if "groups" in path else [{"UserId": 7, "LoginId": "nam"}]
            rows = [r_ for r_ in rows if all(str(v) in str(r_.get(k)) for k, v in col.items())]   # like-match, as Pleasanter
            return 200, {"Response": {"Data": rows, "TotalCount": len(rows)}}
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
            s.update({k: body[k] for k in ("InheritPermission", "Permissions") if k in body})
            if self.drop_on_save:                        # Pleasanter canonicalises on save (D8)
                s["SiteSettings"] = {k: v for k, v in s["SiteSettings"].items() if k != self.drop_on_save}
            s["UpdatedTime"] = f"t{len(self.calls)}"
            return 200, {"Message": "updated"}
        if act == "bulkupsert":                       # D13: matched by Keys → update, others created; D18: duplicates → 400
            if who != "admin":
                return 403, {"Message": "forbidden"}
            keys, added, updated = body.get("Keys") or [], 0, 0
            for row in body.get("Data") or []:
                hits = [r_ for r_ in self.records.values() if r_["site"] == iid and all(r_.get(k) == row.get(k) for k in keys)]
                if len(hits) > 1:
                    return 400, {"Message": "条件に一致するレコードが複数存在します。"}
                if hits:
                    hits[0].update(row)
                    updated += 1
                else:
                    self.next_id += 1
                    self.records[self.next_id] = {"site": iid, "ResultId": self.next_id, **row}
                    added += 1
            return 200, {"Message": f"{added} 件追加し、{updated} 件更新しました。"}
        if act == "createsite":
            self.next_id += 1
            self.sites[self.next_id] = {"SiteId": self.next_id, "Title": body["Title"], "ReferenceType": body["ReferenceType"],
                                        "ParentId": iid, "UpdatedTime": "t0", "SiteSettings": {}}
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
        self.srv.server_close()
        self.tmp.cleanup()
        os.environ.pop("T_ADMIN", None)

    def plan(self, rel="R-1"):
        d = self.r / "releases" / rel
        d.mkdir(parents=True)
        steps = [{"op": "updatesite", "site": s, "site_id": i, "payload_file": f"payload-{s}.json", "expect_updated_time": "t0"}
                 for s, i in (("equipment", EQ), ("loans", LO))]
        plan = {"release": rel, "env": "dev", "status": "planned", "sites": ["equipment", "loans"], "classification": "config-only",
                "per_site": {"equipment": {"site_id": EQ, "side_effects": []}, "loans": {"site_id": LO, "side_effects": []}}, "steps": steps,
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
        files = {f.name: json.loads(f.read_text(encoding="utf-8")) for f in d.glob("*-*.json")}
        c = H.Client(self.url, "K-ADMIN")
        self.fake.fail_update_on = LO
        res = H.apply_release(c, plan, files)
        # the failing site refuses its restore too: at the HTTP level that is a failed restore, never "rolled-back"
        self.assertEqual(res["status"], "recovery-required")
        self.assertEqual(res["failed_restores"], ["loans"])
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
        files = {f.name: json.loads(f.read_text(encoding="utf-8")) for f in d.glob("*-*.json")}
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
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["envs"]["dev"]["sites"]["extra"] = {"title": "dev_X"}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        (d / "bootstrap.json").write_text(json.dumps({"release": "B-1", "env": "dev", "parent_id": FOLDER, "steps": [
            {"op": "createsite", "site": "extra", "parent_id": FOLDER, "payload": {"Title": "dev_X", "ReferenceType": "Results", "SiteSettings": {}}}]}), encoding="utf-8")
        self.assertEqual(pls.main(["bootstrap", "B-1", "--yes"]), 0)
        self.assertTrue(json.loads((self.r / "environments.json").read_text(encoding="utf-8"))["envs"]["dev"]["sites"]["extra"]["id"])

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
        c = json.loads((self.r / ".pls/connections.json").read_text(encoding="utf-8"))
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

    def test_exec_without_expectation_must_succeed(self):
        # a refused process (second 返却 → 400) fails the step unless the spec expects the refusal
        (self.r / "s.json").write_text(json.dumps([{"id": "T-4", "steps": [
            {"op": "create", "site": "${site:loans}", "save": "l", "data": {}},
            {"op": "exec", "record": "$l", "process": "return"},
            {"op": "exec", "record": "$l", "process": "return"}]}]), encoding="utf-8")
        pls.main(["test", "s.json", "--env", "dev", "--site", "loans", "--out", "z.json"])
        res = json.loads((self.r / "z.json").read_text(encoding="utf-8"))
        self.assertEqual(res["tests"][0]["status"], "fail", res)
        self.assertTrue(any("expected HTTP 200" in line for line in res["tests"][0]["log"]), res)

    def test_timeout_from_the_connection_entry(self):
        self.assertEqual(H.conn_timeout({}), 30.0)
        self.assertEqual(H.conn_timeout({"timeout": 120}), 120.0)
        for bad in (0, 601, "60", True):
            with self.assertRaises(H.TransportError):
                H.conn_timeout({"timeout": bad})
        c = json.loads((self.r / ".pls/connections.json").read_text(encoding="utf-8"))
        c["dev"]["timeout"] = "slow"
        (self.r / ".pls/connections.json").write_text(json.dumps(c), encoding="utf-8")
        self.assertNotEqual(pls.main(["export", "--env", "dev", "--site", "equipment"]), 0)


    # ---------------------------------------------------------------- D3b (architecture review S1–S4, B2)

    def test_bootstrap_twice_is_refused_and_partial_creates_only_the_rest(self):          # S1
        d = self.r / "releases/B-2"
        d.mkdir(parents=True)
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["envs"]["dev"]["sites"].update({"x1": {"title": "X1"}, "x2": {"title": "X2"}})
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        steps = [{"op": "createsite", "site": s, "parent_id": FOLDER, "payload": {"Title": s, "ReferenceType": "Results", "SiteSettings": {}}}
                 for s in ("x1", "x2")]
        (d / "bootstrap.json").write_text(json.dumps({"release": "B-2", "env": "dev", "parent_id": FOLDER, "steps": steps,
                                                      "status": "partial", "created": {"x1": 4711}}), encoding="utf-8")
        envs["envs"]["dev"]["sites"]["x1"]["id"] = 4711
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        n = len(self.fake.sites)
        self.assertEqual(pls.main(["bootstrap", "B-2", "--yes"]), 0)
        self.assertEqual(len(self.fake.sites), n + 1)                                     # only x2 created
        self.assertEqual(json.loads((d / "bootstrap.json").read_text(encoding="utf-8"))["status"], "created")
        self.assertEqual(pls.main(["bootstrap", "B-2", "--yes"]), 2)                       # never twice
        self.assertEqual(len(self.fake.sites), n + 1)

    def test_apply_with_canonicalisation_differences_becomes_the_baseline(self):        # S2
        plan, d = self.plan()
        for s in ("equipment", "loans"):
            plan["per_site"][s]["payload_file"] = f"payload-{s}.json"
            (d / f"payload-{s}.json").write_text(json.dumps({"Title": f"new {s}", "ReferenceType": "Results",
                                                             "SiteSettings": {"X": 1, "Dflt": True}}), encoding="utf-8")
        (d / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
        self.fake.drop_on_save = "Dflt"
        self.assertEqual(pls.main(["apply", "R-1", "--yes"]), 1)
        p2 = json.loads((d / "plan.json").read_text(encoding="utf-8"))
        self.assertEqual(p2["status"], "applied-differs")
        self.assertTrue((d / "live-loans.json").exists())
        e = pls.env_conf(self.r, "dev")
        base, label = pls.baseline(self.r, e, "dev", "loans", None)
        self.assertIn("live-loans.json", label)
        self.assertNotIn("Dflt", base["settings"])                                        # fold-back release is not drift
        self.assertEqual(pls.new_sites(self.r, "dev"), set())

    def test_restore_restores_permissions_and_survives_errors(self):                    # S4
        self.fake.sites[EQ].update(InheritPermission=EQ, Permissions=["User,1,511"])
        files = {"payload-equipment.json": {"Title": "n", "ReferenceType": "Results", "SiteSettings": {}, "InheritPermission": FOLDER, "Permissions": []},
                 "rollback-equipment.json": {"Title": "o", "ReferenceType": "Results", "SiteSettings": {}, "InheritPermission": EQ, "Permissions": ["User,1,511"]},
                 "payload-loans.json": {"Title": "n", "ReferenceType": "Issues", "SiteSettings": {}},
                 "rollback-loans.json": {"Title": "o", "ReferenceType": "Issues", "SiteSettings": {}}}
        plan, _ = self.plan()
        self.fake.fail_update_on = LO
        res = H.apply_release(H.Client(self.url, "K-ADMIN"), plan, files)
        self.assertEqual(res["status"], "recovery-required")                     # loans refused its restore too
        self.assertEqual(self.fake.sites[EQ]["Permissions"], ["User,1,511"])
        self.assertEqual(self.fake.sites[EQ]["InheritPermission"], EQ)
        broken = H.Client("http://127.0.0.1:9", "K-ADMIN", timeout=1)
        out, failed = H.rollback(broken, plan, files)                                     # errors are logged, not raised
        self.assertEqual(len(out), 2)
        self.assertEqual(failed, ["loans", "equipment"])
        self.assertIn("error", out[0])

    def test_http_check_accepts_a_restricted_key_without_access(self):                  # B2
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["envs"]["dev"]["sites"] = {"loans": {"id": LO, "title": "dev_L"}}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        self.assertEqual(pls.main(["http-check", "--env", "dev"]), 0)                     # staff → 404 = valid key
        (self.r / ".pls/staff.key").write_text("K-WRONG", encoding="utf-8")
        self.assertEqual(pls.main(["http-check", "--env", "dev"]), 1)                     # 401 = bad key


    def test_setup_once_then_init_then_principals_after_design(self):                     # D4 + permission design in P2
        os.environ["PLS_PROFILE_DIR"] = str(self.r / "_profiles")
        try:
            answers = iter([self.url, f"{self.url}/items/{FOLDER}/index", "nam"])
            prof = pls.setup_profile("dev", ask=lambda *_: next(answers), ask_secret=lambda *_: "K-ADMIN")
            self.assertEqual(prof["parent_id"], FOLDER)
            self.assertEqual(prof["principals"], {"admin": "User,7"})
            self.assertNotIn("K-ADMIN", (self.r / "_profiles/dev.json").read_text(encoding="utf-8"))   # key never in the profile
            proj = self.r / "app"
            self.assertEqual(pls.main(["init", str(proj), "--approver", "Nam", "--no-git"]), 0)
            os.chdir(proj)
            self.assertEqual(pls.main(["http-check", "--env", "dev"]), 0)
            self.assertEqual(pls.lint(proj), [])
            # P2 permission design writes design/roles.json; after G2 the groups are bound by name
            (proj / "design/roles.json").write_text(json.dumps({"roles": {
                "somu": {"principal": "Group", "group_name": "zz_demo_総務"},
                "staff": {"principal": "Group", "group_name": "zz_demo_社員"},
                "audit": {"principal": "Group", "group_name": "zz_demo_監査"}}}, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(pls.main(["principals", "--env", "dev"]), 1)                   # 監査 does not exist yet
            ev = json.loads((proj / "environments.json").read_text(encoding="utf-8"))
            self.assertEqual(ev["envs"]["dev"]["principals"],
                             {"admin": "User,7", "somu": "Group,374", "staff": "Group,375"})   # exact name, not 総務2
        finally:
            os.environ.pop("PLS_PROFILE_DIR", None)


if __name__ == "__main__":
    unittest.main()
