"""Test users for role tests on dev (ADR-0018 option C, ADR-0019 option B): `pls test-users --env <dev env>`.

For each role of design/roles.json with principal "Group" that `pls principals` bound on the environment:
  1. a user `zz_test_<project>_<role>` is created (`/api/users/create`, tenant administrator key) with a random
     password kept only in the operator's `.pls/test-users/<env>-<role>.password` (CLAUDE.md Mandatory 1 exception);
  2. its API key is issued through the screens (`/users/authenticate`, `/users/createapikey`; KB D32) and kept in
     `.pls/test-users/<env>-<role>.key` — only on a Pleasanter version where KB D32 is verified; otherwise the
     person issues it (ADR-0018 fallback B) and runs the command again;
  3. `keys.<role>` is added to `.pls/connections.json` when the role has no key yet (never replaced);
  4. the user joins the role's group: read, add, write, check (ADR-0019 B) — the read list with every flag,
     `GroupName` and `Body` as read, `UpdatedTime`/`Ver` re-read just before the write.
An existing user with the test LoginId is written to (joined to the group) only after this machine proves it is the
one pls created here: its key file, or a key issued now by logging in with its stored password, is accepted by the
API. A password file alone does not prove it (the user may have been deleted and made again by someone else).
Nothing of a password, key or cookie is printed or logged. Removal: `--remove` (pls_test_users_removal); rotation is
not built (tech debt TD-24).
"""
from __future__ import annotations

import http.cookiejar
import json
import os
import re
import secrets
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROLE_NAME = re.compile(r"^[a-z0-9_]+$")
MEMBER = re.compile(r"^(User|Dept),(\d+),(True|False)$")
KEY_SHAPE = re.compile(r"[A-Za-z0-9]{32,}")
KB_ENTRY = "D32"                                      # screen login and key issue, KB behaviours.md


class TestUsersError(Exception):
    pass


def screen_path_verified(index, unverified: list | None) -> bool:
    """True only when KB entry D32 exists and is verified on the environment's version (a missing entry or an
    unknown version is never treated as verified)."""
    entries = index.get("entries") if isinstance(index, dict) else None
    return isinstance(entries, dict) and KB_ENTRY in entries and unverified is not None and KB_ENTRY not in unverified


def login_id(project: str, role: str) -> str:
    slug = re.sub(r"[^a-z0-9_]", "", project.lower().replace("-", "_"))
    if not slug:
        raise TestUsersError(f"the project folder name {project!r} gives no usable LoginId part (letters, digits, _)")
    return f"zz_test_{slug}_{role}"


def files(conn_dir: Path, env: str, role: str) -> tuple[Path, Path, str]:
    """(password file, key file, key reference for connections.json) of one role."""
    d = conn_dir / "test-users"
    return d / f"{env}-{role}.password", d / f"{env}-{role}.key", f"file:test-users/{env}-{role}.key"


def write_secret(p: Path, value: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(value + "\n", encoding="utf-8", newline="\n")
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass


def read_secret(p: Path) -> str | None:
    try:
        v = p.read_text(encoding="utf-8-sig").strip()
    except OSError:
        return None
    return v or None


def as_id(v) -> int | None:
    if isinstance(v, str) and v.isdigit():
        v = int(v)
    return v if isinstance(v, int) and not isinstance(v, bool) and v > 0 else None


def users_with_login(client, login: str) -> list[int]:
    """Ids of the users with exactly this LoginId. A test user that reads back as a tenant manager or disabled is
    refused: pls never makes or uses such a user for role tests."""
    st, js, _ = client.call("/api/users/get", {"View": {"ColumnFilterHash": {"LoginId": login}}})
    if st != 200 or not isinstance(js, dict):
        raise TestUsersError(f"looking up user {login} answered HTTP {st} — nothing written")
    rows = [x for x in (js.get("Response") or {}).get("Data") or [] if isinstance(x, dict) and x.get("LoginId") == login]
    ids = [as_id(x.get("UserId")) for x in rows]
    if None in ids:
        raise TestUsersError(f"user {login}: an id the lookup returned is not a number — check it in Pleasanter")
    if any(x.get("TenantManager") is True or x.get("Disabled") is True for x in rows):
        raise TestUsersError(f"user {login} is a tenant manager or disabled — not a test user pls uses; check it in "
                             "Pleasanter")
    return sorted(ids)


def key_works(client_for, login: str, key: str) -> bool:
    """True when the API accepts `key` (a read of the key's own user, allowed to a plain user on 1.5.2, KB D32)."""
    st, js, _ = client_for(key).call("/api/users/get", {"View": {"ColumnFilterHash": {"LoginId": login}}})
    return st == 200 and isinstance(js, dict) and js.get("StatusCode") == 200


def read_group(client, name: str, gid: int) -> dict:
    """The group record of `gid`, found by its exact name; refused unless its members are in a known shape."""
    st, js, _ = client.call("/api/groups/get", {"View": {"ColumnFilterHash": {"GroupName": name}}})
    if st != 200 or not isinstance(js, dict):
        raise TestUsersError(f"reading group '{name}' answered HTTP {st} — nothing written")
    rows = [x for x in (js.get("Response") or {}).get("Data") or [] if isinstance(x, dict) and x.get("GroupName") == name]
    if [as_id(x.get("GroupId")) for x in rows] != [gid]:
        raise TestUsersError(f"group '{name}': the lookup does not find exactly the bound id {gid} — run pls principals "
                             f"--env <env> and check the groups with that name")
    g = rows[0]
    members, children = g.get("GroupMembers"), g.get("GroupChildren")
    if not isinstance(members, list) or not all(isinstance(m, str) and MEMBER.match(m) for m in members):
        raise TestUsersError(f"group '{name}' ({gid}): members are not in the known form 'User|Dept,<id>,True|False' — "
                             "nothing changed; add the test user in the UI")
    if children not in ([], None):
        raise TestUsersError(f"group '{name}' ({gid}) has child groups — pls does not update it; add the test user in the UI")
    return g


def is_member(group: dict, uid: int) -> bool:
    return any(MEMBER.match(m).group(1, 2) == ("User", str(uid)) for m in group["GroupMembers"])


class ScreenSession:
    """The Pleasanter screens as a logged-in user (not a documented API; KB D32, verified on the versions it lists).
    Redirects are not followed; nothing of the session is ever printed."""

    def __init__(self, url: str, timeout: float, opener=None):
        self.base = url.rstrip("/")
        self.timeout = timeout
        self.jar = http.cookiejar.CookieJar()

        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **k):
                return None
        self.opener = opener or urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar), NoRedirect())

    def call(self, path: str, form: dict | None = None) -> tuple[int, str]:
        data = None if form is None else urllib.parse.urlencode(form).encode("utf-8")
        headers = {"X-Requested-With": "XMLHttpRequest"}
        if data is not None:
            headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
        req = urllib.request.Request(self.base + path, data=data, method="POST" if data is not None else "GET",
                                     headers=headers)
        try:
            with self.opener.open(req, timeout=self.timeout) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            with e:
                return e.code, ""
        except (urllib.error.URLError, OSError) as e:
            raise TestUsersError(f"the screens of {self.base} did not answer ({type(e).__name__})")

    def login(self, login: str, password: str) -> bool:
        st, text = self.call("/users/authenticate?ReturnUrl=%2F",
                             {"Users_LoginId": login, "Users_Password": password, "ReturnUrl": ""})
        try:
            cmds = json.loads(text)
        except ValueError:
            return False
        return st == 200 and isinstance(cmds, list) and any(isinstance(c, dict) and c.get("Method") == "Href" for c in cmds)

    def issue_api_key(self, accepted) -> str | None:
        """Issues a key and returns the one candidate `accepted(candidate)` confirms; None when none is confirmed."""
        _, before = self.call("/users/editapi")
        known = set(KEY_SHAPE.findall(before))
        st, answer = self.call("/users/createapikey", {})
        if st != 200:
            return None
        _, after = self.call("/users/editapi")
        cands = [t for t in dict.fromkeys(KEY_SHAPE.findall(answer) + KEY_SHAPE.findall(after)) if t not in known][:5]
        good = [t for t in cands if accepted(t)]
        return good[0] if len(good) == 1 else None

    def logout(self) -> None:
        try:
            self.call("/users/logout")
        except TestUsersError:
            pass


def plan_roles(roles: dict, principals: dict, conn: dict, conn_dir: Path, project: str, env: str, client,
               client_for) -> list[dict]:
    """One entry per Group role: what exists and what must be written. Refuses before any write. A key file counts
    only when the API accepts its key now, so every key issue is known (and confirmed) before anything is written."""
    out = []
    keys = conn.get("keys") or {}
    for role, spec in sorted(roles.items()):
        if not isinstance(spec, dict) or spec.get("principal") != "Group":
            continue
        if not ROLE_NAME.match(role):
            raise TestUsersError(f"role '{role}': a test user needs a role name of a-z, 0-9 and _ — nothing written")
        bound = str(principals.get(role) or "")
        m = re.fullmatch(r"Group,(\d+)", bound)
        name = spec.get("group_name")
        if not m or not isinstance(name, str) or not name:
            raise TestUsersError(f"role '{role}' is not bound to a group on {env} ({bound or 'not bound'}) — run "
                                 f"pls principals --env {env} first; nothing written")
        gid = int(m.group(1))
        pw_file, key_file, ref = files(conn_dir, env, role)
        if keys.get(role) not in (None, ref):              # the value may be a key typed by mistake: never shown
            raise TestUsersError(f"role '{role}': the connections file already names another key for it — pls never "
                                 "replaces it; nothing written")
        login = login_id(project, role)
        ids = users_with_login(client, login)
        if len(ids) > 1:
            raise TestUsersError(f"{len(ids)} users have the LoginId {login} — check them in Pleasanter; nothing written")
        if ids and not read_secret(pw_file):
            raise TestUsersError(f"user {login} exists but its password is not in {pw_file} on this machine — delete the "
                                 "user in Pleasanter (also from the trash box) or restore the file; nothing written")
        key = read_secret(key_file) if ids else None
        if key and key == client.key:
            raise TestUsersError(f"role '{role}': {key_file} holds the operator's own key, not the test user's — delete "
                                 "the file and run pls test-users again; nothing written")
        group = read_group(client, name, gid)
        out.append({"role": role, "login": login, "uid": ids[0] if ids else None, "gid": gid, "group_name": name,
                    "group": group, "pw_file": pw_file, "key_file": key_file, "ref": ref,
                    "key_ok": bool(key) and key_works(client_for, login, key), "add_ref": keys.get(role) is None,
                    "join_planned": not ids or not is_member(group, ids[0])})
    return out


def pending(e: dict, may_issue: bool) -> list[str]:
    """The Pleasanter writes one planned role needs (shown in the confirmation). A key a person must issue is not a
    write of pls and is reported as a person step instead."""
    w = ["create user"] if e["uid"] is None else []
    if not e["key_ok"] and may_issue:
        w.append("issue API key through the screens")
    if e["join_planned"]:
        w.append(f"join group '{e['group_name']}'")
    return w


def write_test_users(entries: list[dict], client, client_for, screens, may_issue: bool, add_key_ref, log) -> list[str]:
    """Writes for the planned (and confirmed) roles. Returns the person steps left (fallback B); raises on a refusal."""
    left = []
    for e in entries:
        role, login = e["role"], e["login"]
        created_now = e["uid"] is None
        if created_now:
            password = secrets.token_urlsafe(18) + "aA1!"
            write_secret(e["pw_file"], password)                 # first: an unanswered create keeps the password
            st, uid, text = client.create_user(login, f"pls test user: role {role}", password)
            again = users_with_login(client, login)
            if st != 200 or not uid or again != [uid]:
                raise TestUsersError(f"{role}: creating user {login} answered HTTP {st} {text}; the lookup found {again} "
                                     "— check the user in Pleasanter; nothing is retried")
            e["uid"] = uid
            log(test_users_created=uid)
            print(f"{role}: user {login} created (User,{uid})")
        uid = e["uid"]
        if not e["key_ok"]:                                      # planned and confirmed; never decided here
            key, why = issue_test_user_key(e, client_for, screens) if may_issue else (None, "not verified on this version")
            if key:
                write_secret(e["key_file"], key)
                e["key_ok"] = True
                print(f"{role}: API key of {login} issued and saved in {e['key_file']}")
            else:
                left.append(f"{role}: no API key for {login} ({why}) — log out of Pleasanter first, then log in as "
                            f"{login} (password in {e['pw_file']}), User > API settings > Create, save the key in "
                            f"{e['key_file']}, then run pls test-users again")
        if e["key_ok"] and e["add_ref"]:
            add_key_ref(role, e["ref"])
            e["add_ref"] = False
            print(f"{role}: connections file keys.{role} = {e['ref']}")
        if e["join_planned"] and not (created_now or e["key_ok"]):
            left.append(f"{role}: user {login} (User,{uid}) was not joined to group '{e['group_name']}' — without a "
                        "working key this machine cannot prove it is the user pls created here; issue its key as the "
                        "line above says and run pls test-users again. If you cannot log in as it with the password "
                        "in the file, it is someone else's user with the same LoginId: check it in Pleasanter")
        elif e["join_planned"]:
            add_test_user_to_group(client, e, uid, log)
        elif not is_member(e["group"], uid):
            left.append(f"{role}: User,{uid} is no longer a member of group '{e['group_name']}' (changed since the "
                        "confirmation) — run pls test-users again")
        for other in entries:                                    # roles sharing this group see the new member list
            if other is not e and other["gid"] == e["gid"]:
                other["group"] = read_group(client, other["group_name"], other["gid"])
    return left


def issue_test_user_key(e: dict, client_for, screens) -> tuple[str | None, str]:
    """(key, reason when none): log in as the test user through the screens and issue a key the API accepts."""
    s = screens()
    try:
        if not s.login(e["login"], read_secret(e["pw_file"]) or ""):
            return None, "logging in through the screens failed"
        key = s.issue_api_key(lambda k: key_works(client_for, e["login"], k))
        return key, "" if key else "not exactly one issued key was confirmed by the API"
    finally:
        s.logout()


def add_test_user_to_group(client, e: dict, uid: int, log) -> None:
    """ADR-0019 B: read, add, write, check. Never removes a member, changes a flag, the name or the Body. An update
    without a complete answer is read back and checked the same way."""
    g0 = e["group"]
    if is_member(g0, uid):
        print(f"{e['role']}: User,{uid} already a member of group '{e['group_name']}'")
        return
    g = read_group(client, e["group_name"], e["gid"])
    for f in ("UpdatedTime", "Ver"):
        if g.get(f) != g0.get(f):
            raise TestUsersError(f"group '{e['group_name']}' changed since it was read ({f}) — nothing written; run "
                                 "pls test-users again")
    if not isinstance(g.get("GroupName"), str) or not isinstance(g.get("Body"), str):
        raise TestUsersError(f"group '{e['group_name']}' ({e['gid']}): the read has no GroupName or Body to send back "
                             "unchanged — nothing written; add the test user in the UI")
    before = list(g["GroupMembers"])
    try:
        st, text = client.update_group(e["gid"], g.get("GroupName"), g.get("Body"), before + [f"User,{uid},False"])
    except Exception as ex:                    # noqa: BLE001 — UncertainOutcome: the server may have written
        st, text = None, f"no complete answer ({type(ex).__name__})"
    try:
        after = read_group(client, e["group_name"], e["gid"])["GroupMembers"]
        why = ""
    except Exception as ex:                    # noqa: BLE001 — also a transport failure: the earlier list is still shown
        after, why = None, f"no read back ({type(ex).__name__}: {ex})"
    if st != 200 or after is None or not set(before) <= set(after) or f"User,{uid},False" not in after:
        raise TestUsersError(f"group '{e['group_name']}' ({e['gid']}): the update answered {st or ''} {text} and the read "
                             f"back is {after if after is not None else why} — the members before were {before}; "
                             "restore them in the UI if one is missing")
    log(group_members_added=e["gid"])
    print(f"{e['role']}: User,{uid} added to group '{e['group_name']}' (members before: {len(before)})")
