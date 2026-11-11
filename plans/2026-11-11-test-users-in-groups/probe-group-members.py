"""Probe for ADR-0019: can the API read a group's members, and how does a group update treat them?

Run by the operator (never by an agent), in a terminal, from a project folder whose environments.json declares the
environment with role "dev" (not a sandbox) and the operator as `principals.admin` ("User,<id>"), and whose
.pls/connections.json allows writes to it with a tenant-administrator key:

    python <framework>/plans/2026-11-11-test-users-in-groups/probe-group-members.py --env dev

What it does on that environment (users and groups are tenant-wide objects); it touches only a probe user
zz_probe_user_<timestamp> and a probe group zz_probe_group_<timestamp> that it creates itself:
  1. checks that neither name exists; creates the user (random password, never used, never printed) and the group
     with one member, the operator; confirms both ids by a lookup;
  2. reads the group (POST /api/groups/get, by name, else every page matched by GroupId) and reports its field names,
     its GroupName and Body (probe text), and every field whose name contains "Member" or "Children" — values only
     when they are ids or "User|Dept|Group,<id>[,True|False]" strings; of anything else only keys, ids and flags;
  3. update with GroupMembers = operator + probe user as group administrator (True) → read: is the flag kept?
  4. update with only Body (no GroupName, no GroupMembers) → read: are the name and members kept?
  5. update with GroupName and GroupMembers = probe user only (no Body) → read: is the operator removed (list
     replaced), and is Body kept?
  6. deletes the probe user → read: does the group drop it?
  Cleanup — in every case, also after a failure or Ctrl+C: deletes the probe group by its confirmed id and any group
  with exactly the probe name, and any user with exactly the probe LoginId; then looks again.
If the read shows no member (or an empty member field), the probe asks the operator after each step to look at the group in the UI and
type the member ids shown (the operator id and the probe user id are printed in the question).

It prints one JSON result: HTTP statuses, the server's Id/StatusCode/Message, field names, member fields, ids.
No password, no key; the server URL and host are replaced by <server>. Paste that output back.
If `left_after_delete` shows anything left, "unknown", or ids in `unconfirmed` / `odd_ids`, check the probe group /
user (and those ids) by hand in the UI and delete what the probe created.

A one-off script outside `pls`: it is not in the write-path inventory (test_write_guards.py) and leaves no run-log
line. Retire it once the KB entry exists.
"""
from __future__ import annotations

import argparse
import json
import re
import secrets
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "pls"))
import pls_http as H  # noqa: E402

MAX_PAGES = 50


class ProbeError(Exception):
    pass


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--env", default="dev")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")       # the result survives a redirect on a cp932 console
    root = Path.cwd()
    envs = json.loads((root / "environments.json").read_text(encoding="utf-8-sig"))["envs"]
    env_conf = envs.get(a.env) or {}
    if env_conf.get("role") != "dev" or env_conf.get("sandbox_of") or env_conf.get("connection"):
        print(f"REFUSED: the probe runs only on a role dev environment that is not a sandbox ({a.env})", file=sys.stderr)
        return 1
    op = str((env_conf.get("principals") or {}).get("admin") or "")
    if not re.fullmatch(r"User,\d+", op):
        print(f"REFUSED: envs.{a.env}.principals.admin must be 'User,<id>' (is {op or 'not set'})", file=sys.stderr)
        return 1
    op_id = int(op.split(",")[1])
    conn = H.load_connection(root, a.env)
    H.assert_writable(env_conf, conn, a.env)
    if not sys.stdin.isatty():
        print("REFUSED: run it in a terminal; it asks for a typed confirmation", file=sys.stderr)
        return 1
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    login, gname = "zz_probe_user_" + ts, "zz_probe_group_" + ts
    if input(f"creates user '{login}' and group '{gname}' (member: operator {op}), updates and deletes them on "
             f"{a.env}; type {a.env} to confirm: ").strip() != a.env:
        print("not confirmed — nothing written")
        return 1
    url = conn["url"].rstrip("/")
    c = H.Client(url, H.resolve_key(conn, None), timeout=H.conn_timeout(conn))
    password = secrets.token_urlsafe(18) + "aA1!"     # lives only in this process; the user never logs in

    parts = urlparse(url)
    hidden = [x for x in (url, parts.netloc, parts.hostname) if x]

    def clean(s: str) -> str:
        for x in (password, c.key):
            s = s.replace(x, "<secret>")
        for x in hidden:
            s = s.replace(x, "<server>")
        return s[:300]

    def short(js) -> dict | None:
        if not isinstance(js, dict):
            return None
        return {k: (clean(v) if isinstance(v, str) else v) for k, v in js.items() if k in ("Id", "StatusCode", "Message")}

    member_str = re.compile(r"^(User|Dept|Group),\d+(,(True|False)?)?$")

    def safe(v, depth: int = 0):
        """Member values without personal data: ids and member strings as they are; of a record only its keys, ids
        and booleans (a member record may carry names or secret fields — never print it whole)."""
        if isinstance(v, bool) or v is None:
            return v
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            return v if member_str.match(v) or v.isdigit() else f"<text, {len(v)} chars>"
        if isinstance(v, list) and depth < 3:
            return [safe(x, depth + 1) for x in v[:50]]
        if isinstance(v, dict) and depth < 3:
            return {"keys": sorted(str(k) for k in v)[:40],
                    "ids": {k: x for k, x in v.items() if str(k).endswith("Id") and as_id(x)},
                    "flags": {k: x for k, x in v.items() if isinstance(x, bool)}}
        return f"<{type(v).__name__}>"

    def as_id(v) -> int | None:
        if isinstance(v, str) and v.isdigit():
            v = int(v)
        return v if isinstance(v, int) and not isinstance(v, bool) and v > 0 else None

    def users_named() -> list[int]:
        st, js, _ = c.call("/api/users/get", {"View": {"ColumnFilterHash": {"LoginId": login}}})
        if st != 200 or not isinstance(js, dict):
            raise ProbeError(f"/api/users/get: HTTP {st}")
        rows = [r for r in (js.get("Response") or {}).get("Data") or [] if isinstance(r, dict) and r.get("LoginId") == login]
        odd.update(repr(r.get("UserId"))[:40] for r in rows if not as_id(r.get("UserId")))   # reported, never deleted
        return sorted(i for i in (as_id(r.get("UserId")) for r in rows) if i)

    def groups_named() -> list[int]:
        st, js, _ = c.call("/api/groups/get", {"View": {"ColumnFilterHash": {"GroupName": gname}}})
        if st != 200 or not isinstance(js, dict):
            raise ProbeError(f"/api/groups/get: HTTP {st}")
        rows = [r for r in (js.get("Response") or {}).get("Data") or [] if isinstance(r, dict) and r.get("GroupName") == gname]
        odd.update(repr(r.get("GroupId"))[:40] for r in rows if not as_id(r.get("GroupId")))
        return sorted(i for i in (as_id(r.get("GroupId")) for r in rows) if i)

    def group_by_id(gid: int) -> dict | None:
        """The group with this id: first by the probe name, then (the name may change in step 4) every page of
        /api/groups/get without a filter. Paging fields are not observed yet: when they are missing and the group was
        not on the first page, that is an error, not "not found"."""
        st, js, _ = c.call("/api/groups/get", {"View": {"ColumnFilterHash": {"GroupName": gname}}})
        if st == 200 and isinstance(js, dict):
            for r in (js.get("Response") or {}).get("Data") or []:
                if isinstance(r, dict) and as_id(r.get("GroupId")) == gid:
                    return r
        offset, seen_ids = 0, set()
        for _ in range(MAX_PAGES):
            st, js, _ = c.call("/api/groups/get", {"Offset": offset})
            if st != 200 or not isinstance(js, dict):
                raise ProbeError(f"/api/groups/get (Offset {offset}): HTTP {st}")
            resp = js.get("Response") or {}
            rows = resp.get("Data") or []
            for r in rows:
                if isinstance(r, dict) and as_id(r.get("GroupId")) == gid:
                    return r
            page_ids = {as_id(r.get("GroupId")) for r in rows if isinstance(r, dict)} - {None}
            if rows and not page_ids - seen_ids:
                raise ProbeError(f"group {gid}: page at Offset {offset} repeats earlier groups — paging not honoured")
            seen_ids |= page_ids
            total, size = resp.get("TotalCount"), resp.get("PageSize")
            if not rows:
                return None
            if not isinstance(size, int) or size <= 0 or not isinstance(total, int):
                raise ProbeError(f"group {gid}: not on the first page and the answer has no TotalCount/PageSize "
                                 f"(keys: {sorted(resp)[:20]})")
            if offset + size >= total:
                return None
            offset += size
        raise ProbeError(f"group {gid} not found within {MAX_PAGES} pages")

    def member_view(r: dict | None, step: str) -> dict:
        if r is None:
            return {"found": False}
        fields = {k: r[k] for k in r if "Member" in str(k) or "Children" in str(k)}
        view = {"found": True, "GroupName": clean(str(r.get("GroupName"))), "Body": clean(str(r.get("Body"))),
                "member_fields": {k: safe(v) for k, v in fields.items()}}
        if not any(v not in (None, "", [], {}) for v in fields.values()):
            seen = input(f"[{step}] The API shows no members. Open group {gid} in the Pleasanter UI (group management) "
                         f"and type the member user ids shown, comma-separated (operator {op_id}, probe user {uid}); "
                         "type ? if unsure: ").strip()
            view["members_seen_in_ui"] = seen[:100]
        return view

    def update(gid: int, body: dict) -> dict:
        st, js, _ = c.call(f"/api/groups/{gid}/update", body)
        return {"status": st, "body": short(js), "not_json": js is None, "sent_fields": sorted(body)}

    out: dict = {"probe": "group-members", "env": a.env, "login_id": login, "group_name": gname, "operator": op,
                 "at": datetime.now().astimezone().isoformat()}
    uid = gid = None
    user_deleted = False
    odd: set[str] = set()
    answered = {"user": set(), "group": set()}       # ids the create answers named; never deleted unless confirmed
    stage = "before"
    try:
        if users_named() or groups_named():
            raise ProbeError("the probe user or group name already exists — nothing created")
        stage = "create_user"
        st, js, _ = c.call("/api/users/create", {"LoginId": login, "Name": "probe user (ADR-0019)", "Password": password})
        out["create_user"] = {"status": st, "body": short(js)}
        if isinstance(js, dict) and as_id(js.get("Id")):
            answered["user"].add(as_id(js.get("Id")))
        found = users_named()
        if len(found) != 1 or (isinstance(js, dict) and as_id(js.get("Id")) not in (None, found[0])):
            raise ProbeError(f"probe user not confirmed (lookup {found})")
        uid = found[0]
        out["user_id"] = uid
        stage = "create_group"
        st, js, _ = c.call("/api/groups/create", {"GroupName": gname, "Body": "probe (ADR-0019)",
                                                  "GroupMembers": [f"{op},False"]})
        out["create_group"] = {"status": st, "body": short(js)}
        if isinstance(js, dict) and as_id(js.get("Id")):
            answered["group"].add(as_id(js.get("Id")))
        found = groups_named()
        if len(found) != 1 or (isinstance(js, dict) and as_id(js.get("Id")) not in (None, found[0])):
            raise ProbeError(f"probe group not confirmed (lookup {found})")
        gid = found[0]
        out["group_id"] = gid
        stage = "read_created"
        r = group_by_id(gid)
        out["group_fields"] = sorted(str(k) for k in r) if r else None
        out["read_created"] = member_view(r, "after create: operator only")
        stage = "update_add"
        out["update_add"] = update(gid, {"GroupName": gname, "Body": "probe (ADR-0019)",
                                         "GroupMembers": [f"{op},False", f"User,{uid},True"]})
        out["read_after_add"] = member_view(group_by_id(gid), "after adding the probe user as group administrator")
        stage = "update_body_only"
        out["update_body_only"] = update(gid, {"Body": "probe body only (ADR-0019)"})
        out["read_after_body_only"] = member_view(group_by_id(gid), "after a Body-only update")
        stage = "update_replace"
        out["update_replace"] = update(gid, {"GroupName": gname, "GroupMembers": [f"User,{uid},True"]})
        out["read_after_replace"] = member_view(group_by_id(gid), "after GroupMembers = probe user only")
        stage = "delete_member_user"
        st, js, _ = c.call(f"/api/users/{uid}/delete")
        out["delete_member_user"] = {"status": st, "body": short(js)}
        user_deleted = st == 200 and isinstance(js, dict) and js.get("StatusCode") == 200
        out["read_after_user_delete"] = member_view(group_by_id(gid), "after the probe user was deleted")
    except BaseException as ex:                        # also Ctrl+C: clean up and print what is known
        out["error"] = {"stage": stage, "type": type(ex).__name__, "message": clean(str(ex))}
    finally:
        out["cleanup"] = []
        if stage != "before":
            for kind, lookup, path in (("group", groups_named, "/api/groups/{}/delete"),
                                       ("user", users_named, "/api/users/{}/delete")):
                try:
                    targets = set(lookup())
                except BaseException as ex:
                    targets = set()
                    out["cleanup"].append({"kind": kind, "lookup_error": clean(f"{type(ex).__name__}: {ex}")})
                confirmed = gid if kind == "group" else (None if user_deleted else uid)
                if confirmed:
                    targets.add(confirmed)             # confirmed at creation; the name may have changed since
                for i in sorted(targets):
                    try:
                        st, js, _ = c.call(path.format(i))
                        out["cleanup"].append({"kind": kind, "id": i, "status": st, "body": short(js)})
                    except BaseException as ex:
                        out["cleanup"].append({"kind": kind, "id": i, "error": clean(f"{type(ex).__name__}: {ex}")})
            left: dict = {}
            for key, check in (("groups_named", groups_named), ("users_named", users_named),
                               ("group_by_id", lambda: bool(gid and group_by_id(gid)))):
                try:
                    left[key] = check()
                except BaseException as ex:
                    left[key] = "unknown: " + clean(f"{type(ex).__name__}: {ex}")
            deleted_ok = any(e.get("kind") == "group" and e.get("id") == gid and e.get("status") == 200
                             and (e.get("body") or {}).get("StatusCode") == 200 for e in out["cleanup"])
            if isinstance(left.get("group_by_id"), str) and left.get("groups_named") == [] and deleted_ok:
                left["group_by_id"] = False            # its delete answered 200 and the name finds nothing
            confirmed_ids = {"user": {uid} - {None}, "group": {gid} - {None}}
            unconfirmed = {k: sorted(answered[k] - confirmed_ids[k]) for k in answered if answered[k] - confirmed_ids[k]}
            if unconfirmed:
                left["unconfirmed"] = unconfirmed      # check these ids in the UI; not deleted
            if odd:
                left["odd_ids"] = sorted(odd)
            out["left_after_delete"] = left
        print(json.dumps(out, ensure_ascii=False, indent=2))
    left = out.get("left_after_delete") or {}
    clean_end = all(left.get(k) in ([], False) for k in ("groups_named", "users_named", "group_by_id")) \
        and not left.get("unconfirmed") and not left.get("odd_ids")
    return 0 if "error" not in out and clean_end else 1


if __name__ == "__main__":
    sys.exit(main())
