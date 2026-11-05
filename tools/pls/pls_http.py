"""HTTP transport for pls (ADR-0008): talk to a Pleasanter environment directly with API keys.

Same files and semantics as the browser runner (browser/pls-runner.js), so a release planned by
`pls release-plan` can be applied either way. Stdlib only.

Connection settings live on the operator's machine, never in git:
  .pls/connections.json   (or the file named by $PLS_CONNECTIONS)
  {
    "dev": {"url": "https://pleasanter-dev.example.jp",
            "keys": {"admin": "env:PLS_DEV_ADMIN_KEY", "staff": "env:PLS_DEV_STAFF_KEY"},
            "default_key": "admin",
            "allow_write": true}
  }
Key references: "env:NAME" (environment variable) or "file:PATH" (file containing only the key,
relative to the connections file). Literal keys are refused, so a key never sits in a JSON file that
could be copied around by mistake.

Write guard (CLAUDE.md rule 1, ADR-0003): writes need environments.json role "dev" or "stg" AND
allow_write true in the local connection. role "prod" is never written to by this tool.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

WRITABLE_ROLES = {"dev", "stg"}


class TransportError(Exception):
    pass


# ---------------------------------------------------------------- connections

def connections_file(root: Path) -> Path:
    p = os.environ.get("PLS_CONNECTIONS")
    return Path(p) if p else root / ".pls" / "connections.json"


def load_connection(root: Path, env: str) -> dict:
    f = connections_file(root)
    if not f.exists():
        raise TransportError(f"{f} not found — copy connections.example.json to .pls/connections.json and fill in the URL "
                             "(keys go in environment variables, see README)")
    try:
        allc = json.loads(f.read_text(encoding="utf-8-sig"))   # Windows PowerShell 5 writes a BOM
    except json.JSONDecodeError as ex:
        raise TransportError(f"{f} is not JSON: {ex}")
    c = allc.get(env)
    if not c or not c.get("url"):
        raise TransportError(f"{f}: no url for environment '{env}'")
    c = dict(c)
    c["_dir"] = str(f.parent)
    return c


def resolve_key(conn: dict, name: str | None) -> str:
    name = name or conn.get("default_key") or "admin"
    ref = (conn.get("keys") or {}).get(name)
    if not ref:
        raise TransportError(f"no key '{name}' in the connection (keys: {sorted((conn.get('keys') or {}))})")
    if ref.startswith("env:"):
        v = os.environ.get(ref[4:], "")
        if not v:
            raise TransportError(f"key '{name}': environment variable {ref[4:]} is not set")
        return v.strip()
    if ref.startswith("file:"):
        p = Path(conn["_dir"]) / ref[5:]
        if not p.exists():
            raise TransportError(f"key '{name}': file {p} not found")
        return p.read_text(encoding="utf-8-sig").strip()
    raise TransportError(f"key '{name}': use 'env:NAME' or 'file:PATH', not a literal key")


def assert_writable(env_conf: dict, conn: dict, env: str) -> None:
    role = env_conf.get("role")
    if role not in WRITABLE_ROLES or conn.get("allow_write") is not True:
        raise TransportError(f"REFUSED: writing to '{env}' needs environments.json role dev/stg (is {role!r}) and "
                             f"allow_write: true in the local connection (is {conn.get('allow_write')!r}). "
                             "Production is written only by the customer-side runner (ADR-0003).")


# ---------------------------------------------------------------- client

class Client:
    """Minimal Pleasanter API client. `opener` is injectable for tests."""

    def __init__(self, url: str, key: str, opener: Callable | None = None, timeout: float = 30):
        self.base = url.rstrip("/")
        self.key = key
        self.timeout = timeout
        self.opener = opener or urllib.request.urlopen

    def call(self, path: str, body: dict | None = None) -> tuple[int, Any, str]:
        data = json.dumps({"ApiVersion": 1.1, "ApiKey": self.key, **(body or {})}, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(self.base + path, data=data, method="POST",
                                     headers={"Content-Type": "application/json; charset=utf-8"})
        try:
            with self.opener(req, timeout=self.timeout) as r:
                status, text = r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            status, text = e.code, e.read().decode("utf-8", "replace")
        except urllib.error.URLError as e:
            raise TransportError(f"cannot reach {self.base}: {e.reason}")
        try:
            js = json.loads(text)
        except json.JSONDecodeError:
            js = None
        return status, js, text

    def export_site(self, site_id: int) -> dict:
        st, js, text = self.call(f"/api/items/{site_id}/getsite")
        if st != 200 or not js:
            raise TransportError(f"getsite {site_id}: HTTP {st} {text[:200]}")
        return js

    def apply(self, site_id: int, payload: dict) -> tuple[int, str]:
        for k in ("Title", "ReferenceType", "SiteSettings"):
            if k not in payload:
                raise TransportError(f"payload missing {k} (I2)")
        st, js, text = self.call(f"/api/items/{site_id}/updatesite", payload)
        return st, (js or {}).get("Message", text[:200])

    def create_site(self, parent_id: int, payload: dict) -> tuple[int, int | None, str]:
        st, js, text = self.call(f"/api/items/{parent_id}/createsite", payload)
        return st, (js or {}).get("Id"), text[:200]

    def backup_records(self, site_id: int, page: int = 200) -> dict:
        out: list = []
        offset = 0
        while True:
            st, js, text = self.call(f"/api/items/{site_id}/get",
                                     {"Offset": offset, "PageSize": page, "View": {"ColumnSorterHash": {"ResultId": "asc"}}})
            if st != 200 or not js:
                raise TransportError(f"get {site_id} offset {offset}: HTTP {st}")
            data = js["Response"].get("Data") or []
            out += data
            total = js["Response"].get("TotalCount")
            if not data or len(data) < page or (total is not None and len(out) >= total):
                break
            offset += page
        return {"site_id": site_id, "count": len(out), "records": out}

    def bulk_upsert(self, site_id: int, keys: list, data: list) -> tuple[int, str]:
        st, js, text = self.call(f"/api/items/{site_id}/bulkupsert", {"Keys": keys, "Data": data})
        return st, (js or {}).get("Message", text[:200])


# ---------------------------------------------------------------- release (same semantics as runner applyRelease)

def apply_release(client: Client, plan: dict, files: dict) -> dict:
    log: list[str] = []
    for step in plan["steps"] + plan["rollback"]:
        if step["payload_file"] not in files:
            return {"status": "refused", "log": [f"missing {step['payload_file']}"]}
    for step in plan["steps"]:
        live = client.export_site(step["site_id"])["Response"]["Data"]
        if live.get("UpdatedTime") != step["expect_updated_time"]:
            return {"status": "refused", "log": log + [f"{step['site']}: UpdatedTime {live.get('UpdatedTime')} ≠ plan "
                                                      f"{step['expect_updated_time']} — re-plan"]}
        log.append(f"preflight {step['site']} ok")
    touched: list[str] = []
    for step in plan["steps"]:
        touched.append(step["site"])          # a failed updatesite may still have changed the site → restore it too
        try:
            st, msg = client.apply(step["site_id"], files[step["payload_file"]])
        except TransportError as ex:
            st, msg = 0, str(ex)
        log.append(f"apply {step['site']} ({step['site_id']}) → HTTP {st}")
        if st != 200:
            return {"status": "rolled-back", "failed_site": step["site"], "log": log + rollback(client, plan, files, touched)}
    return {"status": "applied-unverified", "log": log + ["next: pls export each site, then pls mark-applied"]}


def rollback(client: Client, plan: dict, files: dict, sites: list | None = None) -> list[str]:
    out = []
    for step in plan["rollback"]:
        if sites is not None and step["site"] not in sites:
            continue
        try:                                            # one failing restore must not stop the others (S4)
            st, _ = client.apply(step["site_id"], files[step["payload_file"]])
        except TransportError as ex:
            st = f"error {ex}"
        out.append(f"restore {step['site']} ({step['site_id']}) → HTTP {st}")
    return out


def bootstrap(client: Client, plan: dict) -> dict:
    created, log = {}, []
    st, js, _ = client.call(f"/api/items/{plan['parent_id']}/getsite")
    if st != 200 or not js or js["Response"]["Data"].get("ReferenceType") != "Sites":
        return {"status": "refused", "created": created, "log": [f"parent {plan['parent_id']} is not a reachable folder (HTTP {st})"]}
    for s in plan["steps"]:
        if s["op"] != "createsite" or s["parent_id"] != plan["parent_id"]:
            return {"status": "refused", "created": created, "log": log + [f"bad step {s.get('site')}"]}
        st, sid, text = client.create_site(s["parent_id"], s["payload"])
        log.append(f"createsite {s['site']} under {s['parent_id']} → HTTP {st}" + (f" id {sid}" if sid else ""))
        if st != 200 or not sid:
            return {"status": "partial", "created": created, "log": log + [text, "stop: bind what was created, then decide"]}
        created[s["site"]] = sid
    return {"status": "created", "created": created, "log": log}


# ---------------------------------------------------------------- tests (same spec format as runner runTests)

_VAR = re.compile(r"^\$(\w+)$")


def _subst(v: Any, vars_: dict) -> Any:
    if isinstance(v, str):
        m = _VAR.match(v)
        return str(vars_[m.group(1)]) if m and m.group(1) in vars_ else v
    if isinstance(v, list):
        return [_subst(x, vars_) for x in v]
    if isinstance(v, dict):
        return {k: _subst(x, vars_) for k, x in v.items()}
    return v


def _get_path(o: Any, path: str) -> Any:
    for k in path.split("."):
        if o is None:
            return None
        if isinstance(o, list):
            o = o[int(k)] if k.isdigit() and int(k) < len(o) else None
        else:
            o = o.get(k) if isinstance(o, dict) else None
    return o


def _check(actual: Any, expected: Any) -> bool:
    if expected == "!empty":
        return actual not in (None, "") and not str(actual).startswith("1899-12-30")
    num = (int, float)
    if isinstance(actual, num) and isinstance(expected, num) and not isinstance(actual, bool) and not isinstance(expected, bool):
        return float(actual) == float(expected)   # Pleasanter sends 1.0; JSON.parse in the browser runner sees 1
    return json.dumps(actual, sort_keys=True, ensure_ascii=False) == json.dumps(expected, sort_keys=True, ensure_ascii=False)


def run_tests(clients: Callable[[str | None], Client], site_id: int, specs: list, env: str) -> dict:
    """clients(role) → Client using that role's key ("as" in a spec; None = default key)."""
    out = []
    for spec in specs:
        c = clients(spec.get("as_key"))
        vars_ = dict(spec.get("vars") or {})
        log: list[str] = []
        status = "pass"
        try:
            # configuration (process ids) is read with the default key: the role under test may not see the site (TD-14d)
            site = clients(None).export_site(spec.get("run_on") or site_id)["Response"]["Data"]
            procs = {p["Name"]: p for p in site["SiteSettings"].get("Processes") or []}
            spec_client = c
            for st in spec["steps"]:
                op = st["op"]
                c = clients(st["as_key"]) if st.get("as_key") else spec_client   # step-level key: fixtures as 総務, checks as 社員
                rid = vars_.get(st["record"].lstrip("$")) if st.get("record") else None
                if op == "create":
                    code, js, text = c.call(f"/api/items/{st.get('site') or site_id}/create", _subst(st.get("data") or {}, vars_))
                    if st.get("expectHttp"):
                        ok = code == st["expectHttp"]
                        log.append(f"{'ok ' if ok else 'NG '} create refused → HTTP {code} (expected {st['expectHttp']})"
                                   + (f" {js.get('Message')}" if js and js.get("Message") else ""))
                        status = status if ok else "fail"
                        continue
                    if not js or not js.get("Id"):
                        raise TransportError(f"create failed: HTTP {code} {text[:200]}")
                    vars_[st["save"]] = js["Id"]
                    log.append(f"create → {js['Id']}")
                elif op == "exec":
                    p = procs.get(st["process"])
                    if not p:
                        raise TransportError(f"process '{st['process']}' not found")
                    code, _, _ = c.call(f"/api/items/{rid}/update", {"ProcessId": p["Id"], **(st.get("data") or {})})
                    log.append(f"exec {st['process']}(Id {p['Id']}) → HTTP {code}")
                    if st.get("expectHttp") and code != st["expectHttp"]:
                        status = "fail"
                        log.append(f"expected HTTP {st['expectHttp']}")
                elif op in ("update", "delete"):
                    code, _, _ = c.call(f"/api/items/{rid}/{op}", _subst(st.get("data") or {}, vars_) if op == "update" else None)
                    log.append(f"{op} {rid} → HTTP {code}")
                    if code != (st.get("expectHttp") or 200):
                        status = "fail"
                        log.append(f"expected HTTP {st.get('expectHttp') or 200}")
                elif op == "get":
                    code, js, _ = c.call(f"/api/items/{rid}/get")
                    if st.get("expectHttp"):
                        ok = code == st["expectHttp"]
                        log.append(f"{'ok ' if ok else 'NG '} get {rid} → HTTP {code} (expected {st['expectHttp']})")
                        status = status if ok else "fail"
                        continue
                    if code != 200 or not js:
                        raise TransportError(f"get {rid}: HTTP {code}")
                    rec = js["Response"]["Data"][0]
                    for path, exp in st["expect"].items():
                        act, exp = _get_path(rec, path), _subst(exp, vars_)
                        ok = _check(act, exp)
                        log.append(f"{'ok ' if ok else 'NG '} {path} = {json.dumps(act, ensure_ascii=False)} (expected {json.dumps(exp, ensure_ascii=False)})")
                        status = status if ok else "fail"
                elif op == "list":
                    code, js, _ = c.call(f"/api/items/{st.get('site') or site_id}/get", {"View": st.get("view") or {}})
                    if st.get("expectHttp"):
                        ok = code == st["expectHttp"]
                        log.append(f"{'ok ' if ok else 'NG '} list → HTTP {code} (expected {st['expectHttp']})")
                        status = status if ok else "fail"
                        continue
                    ids = {str(x.get("IssueId") or x.get("ResultId")) for x in ((js or {}).get("Response") or {}).get("Data") or []}
                    for want, items in ((True, st.get("contains") or []), (False, st.get("excludes") or [])):
                        for v in items:
                            i = str(_subst(v, vars_))
                            ok = (i in ids) == want
                            log.append(f"{'ok ' if ok else 'NG '} {i} {'in' if want else 'not in'} view")
                            status = status if ok else "fail"
                elif op == "siteConfig":
                    for path, exp in st["expect"].items():
                        act = _get_path(site["SiteSettings"], path)
                        ok = (exp.get("contains") in str(act)) if isinstance(exp, dict) and "contains" in exp else _check(act, exp)
                        log.append(f"{'ok ' if ok else 'NG '} SiteSettings.{path} = {json.dumps(act, ensure_ascii=False)} (expected {json.dumps(exp, ensure_ascii=False)})")
                        status = status if ok else "fail"
                elif op == "editPage":
                    # Rendering needs a browser session of that user; an API key cannot open the edit screen.
                    log.append(f"skip editPage '{st.get('button')}' — needs a browser session (pls-runner.js); "
                               "covered by the API refusal and the process access control (D20)")
                    if status == "pass":
                        status = "pass-api-only"
                else:
                    raise TransportError(f"unknown op {op}")
        except TransportError as ex:
            status = "error"
            log.append(str(ex))
        out.append({"id": spec["id"], "reqs": spec.get("reqs"), "title": spec.get("title"),
                    "as": spec.get("as_key") or "default", "status": status, "log": log})
    return {"env": env, "site_id": site_id, "transport": "http", "tests": out}
