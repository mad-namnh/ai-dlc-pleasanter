"""`pls test-users --env dev` (ADR-0018 option C, ADR-0019 option B): one test user per Group role, its API key issued
through the screens only on a version where KB D32 is verified, the key reference added to connections.json only when
the role has none, and the user added to its group by read, add, write, check — never on stg, prod or a sandbox,
never without allow_write or a confirmation, never printing a password or a key."""
import contextlib
import io
import json
import os
import re
import sys
import tempfile
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
import pls  # noqa: E402
import pls_http as H  # noqa: E402
import pls_test_users as TU  # noqa: E402

ADMIN_KEY = "K-ADMIN"
ROLES = {"roles": {"somu": {"principal": "Group", "group_name": "zz_demo_総務"},
                   "boss": {"principal": "User", "login": "boss"}}}


class Fake:
    """Pleasanter 1.5.2 as the probes saw it (KB api.md "Users and groups", D32)."""

    def __init__(self):
        self.users = {7: {"UserId": 7, "LoginId": "nam", "password": None}}
        self.groups = {374: {"GroupId": 374, "GroupName": "zz_demo_総務", "Body": "role somu",
                             "GroupMembers": ["User,7,False", "User,8,True", "Dept,3,False"], "GroupChildren": [],
                             "UpdatedTime": "t0", "Ver": 1}}
        self.keys = {ADMIN_KEY: 7}
        self.sessions = {}
        self.next_id = 10060
        self.calls = []
        self.change_group_on_read = None        # n-th group read after which the group changes (UpdatedTime/Ver)
        self.drop_member_on_update = False
        self.group_reads = 0
        self.answer = {}                        # path → (status, json): a broken answer for one endpoint
        self.user_bodies = []
        self.issued = 0
        self.noise_token = False                # a new key-shaped string (not a key) before the key in the answer
        self.two_keys = False                   # the answer carries two keys the API accepts
        self.keep_old_keys = False              # an earlier key stays valid and stays on the API settings page
        self.on_key_issue = None                # called when a key is issued (a person editing files meanwhile)

    def api(self, path, body):
        if path in self.answer:
            return self.answer[path]
        who = self.keys.get(body.get("ApiKey"))
        if who is None and body.get("ApiKey") is not None:
            return 401, {"Id": 0, "StatusCode": 401, "Message": "Unable to authorize."}
        if path == "/api/users/get":
            lid = ((body.get("View") or {}).get("ColumnFilterHash") or {}).get("LoginId", "")
            rows = [{"UserId": u["UserId"], "LoginId": u["LoginId"], "SecretKey": "S3CRET",
                     "TenantManager": u.get("tm", False), "Disabled": u.get("disabled", False)} for u in self.users.values() if lid in u["LoginId"]]
            return 200, {"StatusCode": 200, "Response": {"Data": rows, "TotalCount": len(rows)}}
        if path == "/api/users/create":
            self.user_bodies.append(sorted(k for k in body if k not in ("ApiKey", "ApiVersion")))
            if any(u["LoginId"] == body["LoginId"] for u in self.users.values()):
                return 500, {"Id": 0, "StatusCode": 500, "Message": "このログインIDは既に使用中です"}
            self.next_id += 1
            self.users[self.next_id] = {"UserId": self.next_id, "LoginId": body["LoginId"], "password": body["Password"]}
            return 200, {"Id": self.next_id, "StatusCode": 200, "Message": "created"}
        if path == "/api/groups/get":
            self.group_reads += 1
            if self.change_group_on_read and self.group_reads == self.change_group_on_read:
                g = self.groups[374]
                g["Ver"] += 1
                g["UpdatedTime"] = "t-person"
            name = ((body.get("View") or {}).get("ColumnFilterHash") or {}).get("GroupName", "")
            rows = [json.loads(json.dumps(g)) for g in self.groups.values() if name in g["GroupName"]]
            return 200, {"StatusCode": 200, "Response": {"Data": rows, "TotalCount": len(rows)}}
        m = re.fullmatch(r"/api/groups/(\d+)/update", path)
        if m:
            g = self.groups[int(m.group(1))]
            for k in ("GroupName", "Body"):
                if k in body:
                    g[k] = body[k]
            if "GroupMembers" in body:
                g["GroupMembers"] = list(body["GroupMembers"])[1:] if self.drop_member_on_update else list(body["GroupMembers"])
            g["Ver"] += 1
            return 200, {"Id": g["GroupId"], "StatusCode": 200, "Message": "updated"}
        return 400, {"Message": "unknown"}

    def screen(self, method, path, form, cookie):
        user = self.sessions.get(cookie)
        if path.startswith("/users/authenticate"):
            u = [x for x in self.users.values() if x["LoginId"] == form.get("Users_LoginId", [""])[0]]
            if u and u[0]["password"] == form.get("Users_Password", [""])[0]:
                sid = f"sess{len(self.sessions)}"
                self.sessions[sid] = u[0]["UserId"]
                return 200, json.dumps([{"Method": "Log"}, {"Method": "Href", "Value": "/"}]), sid
            return 200, json.dumps([{"Method": "Message", "Value": "failed"}]), None
        if user is None:
            return 302, "", None
        if path == "/users/editapi":
            key = "".join(f'<input value="{k}">' for k, v in self.keys.items() if v == user)
            return 200, f'{key}<script src="/a.js?v=STATICHASHSTATICHASHSTATICHASH12"></script>', None
        if path == "/users/createapikey":
            for k in [k for k, v in self.keys.items() if v == user and not self.keep_old_keys]:
                del self.keys[k]
            self.issued += 1
            key = f"ISSUED{user:04d}{self.issued:04d}" + "f" * 40          # random on a real server
            self.keys[key] = user
            extra = ""
            if self.noise_token:
                extra += f'<input id="Token" value="NOISE{len(self.calls):06d}' + "a" * 40 + '">'
            if self.two_keys:
                second = f"SECOND{user:04d}" + "e" * 40
                self.keys[second] = user
                extra += f'<input id="ApiKey2" value="{second}">'
            if self.on_key_issue:
                self.on_key_issue()
            return 200, json.dumps([{"Method": "Log"}, {"Method": "ReplaceAll", "Target": "#EditorTabsContainer",
                                     "Value": extra + f'<input id="ApiKey" value="{key}">'}]), None
        if path == "/users/logout":
            return 200, "", None
        return 404, "", None


def serve(fake):
    class Handler(BaseHTTPRequestHandler):
        def answer(self, method):
            n = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(n) if n else b""
            fake.calls.append((method, self.path))
            if self.path.startswith("/api/"):
                code, js = fake.api(self.path, json.loads(raw or b"{}"))
                data, extra = json.dumps(js).encode(), {"Content-Type": "application/json"}
            else:
                ck = re.search(r"sid=(\w+)", self.headers.get("Cookie") or "")
                code, text, sid = fake.screen(method, self.path, urllib.parse.parse_qs(raw.decode()),
                                              ck.group(1) if ck else None)
                data, extra = text.encode(), {"Content-Type": "text/html"}
                if sid:
                    extra["Set-Cookie"] = f"sid={sid}; Path=/"
                if code == 302:
                    extra["Location"] = "https://sso.example/login"
            self.send_response(code)
            for k, v in extra.items():
                self.send_header(k, v)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            self.answer("POST")

        def do_GET(self):
            self.answer("GET")

        def log_message(self, *a):
            pass
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


class TestUsers(unittest.TestCase):
    def setUp(self):
        self.fake = Fake()
        self.srv = serve(self.fake)
        url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        self.tmp = tempfile.TemporaryDirectory()
        self.r = Path(self.tmp.name) / "pls-demo-x"
        (self.r / ".pls").mkdir(parents=True)
        (self.r / "design").mkdir()
        (self.r / "design/roles.json").write_text(json.dumps(ROLES, ensure_ascii=False), encoding="utf-8")
        envs = {"envs": {
            "dev": {"role": "dev", "sites": {}, "principals": {"admin": "User,7", "somu": "Group,374"},
                    "pleasanter": {"app": "1.5.2"}},
            "stg": {"role": "stg", "sites": {}, "principals": {"somu": "Group,374"}},
            "prod": {"role": "prod", "sites": {}, "principals": {"somu": "Group,374"}},
            "sbx": {"role": "dev", "sandbox_of": "dev", "connection": "dev", "sites": {}}}}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        conns = {e: {"url": url, "keys": {"admin": "env:T_ADMIN"}, "allow_write": True} for e in ("dev", "stg", "prod")}
        (self.r / ".pls/connections.json").write_text(json.dumps(conns), encoding="utf-8")
        os.environ["T_ADMIN"] = ADMIN_KEY
        self.cwd = os.getcwd()
        os.chdir(self.r)

    def tearDown(self):
        os.chdir(self.cwd)
        self.srv.shutdown()
        self.srv.server_close()
        self.tmp.cleanup()
        os.environ.pop("T_ADMIN", None)

    def run_pls(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = pls.main(["test-users", *argv])
        return rc, out.getvalue()

    def writes(self, n=0):
        return [p for _, p in self.fake.calls[n:] if re.search(r"/(create|update|delete|createapikey)$", p)]

    def conns(self):
        return json.loads((self.r / ".pls/connections.json").read_text(encoding="utf-8"))

    def set_env(self, env, **kw):
        ev = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        ev["envs"][env].update(kw)
        (self.r / "environments.json").write_text(json.dumps(ev), encoding="utf-8")

    def test_user_key_reference_and_membership_on_dev_and_nothing_secret_printed(self):
        rc, out = self.run_pls("--env", "dev", "--yes")
        self.assertEqual(rc, 0, out)
        uid = max(self.fake.users)
        self.assertEqual(self.fake.users[uid]["LoginId"], "zz_test_pls_demo_x_somu")
        password = (self.r / ".pls/test-users/dev-somu.password").read_text(encoding="utf-8").strip()
        key = (self.r / ".pls/test-users/dev-somu.key").read_text(encoding="utf-8").strip()
        self.assertEqual((self.fake.users[uid]["password"], self.fake.keys.get(key)), (password, uid))
        self.assertEqual(self.conns()["dev"]["keys"], {"admin": "env:T_ADMIN", "somu": "file:test-users/dev-somu.key"})
        g = self.fake.groups[374]
        self.assertEqual(g["GroupMembers"], ["User,7,False", "User,8,True", "Dept,3,False", f"User,{uid},False"])
        self.assertEqual((g["GroupName"], g["Body"]), ("zz_demo_総務", "role somu"))
        for secret in (password, key, ADMIN_KEY, "S3CRET"):
            self.assertNotIn(secret, out)
        ev = [json.loads(x) for f in sorted((self.r / "ops/log").glob("*.jsonl"))
              for x in f.read_text(encoding="utf-8").splitlines() if '"test-users"' in x][-1]
        self.assertEqual((ev["writes"], ev["metrics"]), (True, {"test_users_created": [uid], "group_members_added": [374]}))
        for secret in (password, key):
            self.assertNotIn(secret, json.dumps(ev))
        n = len(self.fake.calls)
        rc, out = self.run_pls("--env", "dev", "--yes")                 # second run: nothing left to write
        self.assertEqual((rc, self.writes(n)), (0, []), out)

    def test_stg_prod_and_sandboxes_are_refused_before_any_request(self):
        for env in ("stg", "prod", "sbx"):
            n = len(self.fake.calls)
            with self.assertRaisesRegex(pls.Fail, "only on a dev environment", msg=env):
                self.run_pls("--env", env, "--yes")
            self.assertEqual(self.fake.calls[n:], [], env)

    def test_no_write_without_allow_write(self):
        c = self.conns()
        c["dev"]["allow_write"] = False
        (self.r / ".pls/connections.json").write_text(json.dumps(c), encoding="utf-8")
        with self.assertRaisesRegex(pls.Fail, "REFUSED"):
            self.run_pls("--env", "dev", "--yes")
        self.assertEqual(self.writes(), [])

    def test_not_confirmed_writes_nothing(self):
        with self.assertRaisesRegex(pls.Fail, "not confirmed"):            # no --yes and no terminal
            self.run_pls("--env", "dev")
        self.assertEqual(self.writes(), [])
        self.assertFalse((self.r / ".pls/test-users").exists())

    def test_unverified_version_leaves_the_key_to_the_person(self):
        self.set_env("dev", pleasanter={"app": "1.6.0"})
        rc, out = self.run_pls("--env", "dev", "--yes")
        self.assertEqual(rc, 1, out)
        self.assertIn("PERSON STEP", out)
        self.assertNotIn("/users/createapikey", [p for _, p in self.fake.calls])
        self.assertNotIn("/users/authenticate?ReturnUrl=%2F", [p for _, p in self.fake.calls])
        self.assertFalse((self.r / ".pls/test-users/dev-somu.key").exists())
        self.assertNotIn("somu", self.conns()["dev"]["keys"])               # no reference to a key that does not exist
        uid = max(self.fake.users)
        self.assertIn(f"User,{uid},False", self.fake.groups[374]["GroupMembers"])

    def test_unknown_version_leaves_the_key_to_the_person(self):
        self.set_env("dev", pleasanter={})
        rc, out = self.run_pls("--env", "dev", "--yes")
        self.assertEqual(rc, 1, out)
        self.assertNotIn("/users/createapikey", [p for _, p in self.fake.calls])

    def test_another_key_for_the_role_is_never_replaced(self):
        c = self.conns()
        c["dev"]["keys"]["somu"] = "a1b2c3d4LITERALKEYTYPEDBYMISTAKE"       # a value that may be a secret
        (self.r / ".pls/connections.json").write_text(json.dumps(c), encoding="utf-8")
        with self.assertRaisesRegex(pls.Fail, "never replaces it") as cm:
            self.run_pls("--env", "dev", "--yes")
        self.assertNotIn("LITERALKEY", str(cm.exception))
        self.assertEqual((self.writes(), self.conns()["dev"]["keys"]["somu"]), ([], "a1b2c3d4LITERALKEYTYPEDBYMISTAKE"))

    def test_existing_user_without_its_password_here_is_refused(self):
        self.fake.users[500] = {"UserId": 500, "LoginId": "zz_test_pls_demo_x_somu", "password": "elsewhere"}
        with self.assertRaisesRegex(pls.Fail, "password is not in"):
            self.run_pls("--env", "dev", "--yes")
        self.assertEqual(self.writes(), [])

    def test_role_not_bound_is_refused(self):
        self.set_env("dev", principals={"admin": "User,7"})
        with self.assertRaisesRegex(pls.Fail, "not bound to a group"):
            self.run_pls("--env", "dev", "--yes")
        self.assertEqual(self.writes(), [])

    def test_group_with_child_groups_or_unknown_members_is_not_updated(self):
        for change in ({"GroupChildren": ["Group,9,"]}, {"GroupMembers": ["User,7,False", {"UserId": 8}]}):
            self.fake.groups[374].update(change)
            with self.assertRaises(pls.Fail, msg=change):
                self.run_pls("--env", "dev", "--yes")
            self.assertEqual(self.writes(), [], change)
            self.fake.groups[374].update({"GroupChildren": [], "GroupMembers": ["User,7,False"]})

    def test_group_changed_since_read_is_refused(self):
        self.fake.change_group_on_read = 2                                 # the person edits it before pls writes
        with self.assertRaisesRegex(pls.Fail, "changed since it was read"):
            self.run_pls("--env", "dev", "--yes")
        self.assertNotIn("/api/groups/374/update", [p for _, p in self.fake.calls])

    def test_a_member_lost_by_the_update_is_reported_with_the_list_before(self):
        self.fake.drop_member_on_update = True
        with self.assertRaisesRegex(pls.Fail, r"members before were \['User,7,False', 'User,8,True', 'Dept,3,False'\]"):
            self.run_pls("--env", "dev", "--yes")


    def test_roles_file_missing_is_refused(self):
        (self.r / "design/roles.json").unlink()
        with self.assertRaisesRegex(pls.Fail, "design/roles.json not found"):
            self.run_pls("--env", "dev", "--yes")
        self.assertEqual(self.fake.calls, [])

    def test_role_name_unusable_in_a_login_id_is_refused(self):
        (self.r / "design/roles.json").write_text(json.dumps({"roles": {"Somu-1": {"principal": "Group", "group_name": "g"}}}),
                                                  encoding="utf-8")
        with self.assertRaisesRegex(pls.Fail, "role name of a-z"):
            self.run_pls("--env", "dev", "--yes")
        self.assertEqual(self.writes(), [])

    def test_project_name_without_usable_characters_is_refused(self):
        with self.assertRaisesRegex(TU.TestUsersError, "no usable LoginId part"):
            TU.login_id("日本語", "somu")

    def test_several_users_with_the_login_id_are_refused(self):
        for uid in (500, 501):
            self.fake.users[uid] = {"UserId": uid, "LoginId": "zz_test_pls_demo_x_somu", "password": "x"}
        with self.assertRaisesRegex(pls.Fail, "2 users have the LoginId"):
            self.run_pls("--env", "dev", "--yes")
        self.assertEqual(self.writes(), [])

    def test_a_user_lookup_that_fails_or_answers_odd_ids_writes_nothing(self):
        for answer, msg in (((500, {"Message": "boom"}), "answered HTTP 500"),
                            ((200, {"Response": {"Data": [{"UserId": "x", "LoginId": "zz_test_pls_demo_x_somu"}]}}),
                             "not a number")):
            self.fake.answer["/api/users/get"] = answer
            with self.assertRaisesRegex(pls.Fail, msg):
                self.run_pls("--env", "dev", "--yes")
            self.assertEqual(self.writes(), [])

    def test_a_group_lookup_that_fails_or_finds_another_id_writes_nothing(self):
        self.fake.answer["/api/groups/get"] = (500, {"Message": "boom"})
        with self.assertRaisesRegex(pls.Fail, "reading group"):
            self.run_pls("--env", "dev", "--yes")
        del self.fake.answer["/api/groups/get"]
        self.set_env("dev", principals={"admin": "User,7", "somu": "Group,999"})
        with self.assertRaisesRegex(pls.Fail, "exactly the bound id 999"):
            self.run_pls("--env", "dev", "--yes")
        self.assertEqual(self.writes(), [])

    def test_a_refused_user_create_stops_before_the_group(self):
        self.fake.answer["/api/users/create"] = (403, {"StatusCode": 403, "Message": "forbidden"})
        with self.assertRaisesRegex(pls.Fail, "creating user zz_test_pls_demo_x_somu answered HTTP 403"):
            self.run_pls("--env", "dev", "--yes")
        self.assertNotIn("/api/groups/374/update", [p for _, p in self.fake.calls])
        self.assertTrue((self.r / ".pls/test-users/dev-somu.password").exists())     # kept for the next run

    def test_an_unanswered_user_create_says_to_run_again(self):
        real = H.Client.create_user

        def unanswered(self_, *a):
            raise H.UncertainOutcome("/api/users/create: no complete answer")
        H.Client.create_user = unanswered
        try:
            with self.assertRaisesRegex(pls.Fail, "run pls test-users --env dev again"):
                self.run_pls("--env", "dev", "--yes")
        finally:
            H.Client.create_user = real

    def test_a_key_reference_written_meanwhile_is_not_replaced(self):
        def person_edits():
            c = self.conns()
            c["dev"]["keys"]["somu"] = "env:PERSON_KEY"
            (self.r / ".pls/connections.json").write_text(json.dumps(c), encoding="utf-8")
        self.fake.on_key_issue = person_edits
        with self.assertRaisesRegex(pls.Fail, "set meanwhile") as cm:
            self.run_pls("--env", "dev", "--yes")
        self.assertNotIn("PERSON_KEY", str(cm.exception))
        self.assertEqual(self.conns()["dev"]["keys"]["somu"], "env:PERSON_KEY")

    def test_screens_that_do_not_answer_are_a_refusal(self):
        srv = serve(Fake())
        port = srv.server_address[1]
        srv.shutdown()
        srv.server_close()
        with self.assertRaisesRegex(TU.TestUsersError, "did not answer"):
            TU.ScreenSession(f"http://127.0.0.1:{port}", 2).call("/users/editapi")


    def test_the_create_request_never_makes_a_tenant_manager(self):
        self.assertEqual(self.run_pls("--env", "dev", "--yes")[0], 0)
        self.assertEqual(self.fake.user_bodies, [["LoginId", "Name", "Password"]])

    def test_an_existing_test_user_that_is_a_tenant_manager_is_refused(self):
        self.fake.users[500] = {"UserId": 500, "LoginId": "zz_test_pls_demo_x_somu", "password": "x", "tm": True}
        with self.assertRaisesRegex(pls.Fail, "tenant manager or disabled"):
            self.run_pls("--env", "dev", "--yes")
        self.assertEqual(self.writes(), [])

    def test_a_stale_key_is_reissued_only_after_the_confirmation(self):
        self.assertEqual(self.run_pls("--env", "dev", "--yes")[0], 0)
        c = self.conns()
        del c["dev"]["keys"]["somu"]
        (self.r / ".pls/connections.json").write_text(json.dumps(c), encoding="utf-8")
        (self.r / ".pls/test-users/dev-somu.key").write_text("STALEKEY" + "0" * 40 + "\n", encoding="utf-8")
        n = len(self.fake.calls)
        shown = io.StringIO()
        with contextlib.redirect_stdout(shown), self.assertRaisesRegex(pls.Fail, "not confirmed"):   # no --yes, no terminal
            pls.main(["test-users", "--env", "dev"])
        self.assertEqual(self.writes(n), [])
        self.assertIn("issue API key through the screens", shown.getvalue())      # the confirmation names the re-issue
        rc, out = self.run_pls("--env", "dev", "--yes")
        self.assertEqual(rc, 0, out)
        key = (self.r / ".pls/test-users/dev-somu.key").read_text(encoding="utf-8").strip()
        self.assertIn(key, self.fake.keys)

    def test_a_key_shaped_string_that_is_not_a_key_is_never_kept(self):
        self.fake.noise_token = True
        self.assertEqual(self.run_pls("--env", "dev", "--yes")[0], 0)
        key = (self.r / ".pls/test-users/dev-somu.key").read_text(encoding="utf-8").strip()
        self.assertTrue(key.startswith("ISSUED"), key[:6])

    def test_two_accepted_candidates_leave_the_key_to_the_person(self):
        self.fake.two_keys = True
        rc, out = self.run_pls("--env", "dev", "--yes")
        self.assertEqual(rc, 1, out)
        self.assertIn("PERSON STEP", out)
        self.assertFalse((self.r / ".pls/test-users/dev-somu.key").exists())

    def test_a_connections_file_outside_the_project_is_refused(self):
        other = Path(self.tmp.name) / "elsewhere" / "conn.json"
        other.parent.mkdir()
        other.write_text((self.r / ".pls/connections.json").read_text(encoding="utf-8"), encoding="utf-8")
        os.environ["PLS_CONNECTIONS"] = str(other)
        try:
            with self.assertRaisesRegex(pls.Fail, "not the project's .pls/connections.json"):
                self.run_pls("--env", "dev", "--yes")
        finally:
            os.environ.pop("PLS_CONNECTIONS")
        self.assertEqual(self.writes(), [])
        self.assertFalse((other.parent / "test-users").exists())

    def test_an_unanswered_group_update_is_read_back_and_a_loss_reported(self):
        real = H.Client.update_group

        def lossy_then_silent(self_, gid, name, body, members):
            real(self_, gid, name, body, members[1:])                       # written, but a member lost
            raise H.UncertainOutcome("/api/groups/374/update: no complete answer")
        H.Client.update_group = lossy_then_silent
        try:
            with self.assertRaisesRegex(pls.Fail, r"members before were \['User,7,False'"):
                self.run_pls("--env", "dev", "--yes")
        finally:
            H.Client.update_group = real

    def test_two_roles_sharing_one_group_both_join_it(self):
        roles = {"roles": {"somu": {"principal": "Group", "group_name": "zz_demo_総務"},
                           "somu2": {"principal": "Group", "group_name": "zz_demo_総務"}}}
        (self.r / "design/roles.json").write_text(json.dumps(roles, ensure_ascii=False), encoding="utf-8")
        self.set_env("dev", principals={"admin": "User,7", "somu": "Group,374", "somu2": "Group,374"})
        rc, out = self.run_pls("--env", "dev", "--yes")
        self.assertEqual(rc, 0, out)
        new = sorted(u for u in self.fake.users if u > 10000)
        self.assertEqual(self.fake.groups[374]["GroupMembers"][-2:], [f"User,{u},False" for u in new])


    def test_a_failed_read_back_after_an_unanswered_update_still_shows_the_list_before(self):
        real_update, real_call = H.Client.update_group, H.Client.call
        state = {"sent": False}

        def silent(self_, gid, name, body, members):
            real_update(self_, gid, name, body, members[1:])
            state["sent"] = True
            raise H.UncertainOutcome("/api/groups/374/update: no complete answer")

        def down_after_update(self_, path, body=None):
            if state["sent"] and path == "/api/groups/get":
                raise H.TransportError("cannot reach host: down")
            return real_call(self_, path, body)
        H.Client.update_group, H.Client.call = silent, down_after_update
        try:
            with self.assertRaisesRegex(pls.Fail, r"no read back \(TransportError.*members before were \['User,7,False'"):
                self.run_pls("--env", "dev", "--yes")
        finally:
            H.Client.update_group, H.Client.call = real_update, real_call

    def test_the_operators_own_key_in_a_key_file_is_refused(self):
        self.assertEqual(self.run_pls("--env", "dev", "--yes")[0], 0)
        (self.r / ".pls/test-users/dev-somu.key").write_text(ADMIN_KEY + "\n", encoding="utf-8")
        with self.assertRaisesRegex(pls.Fail, "operator's own key") as cm:
            self.run_pls("--env", "dev", "--yes")
        self.assertNotIn(ADMIN_KEY, str(cm.exception))

    def test_a_key_the_person_saved_is_used_and_its_reference_added(self):
        self.set_env("dev", pleasanter={"app": "1.6.0"})
        self.assertEqual(self.run_pls("--env", "dev", "--yes")[0], 1)
        uid = max(self.fake.users)
        person_key = "PERSONMADE" + "b" * 40
        self.fake.keys[person_key] = uid                                      # the person issued it in the UI
        (self.r / ".pls/test-users/dev-somu.key").write_text(person_key + "\n", encoding="utf-8")
        n = len(self.fake.calls)
        rc, out = self.run_pls("--env", "dev")                               # no Pleasanter write left: no confirmation
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.writes(n), [])
        self.assertEqual(self.conns()["dev"]["keys"]["somu"], "file:test-users/dev-somu.key")
        self.assertNotIn(person_key, out)

    def test_an_unverified_version_asks_no_confirmation_when_only_a_person_step_is_left(self):
        self.set_env("dev", pleasanter={"app": "1.6.0"})
        self.assertEqual(self.run_pls("--env", "dev", "--yes")[0], 1)
        n = len(self.fake.calls)
        rc, out = self.run_pls("--env", "dev")                               # no --yes, no terminal
        self.assertEqual((rc, self.writes(n)), (1, []), out)
        self.assertIn("PERSON STEP", out)

    def test_a_disabled_test_user_is_refused(self):
        self.fake.users[500] = {"UserId": 500, "LoginId": "zz_test_pls_demo_x_somu", "password": "x", "disabled": True}
        with self.assertRaisesRegex(pls.Fail, "tenant manager or disabled"):
            self.run_pls("--env", "dev", "--yes")
        self.assertEqual(self.writes(), [])

    def test_an_earlier_valid_key_on_the_page_is_not_taken_for_the_new_one(self):
        self.assertEqual(self.run_pls("--env", "dev", "--yes")[0], 0)
        old = (self.r / ".pls/test-users/dev-somu.key").read_text(encoding="utf-8").strip()
        self.fake.keep_old_keys = True
        (self.r / ".pls/test-users/dev-somu.key").write_text("STALEKEY" + "0" * 40 + "\n", encoding="utf-8")
        rc, out = self.run_pls("--env", "dev", "--yes")
        self.assertEqual(rc, 0, out)
        new = (self.r / ".pls/test-users/dev-somu.key").read_text(encoding="utf-8").strip()
        self.assertNotEqual(new, old)

    def test_the_screen_path_needs_the_kb_entry_and_a_verified_version(self):
        index = {"entries": {"D32": {"verified_on": ["1.5.2"]}}}
        self.assertTrue(TU.screen_path_verified(index, []))
        self.assertFalse(TU.screen_path_verified(index, ["D32"]))
        self.assertFalse(TU.screen_path_verified(index, None))                # version unknown
        self.assertFalse(TU.screen_path_verified({"entries": {}}, []))        # entry removed from the KB
        self.assertFalse(TU.screen_path_verified(None, None))

    def test_a_group_read_without_name_or_body_is_not_updated(self):
        del self.fake.groups[374]["Body"]
        with self.assertRaisesRegex(pls.Fail, "no GroupName or Body"):
            self.run_pls("--env", "dev", "--yes")
        self.assertNotIn("/api/groups/374/update", [p for _, p in self.fake.calls])


if __name__ == "__main__":
    unittest.main()
