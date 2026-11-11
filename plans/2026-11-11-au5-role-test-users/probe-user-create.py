"""Probe for ADR-0018 (AU5): can a dev environment get a test user, and that user an API key, without a person?

Run by the operator (never by an agent), in a terminal, from a project folder whose environments.json declares the
environment with role "dev" (not a sandbox) and whose .pls/connections.json allows writes to it with a
tenant-administrator key:

    python <framework>/plans/2026-11-11-au5-role-test-users/probe-user-create.py --env dev
    python <framework>/plans/2026-11-11-au5-role-test-users/probe-user-create.py --env dev --api-only

What it does on that environment (users are tenant-wide objects):
  Stage A — documented API, operator's key:
    1. looks up a fresh LoginId zz_probe_user_<timestamp>; stops if a user with it already exists;
    2. creates the user with a random password that exists only in this process (POST /api/users/create);
    3. reads it back by LoginId (POST /api/users/get) and reports the field names and a few flags;
    4. tries a second create with the same LoginId (does the server refuse it?).
  Stage B — undocumented screen endpoints, skipped with --api-only or when stage A did not give exactly one user:
    5. reads the login form's field names (GET /users/login; names only, no values printed);
    6. logs in as the probe user (POST /users/authenticate) with that password;
    7. calls the API with that session and no key (does the API accept a session?);
    8. issues an API key for the probe user (POST /users/createapikey), finds candidate keys in the answer and in the
       API settings screen (GET /users/editapi), and checks each candidate against the API. Keys are never printed.
  Cleanup — in every case, also after a failure or Ctrl+C:
    9. looks the LoginId up again with the operator's key and deletes only the users that lookup returns with exactly
       that LoginId (POST /api/users/{id}/delete), then looks again. When the cleanup lookup fails nothing is deleted.
   10. checks each candidate key of step 8 against the API again (read only): does a key outlive its user?

It prints one JSON result: HTTP statuses, the server's Id/StatusCode/Message, field names and form field names.
No password, no key, no cookie; the server URL and host are replaced by <server>. Paste that output back.
If `left_after_delete` is not [] (or is "unknown"), or `unconfirmed` is not [], check user zz_probe_user_… (and the
ids in `unconfirmed`) by hand in the UI and delete the probe user (also from the trash box). If
`keys_after_delete` shows a key still accepted, tell the framework owner: the key outlives its user. The probe never
sends TenantManager; stage B is skipped if the read-back shows the user is a tenant manager.

A one-off script outside `pls`: it is not in the write-path inventory (test_write_guards.py) and leaves no run-log
line. Retire it once the KB entry exists.
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import re
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "pls"))
import pls_http as H  # noqa: E402

FLAG_FIELDS = ("Disabled", "Lockout", "TenantManager", "ServiceManager", "AllowCreationAtTopSite", "AllowApi",
               "LockoutCounter", "PasswordExpirationTime", "PasswordChangeTime")
KEY_SHAPE = re.compile(r"[A-Za-z0-9]{32,}")


class ProbeError(Exception):
    pass


class InputNames(HTMLParser):
    """Collects <input>/<select>/<textarea> names, types and values of a page (values are never printed)."""

    def __init__(self):
        super().__init__()
        self.fields: list[dict] = []

    def handle_starttag(self, tag, attrs):
        if tag in ("input", "select", "textarea"):
            a = dict(attrs)
            if a.get("name"):
                self.fields.append({"name": a["name"], "type": a.get("type") or tag, "value": a.get("value") or ""})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--env", default="dev")
    ap.add_argument("--api-only", action="store_true", help="stage A only: no login as the probe user, no key issued")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")       # the result survives a redirect on a cp932 console
    root = Path.cwd()
    envs = json.loads((root / "environments.json").read_text(encoding="utf-8-sig"))["envs"]
    env_conf = envs.get(a.env) or {}
    if env_conf.get("role") != "dev" or env_conf.get("sandbox_of") or env_conf.get("connection"):
        print(f"REFUSED: the probe runs only on a role dev environment that is not a sandbox ({a.env})", file=sys.stderr)
        return 1
    conn = H.load_connection(root, a.env)
    H.assert_writable(env_conf, conn, a.env)
    if not sys.stdin.isatty():
        print("REFUSED: run it in a terminal; it asks for a typed confirmation", file=sys.stderr)
        return 1
    login = "zz_probe_user_" + datetime.now().strftime("%Y%m%d%H%M%S")
    what = "creates and deletes user" + ("" if a.api_only else ", logs in as it and issues its API key,")
    if input(f"{what} '{login}' on {a.env}; type {a.env} to confirm: ").strip() != a.env:
        print("not confirmed — nothing written")
        return 1
    url = conn["url"].rstrip("/")
    timeout = H.conn_timeout(conn)
    admin = H.Client(url, H.resolve_key(conn, None), timeout=timeout)
    password = secrets.token_urlsafe(18) + "aA1!"     # lives only in this process

    parts = urlparse(url)
    hidden = [x for x in (url, parts.netloc, parts.hostname) if x]
    secret_values = [password, admin.key]             # candidate keys are added when found

    def clean(s: str) -> str:
        """No server address, password or key in the result: it is pasted back and may reach the repository."""
        for x in secret_values:
            if x:
                s = s.replace(x, "<secret>")
        for x in hidden:
            s = s.replace(x, "<server>")
        return s[:300]

    def short(js) -> dict | None:
        if not isinstance(js, dict):
            return None
        return {k: (clean(v) if isinstance(v, str) else v) for k, v in js.items() if k in ("Id", "StatusCode", "Message")}

    def find() -> list[dict]:
        st, js, _ = admin.call("/api/users/get", {"View": {"ColumnFilterHash": {"LoginId": login}}})
        if st != 200 or not isinstance(js, dict):
            raise ProbeError(f"/api/users/get: HTTP {st}")
        rows = (js.get("Response") or {}).get("Data") or []
        return [r for r in rows if isinstance(r, dict) and r.get("LoginId") == login]

    def ids_of(rows: list[dict]) -> list[int]:
        out = []
        for r in rows:
            uid = r.get("UserId")
            if isinstance(uid, str) and uid.isdigit():
                uid = int(uid)
            if isinstance(uid, int) and not isinstance(uid, bool) and uid > 0:
                out.append(uid)
            else:
                odd.append(repr(uid)[:40])                 # reported, never deleted
        return sorted(out)

    def create(name: str) -> dict:
        st, js, _ = admin.call("/api/users/create", {"LoginId": login, "Name": name, "Password": password})
        if isinstance(js, dict) and isinstance(js.get("Id"), int) and js["Id"] > 0 and st == 200:
            answered.add(js["Id"])
        return {"status": st, "body": short(js), "not_json": js is None}

    out: dict = {"probe": "user-create", "env": a.env, "login_id": login, "api_only": a.api_only,
                 "at": datetime.now().astimezone().isoformat()}
    answered: set[int] = set()
    odd: list[str] = []
    issued_keys: list[str] = []                        # candidate keys of stage B, never printed
    stage = "before"
    try:
        if find():
            out["before"] = "exists"
            raise ProbeError("a user with the probe LoginId already exists — nothing created")
        out["before"] = []
        stage = "create"
        out["create"] = create("probe user (ai-dlc-pleasanter ADR-0018)")
        stage = "after_create"
        rows = find()
        out["after_create"] = ids_of(rows)
        if rows:
            r = rows[0]
            out["fields"] = sorted(str(k) for k in r)
            out["flags"] = {k: r[k] for k in FLAG_FIELDS if k in r and isinstance(r[k], (bool, int, type(None)))}
            out["flags_text_present"] = sorted(k for k in FLAG_FIELDS if k in r and isinstance(r[k], str))
        stage = "create_duplicate"
        out["create_duplicate"] = create("probe duplicate")
        stage = "after_duplicate"
        out["after_duplicate"] = ids_of(find())
        if not a.api_only:
            if len(out["after_duplicate"]) != 1:
                out["session"] = "skipped: not exactly one probe user"
            elif (out.get("flags") or {}).get("TenantManager") or "TenantManager" in out.get("flags_text_present", []):
                out["session"] = "skipped: the read-back does not show the probe user as a plain user (TenantManager)"
            else:
                stage = "session"
                out["session"] = {}                    # filled in place: what ran is kept after a failure
                session_stage(out["session"], issued_keys, url, timeout, login, password, secret_values, clean, short)
    except BaseException as ex:                        # also Ctrl+C: clean up and print what is known
        out["error"] = {"stage": stage, "type": type(ex).__name__, "message": clean(str(ex))}
    finally:
        out["delete"] = []
        if stage != "before":                          # nothing was sent to create before that stage
            try:
                targets = ids_of(find())               # only users with exactly the probe's LoginId
            except BaseException as ex:
                targets = []                           # nothing confirmed: delete nothing
                out["delete_lookup_error"] = clean(f"{type(ex).__name__}: {ex}") + " — nothing deleted"
            out["create_answer_ids"] = sorted(answered)
            seen = set(out.get("after_duplicate") or out.get("after_create") or [])
            out["create_answer_is_user_id"] = bool(answered) and answered <= seen
            out["unconfirmed"] = sorted(answered - set(targets))   # check these ids in the UI; not deleted
            for uid in targets:
                try:
                    st, js, _ = admin.call(f"/api/users/{uid}/delete")
                    out["delete"].append({"id": uid, "status": st, "body": short(js)})
                except BaseException as ex:
                    out["delete"].append({"id": uid, "error": clean(f"{type(ex).__name__}: {ex}")})
            try:
                out["left_after_delete"] = ids_of(find())
            except BaseException as ex:
                out["left_after_delete"] = clean(f"unknown ({type(ex).__name__}: {ex}) — check user {login}")
            if issued_keys:
                out["keys_after_delete"] = []
                for i, cand in enumerate(issued_keys):
                    try:
                        stc, jsc, _ = H.Client(url, cand, timeout=timeout).call(
                            "/api/users/get", {"View": {"ColumnFilterHash": {"LoginId": login}}})
                        out["keys_after_delete"].append({"candidate": i, "status": stc, "body": short(jsc)})
                    except BaseException as ex:
                        out["keys_after_delete"].append({"candidate": i, "error": clean(f"{type(ex).__name__}: {ex}")})
        if odd:
            out["odd_user_ids"] = odd
        print(json.dumps(out, ensure_ascii=False, indent=2))
    clean_end = out.get("left_after_delete") in ([], None) and not out.get("unconfirmed") and "delete_lookup_error" not in out
    return 0 if "error" not in out and clean_end else 1


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Stage B never follows a redirect (e.g. to an SSO host whose name would not be scrubbed): the 3xx is the answer."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def session_stage(res, issued_keys, url, timeout, login, password, secret_values, clean, short) -> None:
    """Stage B: log in as the probe user through the screens, try the API with the session, issue and check a key.

    `res` is filled step by step so that a failure keeps what already ran; candidate keys go to `issued_keys`."""
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar), NoRedirect())

    def send(path: str, data: bytes | None = None, headers: dict | None = None) -> tuple[int, str]:
        req = urllib.request.Request(url + path, data=data, method="POST" if data is not None else "GET",
                                     headers=headers or {})
        try:
            with opener.open(req, timeout=timeout) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            with e:
                return e.code, e.read().decode("utf-8", "replace")

    def cookie_values() -> None:
        for ck in jar:
            if ck.value and ck.value not in secret_values:
                secret_values.append(ck.value)

    ajax = {"X-Requested-With": "XMLHttpRequest"}

    # 5. login form field names
    st, page = send("/users/login")
    parser = InputNames()
    parser.feed(page)
    res["login_page_status"] = st
    res["login_form_fields"] = [{"name": f["name"], "type": f["type"]} for f in parser.fields]
    # Field names observed on dev 1.5.2 (first run, 2026-11-11 19:03): the page also has a hidden `LoginId` and the
    # password-change fields `Users_ChangedPassword*`, so the login fields are picked by their exact names.
    user_f = [f["name"] for f in parser.fields if f["name"] == "Users_LoginId" and f["type"] == "text"]
    pass_f = [f["name"] for f in parser.fields if f["name"] == "Users_Password" and f["type"] == "password"]
    if len(user_f) != 1 or len(pass_f) != 1:
        res["login"] = "skipped: the login form has no single LoginId / Password field"
        return
    # Only the login fields and ReturnUrl: the page's other hidden fields (UserId, LoginId, GroupIds …) describe the
    # page, not the login, and sending them could be read as something else.
    form = {f["name"]: f["value"] for f in parser.fields if f["name"] == "ReturnUrl"}
    form[user_f[0]] = login
    form[pass_f[0]] = password

    # 6. login
    st, text = send("/users/authenticate?ReturnUrl=%2F", urllib.parse.urlencode(form).encode("utf-8"),
                    {**ajax, "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})
    cookie_values()
    res["authenticate"] = {"status": st, "answer": clean(text), "cookies": sorted(ck.name for ck in jar)}

    # 7. API with the session and no key
    body = json.dumps({"ApiVersion": 1.1, "View": {"ColumnFilterHash": {"LoginId": login}}}).encode("utf-8")
    st, text = send("/api/users/get", body, {"Content-Type": "application/json; charset=utf-8"})
    try:
        js = json.loads(text)
    except json.JSONDecodeError:
        js = None
    res["api_with_session_no_key"] = {"status": st, "body": short(js), "not_json": js is None}

    # 8. issue a key and check candidates against the API
    _, before = send("/users/editapi")
    known = set(KEY_SHAPE.findall(before))
    st, issued = send("/users/createapikey", b"", ajax)
    _, after = send("/users/editapi")
    cookie_values()
    cands = [t for t in dict.fromkeys(KEY_SHAPE.findall(issued) + KEY_SHAPE.findall(after))
             if t not in known and t not in secret_values][:5]
    secret_values.extend(cands)                        # before anything of the answer is printed
    issued_keys.extend(cands)
    try:
        cmds = json.loads(issued)
        shape = [{"Method": c.get("Method"), "Target": clean(str(c.get("Target")))} for c in cmds if isinstance(c, dict)]
    except (json.JSONDecodeError, TypeError, AttributeError):
        shape = "not a JSON command list"
    res["createapikey"] = {"status": st, "answer_length": len(issued), "answer_shape": shape,
                           "candidates": len(cands)}
    checks = []
    for i, cand in enumerate(cands):
        stc, jsc, _ = H.Client(url, cand, timeout=timeout).call(
            "/api/users/get", {"View": {"ColumnFilterHash": {"LoginId": login}}})
        checks.append({"candidate": i, "status": stc, "body": short(jsc)})
    res["key_checks"] = checks
    res["key_accepted"] = any(c["status"] == 200 and (c["body"] or {}).get("StatusCode") == 200 for c in checks)
    # A refusal other than "unauthenticated" (e.g. 403: a user who is not tenant manager may not read users) can still
    # mean the key is valid: the statuses and messages above are the evidence, key_accepted is only the clear case.
    send("/users/logout")


if __name__ == "__main__":
    sys.exit(main())
