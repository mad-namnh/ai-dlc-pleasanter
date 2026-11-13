"""Removing the dev test users that `pls test-users` created (TD-24; Nam 2026-11-12: "Build, dev only").

`pls test-users --env <dev env> --remove`, for each role of design/roles.json with principal "Group":
  - a user `zz_test_<project>_<role>` is deleted only when this machine can prove it is the one pls created here:
    its password file `.pls/test-users/<env>-<role>.password` exists **and** its key file holds a key the API accepts
    now. A password file alone is not proof: a user deleted by hand and made again by someone else with the same
    LoginId would match it. A key does not outlive its user (KB api.md "Users and groups", D32), so an old key file
    never proves a newer user. Any other user with that LoginId is never deleted: a person checks it;
  - such a user is deleted (`/api/users/{id}/delete`: it leaves its groups and its key stops working), the LoginId
    lookup must then find no user, and only then its key and password files and `keys.<role>` (only when that is the
    test user's own reference) are removed;
  - local files left from an earlier run whose user is already gone are removed too (no Pleasanter write);
  - password and key files of this environment, and `keys.<role>` test-user references, for roles no longer in
    design/roles.json are named for a person.
Limit: the API cannot show whose key a key is (the rows a plain user reads are not verified), so the proof shows that
the key belongs to *a* live user, not to the user the LoginId lookup found. It fails when a key file is replaced by hand
with another live user's key, or when the test user's LoginId is changed in Pleasanter and a new user is then created
with the old LoginId (the stored key still works). pls writes the key file only with a key it confirmed right after
issuing it in the test user's own session. Nothing of a password or a key is printed. Trash box and LoginId reuse after a
delete are not verified (KB).
"""
from __future__ import annotations

from pathlib import Path

import pls_test_users as TU


def ownership_proven(client, client_for, login: str, key_file: Path) -> bool:
    """True when the key file holds a key that is not the operator's and that the API accepts now."""
    key = TU.read_secret(key_file)
    return bool(key) and key != client.key and TU.key_works(client_for, login, key)


def plan_removals(roles: dict, conn: dict, conn_dir: Path, project: str, env: str, client,
                  client_for) -> tuple[list[dict], list[str]]:
    """(entries to remove, person notes). Reads only; refuses (TestUsersError) before any write."""
    entries, notes, seen = [], [], set()
    keys = conn.get("keys") or {}
    for role, spec in sorted(roles.items()):
        if not isinstance(spec, dict) or spec.get("principal") != "Group":
            continue
        if not TU.ROLE_NAME.match(role):
            raise TU.TestUsersError(f"role '{role}': not a test-user role name (a-z, 0-9, _) — nothing written")
        seen.add(role)
        login = TU.login_id(project, role)
        pw_file, key_file, ref = TU.files(conn_dir, env, role)
        ids = TU.users_with_login(client, login)
        if len(ids) > 1:
            raise TU.TestUsersError(f"{len(ids)} users have the LoginId {login} — check them in Pleasanter; nothing written")
        if ids and TU.read_secret(pw_file) is None:
            notes.append(f"{role}: user {login} (User,{ids[0]}) has no password file on this machine ({pw_file.name}) — "
                         "pls did not create it here, so it is not deleted; a person checks and deletes it in Pleasanter")
            continue
        if ids and not ownership_proven(client, client_for, login, key_file):
            notes.append(f"{role}: user {login} (User,{ids[0]}) is not proven to be the one pls created here (no key in "
                         f"{key_file.name} that the API accepts) — it may be someone else's user with the same LoginId, "
                         "so it is not deleted and the files are kept; a person checks it in Pleasanter, deletes it "
                         "there if it is the test user, then runs pls test-users --remove again to remove the files")
            continue
        drop_ref = keys.get(role) == ref
        if ids or pw_file.exists() or key_file.exists() or drop_ref:
            entries.append({"role": role, "login": login, "uid": ids[0] if ids else None, "pw_file": pw_file,
                            "key_file": key_file, "ref": ref, "drop_ref": drop_ref})
    left = {p.name[len(env) + 1:-len(p.suffix)] for ext in ("password", "key")
            for p in (conn_dir / "test-users").glob(f"{env}-*.{ext}")}
    left |= {r for r, v in keys.items() if v == TU.files(conn_dir, env, r)[2]}
    for role in sorted(r for r in left if TU.ROLE_NAME.match(r) and r not in seen):
        pw_file, key_file, ref = TU.files(conn_dir, env, role)
        found = [f.name for f in (pw_file, key_file) if f.exists()] + ([f"keys.{role}"] if keys.get(role) == ref else [])
        notes.append(f"role '{role}' is not a Group role in design/roles.json any more ({', '.join(found)}) — pls does "
                     f"not remove it; a person deletes the user {TU.login_id(project, role)} in Pleasanter if it exists, "
                     "then those files and the reference")
    return entries, notes


def what(e: dict) -> str:
    parts = ([f"delete user {e['login']} (User,{e['uid']})"] if e["uid"] else []) + \
        [f"remove {f.name}" for f in (e["key_file"], e["pw_file"]) if f.exists()] + \
        ([f"remove keys.{e['role']}"] if e["drop_ref"] else [])
    return f"{e['role']}: " + ", ".join(parts)


def delete_and_clean(entries: list[dict], client, drop_key_ref, log) -> list[str]:
    """Delete each user, check it is gone, then remove its local secrets. Returns the problems (files kept)."""
    problems = []
    for e in entries:
        if e["uid"]:
            st, msg = client.delete_user(e["uid"])
            if st != 200:
                problems.append(f"{e['role']}: deleting {e['login']} answered HTTP {st} ({msg}) — files kept")
                continue
            log(test_users_delete_answered=e["uid"])           # the server took the delete: logged before any check
            if TU.users_with_login(client, e["login"]):
                problems.append(f"{e['role']}: {e['login']} is still found after the delete — files kept; a person "
                                "checks it in Pleasanter")
                continue
            log(test_users_removed=e["uid"])
            print(f"{e['role']}: user {e['login']} (User,{e['uid']}) deleted (the lookup finds no user)")
        for f in (e["key_file"], e["pw_file"]):
            if f.exists():
                f.unlink()
        if e["drop_ref"]:
            drop_key_ref(e["role"], e["ref"])
        print(f"{e['role']}: key and password files removed" + (f", keys.{e['role']} removed" if e["drop_ref"] else ""))
    return problems
