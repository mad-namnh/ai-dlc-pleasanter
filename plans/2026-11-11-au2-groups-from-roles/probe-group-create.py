"""Probe for ADR-0017 (AU2): can the Pleasanter API of a dev environment create and delete a group?

Run by the operator (never by an agent), in a terminal, from a project folder whose environments.json declares the
environment with role "dev" (not a sandbox) and whose .pls/connections.json allows writes to it:

    python pls.py version --env dev
    python <framework>/plans/2026-11-11-au2-groups-from-roles/probe-group-create.py --env dev

What it does on that environment (groups are tenant-wide objects):
  1. looks up a fresh name zz_probe_group_<timestamp>; stops if a group with that name already exists;
  2. creates the group with no members (POST /api/groups/create);
  3. reads it back by name (POST /api/groups/get);
  4. tries to create a second group with the same name (does the server refuse duplicates?);
  5. in every case, also after a failure: looks the name up again and deletes only the groups that lookup returns
     with exactly that name (POST /api/groups/{id}/delete), then checks that none is left. An id a create answered
     with is only reported (it is not known yet whether it is the GroupId); when the cleanup lookup fails nothing is
     deleted and the result says so.
It prints one JSON result: HTTP statuses and the server's Id/StatusCode/Message only. No key; the server URL is
replaced by <server> in every message. Paste that output back. If `left_after_delete` is not [] (or is "unknown"),
delete those groups by hand in the UI.

A one-off script outside `pls`: it is not in the write-path inventory (test_write_guards.py) and leaves no run-log
line. Retire it once the KB entry exists.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "pls"))
import pls_http as H  # noqa: E402


class ProbeError(Exception):
    pass


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--env", default="dev")
    a = ap.parse_args()
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
    name = "zz_probe_group_" + datetime.now().strftime("%Y%m%d%H%M%S")
    if input(f"creates and deletes group '{name}' on {a.env}; type {a.env} to confirm: ").strip() != a.env:
        print("not confirmed — nothing written")
        return 1
    url = conn["url"].rstrip("/")
    c = H.Client(url, H.resolve_key(conn, None), timeout=H.conn_timeout(conn))

    parts = urlparse(url)
    secrets_of_location = [x for x in (url, parts.netloc, parts.hostname) if x]

    def clean(s: str) -> str:
        """No server URL or host name in the result: it is pasted back and may reach the repository."""
        for x in secrets_of_location:
            s = s.replace(x, "<server>")
        return s[:300]

    def short(js) -> dict | None:
        if not isinstance(js, dict):
            return None
        return {k: (clean(v) if isinstance(v, str) else v) for k, v in js.items() if k in ("Id", "StatusCode", "Message")}

    def find() -> tuple[int, list[int]]:
        st, js, _ = c.call("/api/groups/get", {"View": {"ColumnFilterHash": {"GroupName": name}}})
        if st != 200 or not isinstance(js, dict):
            raise ProbeError(f"/api/groups/get: HTTP {st}")
        rows = (js.get("Response") or {}).get("Data") or []
        ids = []
        for r in rows:
            gid = r.get("GroupId")
            if r.get("GroupName") != name:
                continue
            if isinstance(gid, str) and gid.isdigit():
                gid = int(gid)
            if isinstance(gid, int) and not isinstance(gid, bool) and gid > 0:
                ids.append(gid)
            else:
                odd.append(repr(gid)[:40])          # reported, never deleted
        return st, sorted(ids)

    def create(body: str) -> dict:
        st, js, _ = c.call("/api/groups/create", {"GroupName": name, "Body": body})
        if isinstance(js, dict) and isinstance(js.get("Id"), int) and js["Id"] > 0 and st == 200:
            answered.add(js["Id"])
        return {"status": st, "body": short(js), "not_json": js is None}

    out: dict = {"probe": "group-create", "env": a.env, "name": name, "at": datetime.now().astimezone().isoformat()}
    answered: set[int] = set()
    odd: list[str] = []
    stage = "before"
    try:
        _, ids = find()
        out["before"] = ids
        if ids:
            raise ProbeError("a group with the probe name already exists — nothing created")
        stage = "create"
        out["create"] = create("probe (ai-dlc-pleasanter ADR-0017)")
        stage = "after_create"
        out["after_create"] = find()[1]
        stage = "create_duplicate"
        out["create_duplicate"] = create("probe duplicate")
        stage = "after_duplicate"
        out["after_duplicate"] = find()[1]
    except BaseException as ex:                    # also Ctrl+C: clean up and print what is known
        out["error"] = {"stage": stage, "type": type(ex).__name__, "message": clean(str(ex))}
    finally:
        out["delete"] = []
        if stage != "before":                      # nothing was sent to create before that stage
            try:
                targets = find()[1]                    # only groups with exactly the probe's name
            except BaseException as ex:
                targets = []                           # nothing confirmed: delete nothing
                out["delete_lookup_error"] = clean(f"{type(ex).__name__}: {ex}") + " — nothing deleted"
            out["create_answer_ids"] = sorted(answered)
            out["create_answer_is_group_id"] = bool(answered) and answered <= set(out.get("after_duplicate") or out.get("after_create") or [])
            out["unconfirmed"] = sorted(answered - set(targets))   # check these ids in the UI; not deleted
            for gid in targets:
                try:
                    st, js, _ = c.call(f"/api/groups/{gid}/delete")
                    out["delete"].append({"id": gid, "status": st, "body": short(js)})
                except BaseException as ex:
                    out["delete"].append({"id": gid, "error": clean(f"{type(ex).__name__}: {ex}")})
            try:
                out["left_after_delete"] = find()[1]
            except BaseException as ex:
                out["left_after_delete"] = clean(f"unknown ({type(ex).__name__}: {ex}) — check groups named {name}")
        if odd:
            out["odd_group_ids"] = odd
        print(json.dumps(out, ensure_ascii=False, indent=2))
    clean_end = out.get("left_after_delete") in ([], None) and not out.get("unconfirmed") and "delete_lookup_error" not in out
    return 0 if "error" not in out and clean_end else 1


if __name__ == "__main__":
    sys.exit(main())
