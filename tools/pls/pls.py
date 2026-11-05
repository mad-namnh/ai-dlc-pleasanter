#!/usr/bin/env python3
"""pls — minimal, deterministic toolchain for AI-DLC Pleasanter projects (architecture §7.1).

pls 0.7. File commands work offline. Transport to Pleasanter is the HTTP client (pls_http.py,
ADR-0008: export / apply / bootstrap / test / backup, writes only to role dev/stg with the local
allow_write opt-in, never prod - I3). The browser runner (browser/pls-runner.js) is the fallback.
Projects call it through their launcher `python pls.py` (created by `pls init`).

Project layout used (see docs/architecture.md §3.2; v0.1 uses JSON, stdlib only):
  environments.json     envs → role, site ids/titles per logical name, env values
  config/<site>/        unpacked desired state: site.json, meta.json, server-scripts/, permissions.json (opt-in, ADR-0006)
  design/slot-ledger.json, traceability.json, tests/results/*.json, releases/R-*/

Commands:
  unpack   <export.json> --env E --site S       export → config/S (IDs and env values → references)
  pack     --env E --site S [--out F]           config/S → complete updatesite payload for env E
  canon    --site S                             apply Pleasanter's save-time normalisation to config/S (D8)
  lint                                          rule catalogue (L-SEC-01, L-REF-01, L-SCR-01, L-SLOT-01, L-LAD-01, L-CAN-01)
  diff     <export.json> --env E --site S       export (live) vs config (git HEAD), deterministic
  drift    <export.json> --env E --site S [--baseline P]
                                                live vs LAST APPLIED RELEASE (D11); exit 1 on drift; reports
                                                whether reverting the drift would be data-impacting
  classify <export.json> --env E --site S       config-only / data-impacting / permission-impacting
  slots    <export.json> --env E --site S       column-slot check: live target vs git vs slot ledger (A2); also run by plan
  coverage                                      requirements ↔ config ↔ passing tests
  plan     <export.json> --env E --site S --release R [--accept-drift DECISION] [--migration DIR]
                                                deploy plan with complete payload + rollback; refuses on drift
                                                and on column-slot collisions
  release-plan --env E --release R --export S=F [--export S2=F2 …] [--accept-drift DECISION] [--migration DIR]
                                                multi-site plan (A3): every per-site check, then order by dependency
                                                (${site:x} references, referenced sites first), snapshot + rollback per
                                                site, reverse-order rollback; nothing is written if any site fails
  bootstrap-plan --env E --release R            new sites (ADR-0007): createsite plan for managed sites without an id in E
  bind --env E --release R --created S=ID …     record the ids returned by createsite in environments.json
  mark-applied <release> <export.json>          verify live == release payload, then record the release as applied
  mark-applied <release> --export S=F …         same for a multi-site plan (every site must match)
  init <dir> [--stage S --target T --approver N]  new project from templates/project + skills + launcher (run from anywhere)
  skills check | sync                           project skills vs .claude/framework.lock vs the framework
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))   # pls_http (ADR-0008)
import pls_side_effects as SE                               # noqa: E402 — mail and job safety (ADR-0010)
import pls_version as PV                                    # noqa: E402 — Pleasanter version label (ADR-0009)
import pls_scope as SC                                      # noqa: E402 — components proven to round-trip (ADR-0001)
import pls_adopt as AD                                      # noqa: E402 — adopting existing sites (BR4)

SITE_VOLATILE = {"ApiKey", "SiteId", "ParentId", "InheritPermission", "TenantId", "Ver", "Creator", "Updator",
                 "CreatedTime", "UpdatedTime", "Timestamp", "ApiCountDate", "ApiCount", "LockedTime", "LockedUser",
                 "ApiVersion", "Comments", "Permissions", "ClassHash", "NumHash", "DateHash", "DescriptionHash",
                 "CheckHash", "AttachmentsHash", "Publish", "DisableCrossSearch"}
META_FIELDS = ["ReferenceType", "Body", "SiteName", "SiteGroupName"]
SCRIPT_KINDS = {"ServerScripts": ("server-scripts", ".js"), "Scripts": ("scripts", ".js"), "Styles": ("styles", ".css"),
                "Htmls": ("htmls", ".html")}
REF_RE = re.compile(r"\$\{(site|env|principal):([A-Za-z0-9_\-]+)\}")
SECRET_RES = {
    "anthropic-key": re.compile(r"sk-ant-[A-Za-z0-9_\-]{10,}"),
    "aws-access-key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "bearer-token": re.compile(r"(?i)bearer\s+[A-Za-z0-9\-\._~\+/]{20,}"),
    "assigned-secret": re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][^'\"]{12,}['\"]"),
}


# Output is UTF-8 on every console: a Windows console with cp932 cannot encode "—" and labels in other
# scripts, which made pls (and its tests) fail before printing (TD-12).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


class Fail(Exception):
    pass


# ---------------------------------------------------------------- project / io

def root() -> Path:
    p = Path.cwd()
    for d in [p, *p.parents]:
        if (d / "environments.json").exists():
            return d
    raise Fail("environments.json not found (run inside a project repository)")


def rj(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8-sig"))   # tolerate a BOM (files edited on Windows)


def wj(p: Path, obj: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def envs(r: Path) -> dict:
    return rj(r / "environments.json")


def env_conf(r: Path, env: str) -> dict:
    e = envs(r)["envs"].get(env)
    if not e:
        raise Fail(f"unknown environment '{env}'")
    return e


def site_data(export: Any) -> dict:
    d = export.get("Response", export) if isinstance(export, dict) else export
    d = d.get("Data", d) if isinstance(d, dict) else d
    if isinstance(d, list):
        d = d[0]
    if not isinstance(d, dict) or "SiteSettings" not in d:
        raise Fail("export does not look like a getsite response")
    return d


# ---------------------------------------------------------------- references

def id_maps(e: dict) -> tuple[dict, dict]:
    ids = {str(v["id"]): k for k, v in e["sites"].items() if v.get("id")}   # sites not created yet have no id (ADR-0007)
    vals = {v: k for k, v in (e.get("values") or {}).items() if v}
    return ids, vals


def to_refs(obj: Any, ids: dict, vals: dict, key: str = "") -> Any:
    """Replace env-specific values with ${site:x} / ${env:x} references."""
    if isinstance(obj, dict):
        return {k: to_refs(v, ids, vals, k) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_refs(v, ids, vals, key) for v in obj]
    if isinstance(obj, int) and not isinstance(obj, bool) and key.endswith("SiteId") and str(obj) in ids:
        return "${site:%s}" % ids[str(obj)]
    if isinstance(obj, str):
        s = obj
        for v, name in sorted(vals.items(), key=lambda x: -len(x[0])):
            s = s.replace(v, "${env:%s}" % name)
        for i, name in ids.items():
            s = re.sub(r"(?<!\d)%s(?!\d)" % re.escape(i), "${site:%s}" % name, s)
        return s
    return obj


def from_refs(obj: Any, e: dict, key: str = "") -> Any:
    if isinstance(obj, dict):
        return {k: from_refs(v, e, k) for k, v in obj.items()}
    if isinstance(obj, list):
        return [from_refs(v, e, key) for v in obj]
    if isinstance(obj, str):
        def sub(m):
            kind, name = m.group(1), m.group(2)
            if kind == "site":
                if name not in e["sites"]:
                    raise Fail(f"unresolved reference ${{site:{name}}}")
                if not e["sites"][name].get("id"):
                    raise Fail(f"site '{name}' is not created in this environment yet — pls bootstrap-plan, then pls bind (ADR-0007)")
                return str(e["sites"][name]["id"])
            if kind == "principal":
                val = (e.get("principals") or {}).get(name)
                if val is None:
                    raise Fail(f"unresolved reference ${{principal:{name}}} — add it to environments.json principals")
                return val
            val = (e.get("values") or {}).get(name)
            if val is None:
                raise Fail(f"unresolved reference ${{env:{name}}}")
            return val
        s = REF_RE.sub(sub, obj)
        if key.endswith("SiteId") and REF_RE.fullmatch(obj):
            return int(s)
        return s
    return obj


# ---------------------------------------------------------------- canonical form (S1, D8)

DEFAULTS_FILE = Path(__file__).resolve().parent / "canonical-defaults.json"


def _select(node: Any, parts: list[str]) -> list[dict]:
    """Resolve a rule path like 'Processes[].DataChanges[]' to the dicts it designates."""
    if not parts:
        return [node] if isinstance(node, dict) else []
    head, rest = parts[0], parts[1:]
    many = head.endswith("[]")
    key = head[:-2] if many else head
    child = node.get(key) if isinstance(node, dict) else None
    if child is None:
        return []
    if many:
        return [x for item in (child if isinstance(child, list) else []) for x in _select(item, rest)]
    return _select(child, rest)


def canonicalize(settings: dict) -> dict:
    """Apply Pleasanter's observed save-time normalisation so git holds what Pleasanter will store."""
    s = copy.deepcopy(settings)
    for rule in rj(DEFAULTS_FILE)["rules"]:
        for obj in _select(s, rule["path"].split(".")):
            for k, v in (rule.get("set_default") or {}).items():
                obj.setdefault(k, v)
            for k, v in (rule.get("drop_if") or {}).items():
                if k in obj and obj[k] == v:
                    del obj[k]
    return s


# ---------------------------------------------------------------- unpack / pack

def logical(export: Any, e: dict) -> dict:
    """Export → environment-independent logical model (what lives in git)."""
    d = copy.deepcopy(site_data(export))
    ids, vals = id_maps(e)
    ss = d["SiteSettings"]
    scripts = {}
    for kind in SCRIPT_KINDS:
        scripts[kind] = ss.pop(kind, None) or []
    model = {
        "meta": {k: d.get(k) for k in META_FIELDS if k in d},
        "settings": ss,
        "scripts": scripts,
    }
    model = to_refs(model, ids, vals)
    acl_to_refs(model["settings"], e)
    if "Permissions" in d or "InheritPermission" in d:
        model["permissions"] = perms_to_refs(d, e)
    return model


ACL_KEYS = (("Groups", "Group"), ("Users", "User"), ("Depts", "Dept"))


def acl_to_refs(settings: dict, e: dict) -> None:
    """Process access control (1.5.2, PR-4): Processes[].Groups/Users/Depts are lists of principal IDs.
    Replace them with ${principal:x} (environments.json principals); unmapped IDs stay raw (L-PERM-01)."""
    rev = {v: k for k, v in (e.get("principals") or {}).items()}
    for proc in settings.get("Processes") or []:
        for key, typ in ACL_KEYS:
            if key in proc:
                proc[key] = ["${principal:%s}" % rev[f"{typ},{i}"] if f"{typ},{i}" in rev else i for i in proc[key]]


def acl_from_refs(settings: dict, e: dict, site: str) -> None:
    for proc in settings.get("Processes") or []:
        for key, typ in ACL_KEYS:
            if key not in proc:
                continue
            out = []
            for x in proc[key]:
                m = REF_RE.fullmatch(str(x))
                if not m or m.group(1) != "principal":
                    raise Fail(f"{site}: process '{proc.get('Name')}' {key} uses an environment-specific id {x} (L-PERM-01)")
                val = (e.get("principals") or {}).get(m.group(2))
                if val is None:
                    raise Fail(f"unresolved reference ${{principal:{m.group(2)}}} — add it to environments.json principals")
                vtyp, vid = val.split(",")[:2]
                if vtyp != typ:
                    raise Fail(f"{site}: process '{proc.get('Name')}' {key} expects a {typ}, but principal '{m.group(2)}' is {val}")
                out.append(int(vid))
            proc[key] = out


def perms_to_refs(d: dict, e: dict) -> dict:
    """Site permissions (InheritPermission + "Type,Id,Value" entries) with environment-specific IDs replaced:
    sites → ${site:x}, principals → ${principal:x} via environments.json "principals" ({"name": "Group,2"}).
    Unmapped IDs stay raw and are reported by lint L-PERM-01."""
    ids, _ = id_maps(e)
    rev = {v: k for k, v in (e.get("principals") or {}).items()}
    inh = d.get("InheritPermission")
    inherit = "${site:%s}" % ids[str(inh)] if str(inh) in ids else inh
    entries = []
    for x in d.get("Permissions") or []:
        typ, pid, val = (str(x).split(",") + ["", "", ""])[:3]
        key = f"{typ},{pid}"
        entries.append("${principal:%s},%s" % (rev[key], val) if key in rev else str(x))
    return {"inherit": inherit, "entries": sorted(entries)}


def write_tree(model: dict, out: Path) -> None:
    if out.exists():
        for f in sorted(out.rglob("*"), reverse=True):
            if f.is_file():
                f.write_text("", encoding="utf-8")  # truncate; stale files reported by lint
    wj(out / "meta.json", model["meta"])
    wj(out / "site.json", model["settings"])
    if model.get("permissions") is not None:
        wj(out / "permissions.json", model["permissions"])
    for kind, (folder, ext) in SCRIPT_KINDS.items():
        items = model["scripts"].get(kind) or []
        if not items:
            continue
        index, used = [], set()
        for it in items:
            base = it.get("Name") or f"script-{it.get('Id')}"
            name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", base).replace("..", "_").strip(" .") or "script"
            if name != base or name.lower() in used:       # unsafe on disk or duplicate: make it unique with the Id
                name = f"{name}-{it.get('Id')}"
                while name.lower() in used:
                    name += "_"
            used.add(name.lower())
            (out / folder).mkdir(parents=True, exist_ok=True)
            (out / folder / f"{name}{ext}").write_text(it.get("Body", ""), encoding="utf-8", newline="")   # keep CRLF (S7)
            index.append({k: v for k, v in it.items() if k != "Body"} | {"File": f"{name}{ext}"})
        wj(out / folder / "_index.json", index)


def read_tree(d: Path) -> dict:
    if not (d / "site.json").exists():
        raise Fail(f"no unpacked site at {d}")
    scripts = {}
    for kind, (folder, _) in SCRIPT_KINDS.items():
        idx = d / folder / "_index.json"
        items = []
        if idx.exists() and idx.read_text(encoding="utf-8").strip():
            for it in rj(idx):
                it = dict(it)
                f = it.pop("File")
                with open(d / folder / f, encoding="utf-8", newline="") as fh:     # keep CRLF as stored (S7)
                    it["Body"] = fh.read()
                items.append(it)
        scripts[kind] = items
    pf = d / "permissions.json"
    perms = rj(pf) if pf.exists() and pf.read_text(encoding="utf-8").strip() else None
    model = {"meta": rj(d / "meta.json"), "settings": rj(d / "site.json"), "scripts": scripts}
    if perms is not None:
        model["permissions"] = perms
    return model


def payload(model: dict, e: dict, site: str) -> dict:
    raw = [x for x in ((model.get("permissions") or {}).get("entries") or []) if not str(x).startswith("${principal:")]
    if raw:
        raise Fail(f"{site}: permissions use environment-specific principal ids {raw} (L-PERM-01) — map them in environments.json principals")
    m0 = copy.deepcopy(model)
    acl_from_refs(m0["settings"], e, site)       # before from_refs: principal refs → typed integer IDs
    m = from_refs(m0, e)
    ss = m["settings"]
    for kind, items in m["scripts"].items():
        if items:
            ss[kind] = items
    p = {"Title": e["sites"][site].get("title", site), "ReferenceType": m["meta"].get("ReferenceType"),
         "Body": m["meta"].get("Body", ""), "SiteSettings": ss}
    if m.get("permissions") is not None:
        # Permission keys are optional in updatesite: omitted → live permissions untouched (D15, probe 2026-11-05).
        inh = m["permissions"].get("inherit")
        if not str(inh).isdigit():
            raise Fail(f"{site}: permissions.inherit '{inh}' is not resolvable in this environment")
        p["InheritPermission"] = int(inh)
        p["Permissions"] = list(m["permissions"].get("entries") or [])
    return p


# ---------------------------------------------------------------- diff

def flat_diff(a: Any, b: Any, path: str = "") -> list[dict]:
    out: list[dict] = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            p = f"{path}.{k}" if path else k
            if k not in b:
                out.append({"path": p, "kind": "removed", "before": a[k], "after": None})
            elif k not in a:
                out.append({"path": p, "kind": "added", "before": None, "after": b[k]})
            else:
                out += flat_diff(a[k], b[k], p)
    elif isinstance(a, list) and isinstance(b, list) and all(isinstance(x, dict) for x in a + b) and \
            any(("ColumnName" in x or "Id" in x or "Name" in x) for x in a + b):
        def key(x):
            return str(x.get("ColumnName", x.get("Name", x.get("Id"))))
        ka, kb = {key(x): x for x in a}, {key(x): x for x in b}
        for k in sorted(set(ka) | set(kb), key=str):
            p = f"{path}[{k}]"
            if k not in kb:
                out.append({"path": p, "kind": "removed", "before": ka[k], "after": None})
            elif k not in ka:
                out.append({"path": p, "kind": "added", "before": None, "after": kb[k]})
            else:
                out += flat_diff(ka[k], kb[k], p)
        if [key(x) for x in a if key(x) in kb] != [key(x) for x in b if key(x) in ka]:
            out.append({"path": path, "kind": "reordered", "before": [key(x) for x in a], "after": [key(x) for x in b]})
    elif a != b:
        out.append({"path": path, "kind": "changed", "before": a, "after": b})
    return out


def short(v: Any, n: int = 70) -> str:
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    s = s.replace("\n", "⏎").replace("|", "\\|")
    return s if len(s) <= n else s[: n - 1] + "…"


def labels(model: dict) -> dict:
    return {c["ColumnName"]: c.get("LabelText", c["ColumnName"]) for c in model["settings"].get("Columns", [])}


def md_diff(diffs: list[dict], lab: dict, title: str, right: str = "After (git)") -> str:
    rows = [f"### {title}", "", f"{len(diffs)} difference(s).", ""]
    if diffs:
        rows += [f"| Path | Kind | Label | Before (live) | {right} |", "|---|---|---|---|---|"]
        for d in diffs:
            m = re.search(r"\[(\w+)\]", d["path"])
            rows.append(f"| `{d['path']}` | {d['kind']} | {lab.get(m.group(1), '') if m else ''} | "
                        f"{short(d['before']) if d['before'] is not None else ''} | {short(d['after']) if d['after'] is not None else ''} |")
    return "\n".join(rows) + "\n"


# ---------------------------------------------------------------- classify (ADR-0004)

def classify(diffs: list[dict]) -> dict:
    data, perm, cfg = [], [], []
    for d in diffs:
        p = d["path"]
        if p.startswith("settings.Columns[") and d["kind"] == "removed" and p.count("[") == 1:
            data.append(f"{p}: column definition removed")
        elif re.match(r"settings\.Columns\[\w+\]\.ChoicesText", p) and d["kind"] in ("changed", "removed"):
            before = set(str(d["before"] or "").splitlines())
            after = set(str(d["after"] or "").splitlines())
            if before - after:
                data.append(f"{p}: choices removed {sorted(before - after)}")
            else:
                cfg.append(p)
        elif re.match(r"settings\.Columns\[\w+\]\.(Formula|DefaultInput)", p):
            data.append(f"{p}: formula/default changed")
        elif p.startswith("settings.Summaries"):
            data.append(f"{p}: summary added/changed — existing destination values are NOT recalculated (D16); "
                        "migration: touch one child record per parent after the release")
        elif p.startswith("permissions") or "Permission" in p or "AccessControl" in p:
            perm.append(p)
        elif re.match(r"settings\.Processes\[[^\]]+\]\.(Groups|Users|Depts)\b", p) or (
                re.fullmatch(r"settings\.Processes(\[[^\]]+\])?", p)
                and any(isinstance(y, dict) and (y.get("Groups") or y.get("Users") or y.get("Depts"))
                        for x in (d["before"], d["after"]) for y in (x if isinstance(x, list) else [x]))):
            perm.append(f"{p}: process access control (D20)")
        else:
            cfg.append(p)
    cls = "data-impacting" if data else "permission-impacting" if perm else "config-only"
    return {"classification": cls, "data_impacting": data, "permission_impacting": perm, "config_only": cfg}


# ---------------------------------------------------------------- lint (architecture §7.2)

def lint(r: Path) -> list[dict]:
    issues: list[dict] = []
    e_all = envs(r)
    all_ids = {str(s["id"]) for e in e_all["envs"].values() for s in e["sites"].values() if s.get("id")}
    ledger = rj(r / "design/slot-ledger.json") if (r / "design/slot-ledger.json").exists() else None
    decisions = "\n".join(p.read_text(encoding="utf-8") for p in (r / "design").rglob("*.md")) if (r / "design").exists() else ""
    for env_name, ec in e_all["envs"].items():                   # L-ENV-01: setup not finished
        for n, v in (ec.get("principals") or {}).items():
            if "<" in str(v):
                issues.append({"rule": "L-ENV-01", "site": "-", "msg": f"envs.{env_name}.principals.{n} = {v!r}: fill in the id (docs/setup.md)"})
        if ec.get("parent_id") == 0:                              # template value, never a real folder
            issues.append({"rule": "L-ENV-01", "site": "-", "msg": f"envs.{env_name}.parent_id: set the folder id for the app (docs/setup.md)"})
        try:                                                      # L-ENV-02: side effects declared with a known value
            SE.effects(ec)
        except ValueError as ex:
            issues.append({"rule": "L-ENV-02", "site": "-", "msg": f"envs.{env_name}.{ex} (ADR-0010)"})
    for site_dir in sorted((r / "config").iterdir()):
        if not site_dir.is_dir():
            continue
        site = site_dir.name
        if not (site_dir / "site.json").exists():
            continue      # new site designed in P2 (meta.json only) — unpacked after bootstrap in P3 (S5)
        m = read_tree(site_dir)
        blob = json.dumps(m, ensure_ascii=False)
        managed = set(e_all.get("managed_sites") or [])
        for kind_, name_ in sorted(set(REF_RE.findall(blob))):     # L-REF-02: every reference resolves (S5, B2)
            for env_name, ec in e_all["envs"].items():
                known = {"site": set(ec.get("sites") or {}) | managed, "principal": set(ec.get("principals") or {}),
                         "env": set(ec.get("values") or {})}[kind_]
                if name_ not in known:
                    issues.append({"rule": "L-REF-02", "site": site, "msg": f"${{{kind_}:{name_}}} is not defined for env '{env_name}' "
                                   f"({'principals in environments.json - run pls principals after creating the group' if kind_ == 'principal' else 'sites/managed_sites in environments.json' if kind_ == 'site' else 'values in environments.json'})"})
        for path, addr in SE.literal_addresses(m["settings"]):     # L-MAIL-01: no literal addresses (ADR-0010)
            issues.append({"rule": "L-MAIL-01", "site": site, "msg": f"{path}: literal mail address {addr}; use ${{env:…}} or ${{principal:…}}"})
        for name, rx in SECRET_RES.items():
            if rx.search(blob):
                issues.append({"rule": "L-SEC-01", "site": site, "msg": f"secret-like value ({name}) in configuration"})
        for kind, items in m["scripts"].items():
            for it in items:
                body, nm = it.get("Body", ""), it.get("Name")
                for i in all_ids:
                    if re.search(r"(?<!\d)%s(?!\d)" % i, body):
                        issues.append({"rule": "L-REF-01", "site": site, "msg": f"{kind}/{nm}: hard-coded SiteId {i}; use ${{site:…}}"})
                if kind == "ServerScripts" and it.get("Shared") and re.search(r"(?m)^\s*(const|let)\s+\w", body):
                    issues.append({"rule": "L-SCR-01", "site": site, "msg": f"shared server script '{nm}' declares top-level const/let (D7)"})
                if kind == "ServerScripts" and not it.get("Shared") and nm and nm not in decisions:
                    issues.append({"rule": "L-LAD-01", "site": site, "msg": f"server script '{nm}' has no design decision (ladder reason, I5)"})
        for proc in m["settings"].get("Processes") or []:
            for key, _ in ACL_KEYS:
                for x in proc.get(key) or []:
                    if not str(x).startswith("${principal:"):
                        issues.append({"rule": "L-PERM-01", "site": site, "msg": f"process '{proc.get('Name')}' {key} uses an environment-specific id {x}; map it in environments.json principals"})
        perms = m.get("permissions")
        if perms is not None:
            if not str(perms.get("inherit", "")).startswith("${site:"):
                issues.append({"rule": "L-PERM-01", "site": site, "msg": f"permissions.inherit '{perms.get('inherit')}' is an environment-specific id; map the site in environments.json"})
            for x in perms.get("entries") or []:
                if not str(x).startswith("${principal:"):
                    issues.append({"rule": "L-PERM-01", "site": site, "msg": f"permission entry '{x}' uses an environment-specific principal id; map it in environments.json principals"})
        if canonicalize(m["settings"]) != m["settings"]:
            issues.append({"rule": "L-CAN-01", "site": site, "msg": "configuration is not in canonical form; run `pls canon` (D8)"})
        if ledger is not None:
            slots = ledger.get(site, {})
            used = set(slots_in_use(m["settings"]))       # defined or placed — as the collision check sees it (A2)
            for col in sorted(used - set(slots)):
                issues.append({"rule": "L-SLOT-01", "site": site, "msg": f"column slot {col} is not in design/slot-ledger.json"})
            for col, info in slots.items():
                if info.get("status") == "allocated" and col not in used:
                    issues.append({"rule": "L-SLOT-01", "site": site, "msg": f"ledger allocates {col} but configuration does not define it"})
    return issues


# ---------------------------------------------------------------- slot collisions (A2, ADR-0002)

SLOT_RX = re.compile(r"^(Class|Num|Date|Description|Check|Attachments)[A-Z0-9]\w*$")


def slots_in_use(settings: dict) -> dict:
    """Column slots a site uses: defined in Columns, or placed on the editor, grid or filters.
    Pleasanter stores only non-default column attributes (D8), so a slot the customer enabled
    by just adding it to the editor appears in EditorColumnHash without a Columns entry."""
    used = {c["ColumnName"]: c.get("LabelText", "") for c in settings.get("Columns", []) if SLOT_RX.match(c.get("ColumnName", ""))}
    placed = [settings.get("GridColumns") or [], settings.get("FilterColumns") or []]
    placed += [v for v in (settings.get("EditorColumnHash") or {}).values() if isinstance(v, list)]
    for names in placed:
        for n in names:
            if isinstance(n, str) and SLOT_RX.match(n):
                used.setdefault(n, "")
    return used


def slot_collisions(live: dict, git: dict, ledger_site: dict) -> list[dict]:
    """Pre-deploy check: live target vs git vs ledger. Any finding blocks the plan.
    - live uses a slot the ledger does not know  → someone (usually the customer) took it outside the ledger;
      if git also defines it, the deploy would overwrite their column and its data (collision)
    - live label of a ledger slot differs from the ledger label → the slot was repurposed on the target
    - git defines a slot the ledger does not know → allocation skipped (P2 must record it)"""
    out = []
    lv, gv = slots_in_use(live), slots_in_use(git)
    for col in sorted(lv):
        if col not in ledger_site:
            clash = col in gv
            out.append({"slot": col, "kind": "collision" if clash else "unledgered-live",
                        "msg": (f"{col} is used on the target (label '{lv[col]}') but not in the slot ledger"
                                + (f"; git also defines it (label '{gv[col]}') — deploying would overwrite it" if clash
                                   else "; deploying would drop it — record it in the ledger (zone: customer) and fold it into git, or remove it in its own release"))})
        else:
            want = ledger_site[col].get("label", "")
            if lv[col] and want and lv[col] != want:
                out.append({"slot": col, "kind": "repurposed", "msg": f"{col} is labelled '{lv[col]}' on the target but '{want}' in the ledger"})
    for col in sorted(set(gv) - set(ledger_site) - set(lv)):
        out.append({"slot": col, "kind": "unledgered-git", "msg": f"git defines {col} but the slot ledger does not allocate it (record it in P2)"})
    return out


# ---------------------------------------------------------------- coverage (I8)

_PATH_RE = re.compile(r"^(\w+)(?:\[(.+)\])?$")
_LIST_KEYS = {"Columns": "ColumnName", "Processes": "Name", "Views": "Id", "Summaries": "Id", "Links": "ColumnName",
              "Notifications": "Id", "Reminders": "Id", "ServerScripts": "Name"}


def config_path_exists(r: Path, ref: str) -> bool:
    """'config/s/site.json#Columns[ClassA]' → the file exists AND the element exists (TD-14a)."""
    file, _, frag = ref.partition("#")
    f = r / file
    if not f.exists():
        return False
    if not frag or f.suffix != ".json":
        return True
    m = _PATH_RE.match(frag)
    if not m:
        return False
    data = rj(f)
    obj = data.get(m.group(1)) if isinstance(data, dict) else None
    if obj is None:
        return False
    if m.group(2) is None:
        return True
    key = _LIST_KEYS.get(m.group(1))
    if isinstance(obj, list):
        return any(str(x.get(key) if key else x) == m.group(2) or str(x.get("Name")) == m.group(2) for x in obj if isinstance(x, dict))
    if isinstance(obj, dict):
        return m.group(2) in obj
    return False


def coverage(r: Path) -> dict:
    tr = rj(r / "traceability.json")
    results = {}
    for f in sorted((r / "tests/results").glob("*.json")) if (r / "tests/results").exists() else []:
        for t in rj(f).get("tests", []):
            results[t["id"]] = t["status"]
    rows, ok = [], True
    for req, links in sorted(tr.items()):
        cfg = links.get("config", [])
        tests = links.get("tests", [])
        passed = [t for t in tests if results.get(t) in ("pass", "pass-api-only")]   # api-only: UI check skipped (HTTP transport)
        missing_cfg = [c for c in cfg if not config_path_exists(r, c)]
        good = bool(cfg) and not missing_cfg and bool(tests) and len(passed) == len(tests)
        ok &= good
        rows.append({"req": req, "config": len(cfg), "missing_config": missing_cfg, "tests": len(tests),
                     "passed": len(passed), "status": "covered" if good else "GAP"})
    return {"ok": ok, "rows": rows}


# ---------------------------------------------------------------- releases and drift baseline (S2, S3, D11)

APPLIED = ("applied", "applied-differs")   # applied-differs: live differs from the payload (D8) — baseline = live-<site>.json (S2)


def releases_for(r: Path, env: str, site: str, status: str | None = None) -> list[tuple[Path, dict]]:
    """status "applied" matches every applied state (APPLIED)."""
    out = []
    for p in sorted((r / "releases").glob("*/plan.json")) if (r / "releases").exists() else []:
        plan = rj(p)
        in_plan = plan.get("site") == site or site in (plan.get("sites") or [])
        st = plan.get("status")
        if plan.get("env") == env and in_plan and (status is None or st == status or (status == "applied" and st in APPLIED)):
            out.append((p.parent, plan))
    return sorted(out, key=lambda x: (_applied_key(x[1].get("applied_at")), x[1]["release"]))


def _applied_key(ts: str | None) -> float:
    """Sort key for applied_at. Timestamps carry different UTC offsets (+09:00 written by hand, +00:00 by
    mark-applied), so they must be compared as instants, not as strings. Missing/naive -> oldest/UTC."""
    if not ts:
        return float("-inf")
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def baseline(r: Path, e: dict, env: str, site: str, explicit: str | None) -> tuple[dict, str]:
    """Desired state that the environment SHOULD currently have: the last applied release, not git HEAD."""
    if explicit:
        src = Path(explicit)
    else:
        applied = releases_for(r, env, site, "applied")
        if not applied:
            return read_tree(r / "config" / site), "git HEAD (no applied release recorded for this env/site)"
        rel_dir, rel_plan = applied[-1]
        src = rel_dir / ((rel_plan.get("per_site") or {}).get(site, {}).get("payload_file") or "payload.json")
        live_f = rel_dir / f"live-{site}.json"
        if rel_plan.get("status") == "applied-differs" and live_f.exists():
            src = live_f       # what the environment really holds after that release (S2)
    pl = rj(src)
    return logical({"SiteSettings": pl["SiteSettings"], "ReferenceType": pl.get("ReferenceType"), "Body": pl.get("Body", "")}, e), str(src.relative_to(r) if src.is_absolute() and r in src.parents else src)


def same_meta(live: dict, base: dict) -> dict:
    """Release payloads carry only ReferenceType/Body; compare meta on the keys the baseline has."""
    out = dict(live, meta={k: v for k, v in live["meta"].items() if k in base["meta"]})
    if base.get("permissions") is None:
        out.pop("permissions", None)   # permissions not managed in git for this site (opt-in)
    return out


def drift_report(r: Path, e: dict, env: str, site: str, export: Any, explicit: str | None) -> tuple[list[dict], str]:
    base, label = baseline(r, e, env, site, explicit)
    live = same_meta(logical(export, e), base)
    diffs = flat_diff(live, base)
    text = md_diff(diffs, labels(base) | labels(live), f"{env}/{site}: live vs baseline ({label})", "Baseline (last release)")
    if diffs:
        rev = classify(diffs)
        text += (f"\n**Reverting this drift would be: {rev['classification']}.**"
                 + ("".join(f"\n- {x}" for x in rev["data_impacting"] + rev["permission_impacting"]))
                 + "\nResolve by accepting (fold into git + requirement) or reverting (via a release with its own gate); see D11.\n")
    return diffs, text


# ---------------------------------------------------------------- multi-site release plan (A3)

def site_deps(model: dict, site: str, known: set) -> set:
    """Sites this site's desired state references (${site:x} in settings or scripts)."""
    blob = json.dumps(model, ensure_ascii=False)
    return {m.group(2) for m in REF_RE.finditer(blob) if m.group(1) == "site" and m.group(2) in known and m.group(2) != site}


def order_sites(deps: dict) -> tuple[list, list]:
    """Topological order, referenced sites first (ties by name). Returns (order, sites in a cycle).
    Sites in a cycle are appended by name: all sites already exist, so updatesite order only matters
    for readability of the failure point and for rollback order, not for ID resolution."""
    pending = {k: set(v) & set(deps) for k, v in deps.items()}
    order = []
    while True:
        ready = sorted(k for k, v in pending.items() if not v)
        if not ready:
            break
        for k in ready:
            order.append(k)
            del pending[k]
        for v in pending.values():
            v.difference_update(ready)
    cyc = sorted(pending)
    return order + cyc, cyc


SEVERITY = ["config-only", "permission-impacting", "data-impacting"]
MIGRATION_FILES = ("migration.json", "backup", "dry-run.md")


def migration_problems(r: Path, migs: Any) -> list[str]:
    """Accepts one folder or a list (a release may carry several migrations)."""
    if isinstance(migs, (list, tuple)):
        return [p for m in migs for p in _migration_problems(r, m)] if migs else _migration_problems(r, None)
    return _migration_problems(r, migs)


def _migration_problems(r: Path, mig: str | None) -> list[str]:
    """Data-impacting gate (ADR-0004): a migration folder with the conversion (migration.json: site, keys,
    bulkupsert data or mapping), the backup of the affected records taken before (folder `backup/`,
    exported with the runner's backupRecords) and the log of a dry run on a copy (dry-run.md)."""
    if not mig:
        return ["data-impacting change without --migration DIR (ADR-0004)"]
    d = (r / mig) if not Path(mig).is_absolute() else Path(mig)
    out = [f"{mig}/{f} is missing" for f in MIGRATION_FILES if not (d / f).exists()]
    if (d / "backup").is_dir() and not any(f for f in (d / "backup").iterdir() if not f.name.startswith(".")):
        out.append(f"{mig}/backup/ is empty")
    if (d / "migration.json").exists():
        try:
            m = rj(d / "migration.json")
            for k in ("site", "keys", "rollback"):
                if k not in m:
                    out.append(f"{mig}/migration.json lacks '{k}'")
        except json.JSONDecodeError as ex:
            out.append(f"{mig}/migration.json is not JSON: {ex}")
    return out


def plan_site(r: Path, e: dict, env: str, site: str, export: Any, accept_drift: str | None,
              accept_unverified: str | None = None) -> tuple[bool, list, dict]:
    """All pre-deploy checks for one site. Returns (ok, messages, result)."""
    msgs = []
    live = logical(export, e)
    git = read_tree(r / "config" / site)
    scope = SC.site_findings(live["settings"] | live["scripts"], git["settings"] | git["scripts"])
    if scope and not accept_unverified:
        return False, [f"SCOPE {site}: {x}" for x in scope] + [
            f"{site}: REFUSED — components without round-trip evidence (ADR-0001); updatesite could change or drop them (D4). "
            "Probe them on a copy in dev, or pass --accept-unverified <decision record>"], {}
    drift_note = "no applied release recorded: first release, drift not checkable"
    if releases_for(r, env, site, "applied"):
        ddiffs, dtext = drift_report(r, e, env, site, export, None)
        if ddiffs and not accept_drift:
            return False, [dtext, f"{site}: REFUSED — the environment drifted from its last release (I2, D11)"], {}
        drift_note = "clean" if not ddiffs else f"drift accepted by {accept_drift}"
    ledger_p = r / "design/slot-ledger.json"
    if not ledger_p.exists():
        return False, [f"{site}: REFUSED — design/slot-ledger.json is missing (A2)"], {}
    coll = slot_collisions(live["settings"], git["settings"], rj(ledger_p).get(site, {}))
    if coll:
        return False, [f"SLOT {c['kind']:15} {site}: {c['msg']}" for c in coll] + [f"{site}: REFUSED — column-slot check failed (A2)"], {}
    live_site = site_data(export)
    new = payload(git, e, site)
    missing = sorted(set(live_site["SiteSettings"]) - set(new["SiteSettings"]) - {"ServerScripts", "Scripts", "Styles", "Htmls"})
    if missing:
        return False, [f"{site}: REFUSED — L-DEP-01 payload misses {missing}"], {}
    diffs = flat_diff(same_meta(live, git), git)
    snap = json.dumps(export, ensure_ascii=False, sort_keys=True)
    return True, msgs, {
        "site_id": e["sites"][site]["id"], "changes": len(diffs), "classification": classify(diffs),
        "snapshot_sha256": hashlib.sha256(snap.encode()).hexdigest(),
        "snapshot_updated_time": live_site.get("UpdatedTime"),
        "checks": {"L-DEP-01_complete_payload": True, "drift_vs_last_release": drift_note, "slot_collisions": "clean",
                   "scope": "verified" if not scope else {
                       "accepted_by": accept_unverified, "unverified": scope,
                       "record_sha256": hashlib.sha256(Path(accept_unverified).read_bytes()).hexdigest()}},
        "payload": new,
        "rollback": {k: live_site[k] for k in ("Title", "Body", "ReferenceType", "SiteSettings")
                     + (("InheritPermission", "Permissions") if "Permissions" in new or "InheritPermission" in new else ())
                     if k in live_site},
        "raw_diff": md_diff(diffs, labels(git) | labels(live), f"{env}/{site}: live (before) vs git (after)"),
        "deps": site_deps(git, site, set(e["sites"])),
        "side_effects": SE.changed_mail_elements(live["settings"], git["settings"]),
    }


def release_plan(r: Path, env: str, release: str, exports: dict, accept_drift: str | None, migration: str | None = None,
                 accept_unverified: str | None = None) -> int:
    e = env_conf(r, env)
    if (r / "releases" / release / "plan.json").exists():
        raise Fail(f"releases/{release}/plan.json exists — a release id is used once; choose the next id (S3)")
    if accept_drift and not Path(accept_drift).is_file():
        raise Fail(f"--accept-drift must name the drift decision record (file not found: {accept_drift})")
    if accept_unverified and not Path(accept_unverified).is_file():
        raise Fail(f"--accept-unverified must name the decision record (file not found: {accept_unverified})")
    if e.get("role") == "prod":
        print("note: production plans are executed by the customer-side runner (ADR-0003)")
    results, failed = {}, False
    for site, path in sorted(exports.items()):
        if site not in e["sites"]:
            raise Fail(f"site '{site}' is not in environments.json for {env}")
        ok, msgs, res = plan_site(r, e, env, site, rj(Path(path)), accept_drift, accept_unverified)
        for m in msgs:
            print(m)
        failed |= not ok
        results[site] = res
    if failed:
        print("release plan REFUSED: no files written")
        return 1
    fresh = new_sites(r, env)
    for s_, res in results.items():
        c = res["classification"]
        # First release of a site created by a bootstrap (ADR-0007): no records can predate it, and a summary
        # whose destination is also new has no existing values to recalculate (D16). Kept as notes, not gates.
        if s_ in fresh and c["data_impacting"] and all(d in fresh for d in res["deps"]):
            c["new_site_notes"] = [f"{x} — not applicable: first release of a new site (ADR-0007)" for x in c["data_impacting"]]
            c["data_impacting"] = []
            c["classification"] = "permission-impacting" if c["permission_impacting"] else "config-only"
    order, cyc = order_sites({s: res["deps"] for s, res in results.items()})
    rel = r / "releases" / release
    worst = max((res["classification"]["classification"] for res in results.values()), key=SEVERITY.index)
    if worst == "data-impacting":
        probs = migration_problems(r, migration)
        if probs:
            for s_, res in results.items():
                for x in res["classification"]["data_impacting"]:
                    print(f"DATA {s_}: {x}")
            for x in probs:
                print(f"MIGRATION {x}")
            print("release plan REFUSED: data-impacting change needs a migration (ADR-0004); no files written")
            return 1
    per_site = {}
    for s in order:
        res = results[s]
        wj(rel / f"payload-{s}.json", res["payload"])
        wj(rel / f"rollback-{s}.json", res["rollback"])
        (rel / f"raw-diff-{s}.md").write_text(res["raw_diff"], encoding="utf-8")
        per_site[s] = {k: res[k] for k in ("site_id", "changes", "classification", "snapshot_sha256", "snapshot_updated_time", "checks",
                                           "side_effects")}
        for x in res["side_effects"]:
            print(f"MAIL {s}: {x}")
        per_site[s].update(payload_file=f"payload-{s}.json", rollback_file=f"rollback-{s}.json", depends_on=sorted(res["deps"] & set(results)))
    plan = {
        "release": release, "env": env, "status": "planned", "sites": order,
        "classification": worst, "dependency_cycle": cyc, "per_site": per_site,
        "steps": [{"op": "updatesite", "site": s, "site_id": per_site[s]["site_id"], "payload_file": per_site[s]["payload_file"],
                   "expect_updated_time": per_site[s]["snapshot_updated_time"]} for s in order],
        "rollback": [{"op": "updatesite", "site": s, "site_id": per_site[s]["site_id"], "payload_file": per_site[s]["rollback_file"]}
                     for s in reversed(order)],
        "on_failure": "stop; restore every site already touched (including the failing one) from its rollback payload, in reverse order",
        "preflight": "every site's UpdatedTime must equal expect_updated_time, otherwise nothing is applied",
        "migration": migration if worst == "data-impacting" else None,
        "version_check": version_check(r, env),
    }
    for x in plan["version_check"]["differences"]:
        print(f"VERSION {x}")
    wj(rel / "plan.json", plan)
    if any(per_site[s]["side_effects"] for s in order) and e.get("role") != "prod":
        eff = SE.effects(e)
        if eff["mail"] == "unknown":
            print(f"note: envs.{env}.side_effects.mail is 'unknown' — `pls apply` will refuse this release until a person records it (ADR-0010)")
    print(f"release plan written to releases/{release}/ — order: {' → '.join(order)}"
          + (f" (cycle: {cyc})" if cyc else "") + f"; {sum(p['changes'] for p in per_site.values())} change(s), {worst}")
    return 0


def version_check(r: Path, env: str, tested_env: str = "dev") -> dict:
    """Version of the target vs the environment releases are tested on (ADR-0009). Shown at G4, never a refusal."""
    all_envs = envs(r)["envs"]
    target, tested = all_envs.get(env, {}).get("pleasanter"), all_envs.get(tested_env, {}).get("pleasanter")
    if env != tested_env:
        diffs = PV.compare(target, tested, env, tested_env)
    elif not target:
        diffs = [f"version of {env} not recorded — run `pls version --env {env}` (ADR-0009)"]
    elif target.get("app") in (None, PV.UNKNOWN):
        diffs = [f"application version not known for {env} — record it with `pls version --env {env} --app …` (ADR-0009)"]
    else:
        diffs = []
    return {"target": target, "tested_on": {tested_env: tested}, "differences": diffs}


def _adopted(r: Path, site: str) -> bool:
    """True when the site came into the project through `pls adopt` (an adoption record exists in any env)."""
    for p in (r / "releases").glob("A-*/plan.json") if (r / "releases").exists() else []:
        plan = rj(p)
        if plan.get("kind") == "adopt" and site in (plan.get("sites") or []):
            return True
    return False


def adopt_check_name(name: str) -> None:
    if not AD.SAFE_NAME.fullmatch(name):
        raise Fail(f"--name {name!r}: use a stable lower-case logical name (letters, digits, - and _)")


def adopt(r: Path, env: str, name: str, export: dict, today: str, stamp: str) -> int:
    """Local side of `pls adopt` (the export was read by one getsite). Never overwrites anything.
    First adoption of a name: config, ledger, adoption record, report, then environments.json (last, so a failure
    leaves nothing registered; files this run created are removed). Same name on another environment that has no id
    for it yet: only the id, that environment's adoption record and a report of how it differs from config/."""
    adopt_check_name(name)
    ev = rj(r / "environments.json")
    if env not in ev["envs"]:
        raise Fail(f"environment '{env}' is not in environments.json")
    d = site_data(export)
    sid = int(d["SiteId"])
    e = ev["envs"][env]
    known = e.setdefault("sites", {})
    for env_name, ec in ev["envs"].items():
        for other, conf in (ec.get("sites") or {}).items():
            if conf.get("id") == sid and (other != name or env_name == env):
                raise Fail(f"site {sid} is already registered as '{other}' in {env_name}")
    managed = name in (ev.get("managed_sites") or [])
    has_config = (r / "config" / name / "site.json").exists()
    second_env = managed and has_config and not (known.get(name) or {}).get("id")
    if not second_env and (managed or has_config or name in known):
        raise Fail(f"'{name}' is already in this project — adopt never overwrites; choose another name")
    ledger_p = r / "design" / "slot-ledger.json"
    ledger = rj(ledger_p) if ledger_p.exists() else {}
    if not second_env and name in ledger:
        raise Fail(f"design/slot-ledger.json already has '{name}'")

    # ---- compute everything before writing anything
    e_new = copy.deepcopy(e)
    e_new["sites"][name] = {"id": sid, "title": d.get("Title")}
    model = logical(export, e_new)
    model["settings"] = canonicalize(model["settings"])
    ss = d.get("SiteSettings") or {}
    blob = json.dumps(ss, ensure_ascii=False)
    secrets = [n for n, rx in SECRET_RES.items() if rx.search(blob)]
    if secrets:
        raise Fail(f"site {sid}: secret-like values in its configuration ({', '.join(secrets)}) — nothing written. Secrets must "
                   "not reach git (I7, ADR-0005): move them out of the site configuration first, then adopt")
    placed = slots_in_use({k: v for k, v in ss.items() if k != "FilterColumns"})
    entries = AD.slot_entries(slots_in_use(ss), today, set(slots_in_use(ss)) - set(placed))
    nf = sum(1 for v in entries.values() if v.get("placement") == "filter-only")
    rel = f"A-{stamp}-{env}-{name}"
    payload_a = {k: d.get(k) for k in ("Title", "Body", "ReferenceType", "SiteSettings")}
    plan_a = {"release": rel, "env": env, "status": "applied", "kind": "adopt", "sites": [name],
              "applied_at": datetime.now().astimezone().isoformat(timespec="seconds"),
              "per_site": {name: {"site_id": sid, "payload_file": f"payload-{name}.json"}},
              "note": "adoption record: the state found on the environment — a drift baseline, not a release (no gate)"}
    ids_all = {str(v["id"]): k for k, v in e_new["sites"].items() if v.get("id")}
    raw_scripts = {k: ss.get(k) or [] for k in SCRIPT_KINDS}
    perms = model.get("permissions") or {}
    principals = AD.raw_principals(perms) + [
        f"process '{p.get('Name') or p.get('Id')}' {key}: {x}" for p in model["settings"].get("Processes") or []
        for key, _ in ACL_KEYS for x in p.get(key) or [] if not str(x).startswith("${principal:")]
    if perms and not str(perms.get("inherit", "")).startswith("${site:"):
        principals.insert(0, f"permissions inherited from site {perms.get('inherit')} (not managed) — L-PERM-01")
    decisions = "\n".join(p.read_text(encoding="utf-8") for p in (r / "design").rglob("*.md")) if (r / "design").exists() else ""
    undecided = [it.get("Name") or f"(no name, Id {it.get('Id')})" for it in ss.get("ServerScripts") or []
                 if not it.get("Shared") and (not it.get("Name") or it.get("Name") not in decisions)]
    counts = {"slots used": len(entries) - nf, "slots only in filters": nf}
    counts |= {k: len(ss.get(k) or []) for k in ("Columns", "Processes", "Views", "Notifications", "Reminders", "Summaries",
                                                  "Links", "ServerScripts", "Scripts", "Styles", "Htmls", "DashboardParts")}
    extra = {
        "Literal mail addresses (L-MAIL-01)": [f"{p}: {a}" for p, a in SE.literal_addresses(ss)],
        "Site ids inside script bodies (become ${site:x}; review every SUSPICIOUS line)": AD.script_id_uses(raw_scripts, ids_all),
    }
    if second_env:
        git = read_tree(r / "config" / name)
        dd = flat_diff(git["settings"] | git["scripts"], model["settings"] | model["scripts"])
        extra[f"Differences from config/{name} (this environment vs git)"] = [
            f"{x['path']}: {short(x.get('before'))} → {short(x.get('after'))}" for x in dd[:40]] + (
            [f"… {len(dd) - 40} more"] if len(dd) > 40 else [])
    text = AD.report(name, env, sid, d.get("Title", ""), d.get("ReferenceType", ""), counts, SC.unverified(ss),
                     sorted(AD.referenced_sites(ss) - {v.get("id") for v in e_new["sites"].values() if v.get("id")}),
                     principals, undecided, f"releases/{rel}/", today, extra)

    # ---- write; environments.json last; on failure remove what this run created
    created: list[Path] = []
    ledger_before = ledger_p.read_text(encoding="utf-8") if ledger_p.exists() else None
    try:
        if not second_env:
            created.append(r / "config" / name)
            write_tree(model, r / "config" / name)
            ledger[name] = entries
            wj(ledger_p, ledger)
        created.append(r / "releases" / rel)
        wj(r / "releases" / rel / f"payload-{name}.json", payload_a)
        wj(r / "releases" / rel / "plan.json", plan_a)
        out = r / "ops" / "adopt" / f"{today}-{env}-{name}.md"
        created.append(out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        ev["envs"][env] = e_new
        if not managed:
            ev.setdefault("managed_sites", []).append(name)
        wj(r / "environments.json", ev)
    except Exception:
        import shutil
        for p in created:
            shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink(missing_ok=True)
        if ledger_before is None:
            ledger_p.unlink(missing_ok=True)
        else:
            ledger_p.write_text(ledger_before, encoding="utf-8")
        raise
    n_sus = sum(1 for x in extra["Site ids inside script bodies (become ${site:x}; review every SUSPICIOUS line)"] if x.startswith("SUSPICIOUS"))
    print(f"adopted site {sid} as '{name}' ({d.get('ReferenceType')}) from {env} — read only; nothing written to Pleasanter")
    if second_env:
        print(f"  second environment: id registered, config/{name} unchanged; "
              f"{len(extra[f'Differences from config/{name} (this environment vs git)'])} difference line(s) in the report")
    else:
        print(f"  config/{name}/, slot ledger: {len(entries) - nf} slot(s) defined or placed + {nf} only in the filter list "
              f"(zone customer)")
    print(f"  record releases/{rel}/ (drift baseline, not a release)")
    print(f"  findings: {len(SC.unverified(ss))} unverified component(s), {len(principals)} unmapped principal(s), "
          f"{len(undecided)} server script(s) without a decision, {n_sus} suspicious id replacement(s) in scripts")
    print(f"  report: {out.relative_to(r)}")
    return 0


# ---------------------------------------------------------------- new sites (ADR-0007)

def bootstrap_plan(r: Path, env: str, release: str) -> int:
    """Phase 1 of a first release: empty skeleton sites for every managed site that has no id in `env` yet.
    Phase 2 is the normal release-plan (updatesite with the complete payload) once the ids are bound, so every
    ${site:x} reference — also between new sites and inside scripts (D3) — resolves before anything is configured."""
    e = env_conf(r, env)
    if e.get("role") == "prod":
        raise Fail("production sites are created by the customer-side runner (ADR-0003)")
    parent = e.get("parent_id")
    if not isinstance(parent, int) or parent <= 0:
        raise Fail(f"environments.json envs.{env}.parent_id (folder for new sites) is missing")
    steps = []
    for site in envs(r).get("managed_sites", []):
        conf = e["sites"].get(site) or {}
        if conf.get("id"):
            continue
        if _adopted(r, site):
            print(f"{site}: adopted from another environment — not created here; adopt its copy in {env} "
                  f"(pls adopt --env {env} --site <id> --name {site})")
            continue
        if not conf.get("title"):
            raise Fail(f"envs.{env}.sites.{site}.title is missing")
        mp = r / "config" / site / "meta.json"
        if not mp.exists():
            raise Fail(f"config/{site}/meta.json is missing (ReferenceType comes from the design, ADR-0007)")
        rt = rj(mp).get("ReferenceType")
        if rt not in ("Sites", "Issues", "Results", "Wikis", "Dashboards"):
            raise Fail(f"config/{site}/meta.json: ReferenceType '{rt}' is not a site type")
        steps.append({"op": "createsite", "site": site, "parent_id": parent,
                      "payload": {"Title": conf["title"], "ReferenceType": rt, "Body": "", "SiteSettings": {}}})
    if not steps:
        print(f"{env}: every managed site already has an id — nothing to bootstrap")
        return 0
    plan = {"release": release, "env": env, "status": "planned", "parent_id": parent, "steps": steps,
            "next": f"pls bootstrap {release} (HTTP; binds the ids) — or runner bootstrapSites + pls bind --env {env} --release {release} --created SITE=ID …",
            "undo": "a person deletes the created sites in Pleasanter (agents never delete); then remove their ids"}
    wj(r / "releases" / release / "bootstrap.json", plan)
    print(f"bootstrap plan written to releases/{release}/bootstrap.json — create {', '.join(s['site'] for s in steps)} under {parent}")
    return 0


def new_sites(r: Path, env: str) -> set:
    """Sites created by a bootstrap in `env` that have no applied release yet."""
    out = set()
    for bp in sorted((r / "releases").glob("*/bootstrap.json")) if (r / "releases").exists() else []:
        b = rj(bp)
        if b.get("env") == env:
            out |= set(b.get("created", {}))
    return {s for s in out if not releases_for(r, env, s, "applied")}


def bind(r: Path, env: str, release: str, created: dict) -> int:
    bp = r / "releases" / release / "bootstrap.json"
    plan = rj(bp)
    if plan.get("env") != env:
        raise Fail(f"{bp.name} is for env '{plan.get('env')}', not '{env}'")
    want = {s["site"] for s in plan["steps"]}
    if set(created) - want:
        raise Fail(f"not in the bootstrap plan: {sorted(set(created) - want)}")
    allenv = envs(r)
    used = {str(s.get("id")) for x in allenv["envs"].values() for s in x["sites"].values() if s.get("id")}
    for site, sid in created.items():
        if not str(sid).isdigit():
            raise Fail(f"{site}: id '{sid}' is not a number")
        if str(sid) in used:
            raise Fail(f"{site}: id {sid} is already used in environments.json")
        allenv["envs"][env]["sites"][site]["id"] = int(sid)
        used.add(str(sid))
    wj(r / "environments.json", allenv)
    plan["created"] = {**plan.get("created", {}), **{k: int(v) for k, v in created.items()}}
    plan["status"] = "created" if set(plan["created"]) == want else "partial"
    plan["created_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    wj(bp, plan)
    print(f"bound {', '.join(f'{k}={v}' for k, v in created.items())} in environments.json ({env}); bootstrap {plan['status']}")
    return 0


# ---------------------------------------------------------------- project scaffold and skills (Step 4b D3)

FRAMEWORK = Path(__file__).resolve().parents[2]
LAUNCHER = """#!/usr/bin/env python3
\"\"\"Project launcher for the framework's pls (generated by `pls init`).
Framework path: env PLS_HOME, else "path" in .claude/framework.lock (relative to this folder).\"\"\"
import json
import os
import runpy
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
home = os.environ.get("PLS_HOME") or json.loads((here / ".claude" / "framework.lock").read_text(encoding="utf-8-sig"))["path"]
tool = (here / home).resolve() / "tools" / "pls" / "pls.py"
if not tool.exists():
    sys.exit(f"pls not found at {tool} - set 'path' in .claude/framework.lock or the PLS_HOME environment variable")
sys.argv[0] = str(tool)
sys.path.insert(0, str(tool.parent))
runpy.run_path(str(tool), run_name="__main__")
"""
PROJECT_DIRS = ["requirements/sources", "design/decisions", "design/probes", "config", "tests/api", "tests/results",
                "releases", "ops/drift", "migrations"]


def _tree_sha(d: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(x for x in d.rglob("*") if x.is_file()):
        h.update(f.relative_to(d).as_posix().encode() + b"\0" + f.read_bytes().replace(b"\r\n", b"\n") + b"\0")
    return h.hexdigest()


def _skill_versions(fw: Path) -> dict:
    out = {}
    readme = fw / "skills" / "README.md"
    for line in (readme.read_text(encoding="utf-8").splitlines() if readme.exists() else []):
        m = re.match(r"\|\s*`([a-z0-9-]+)`\s*\|[^|]*\|\s*([0-9.]+)\s*\|", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def _framework_skills(fw: Path) -> dict[str, Path]:
    return {d.name: d for d in sorted((fw / "skills").iterdir()) if (d / "SKILL.md").exists()}


def _framework_commit(fw: Path) -> str:
    import subprocess
    try:
        return subprocess.run(["git", "-C", str(fw), "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                              timeout=10).stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def _relpath(target: Path, base: Path) -> str:
    import os
    try:
        return Path(os.path.relpath(target, base)).as_posix()
    except ValueError:            # other drive on Windows
        return target.as_posix()


def sync_skills(proj: Path, fw: Path = FRAMEWORK) -> dict:
    dest = proj / ".claude" / "skills"
    vers, skills = _skill_versions(fw), {}
    for name, src in _framework_skills(fw).items():
        tgt = dest / name
        if tgt.exists():
            for f in sorted(tgt.rglob("*"), reverse=True):
                f.unlink() if f.is_file() else f.rmdir()
        for f in src.rglob("*"):
            if f.is_file():
                (tgt / f.relative_to(src)).parent.mkdir(parents=True, exist_ok=True)
                (tgt / f.relative_to(src)).write_bytes(f.read_bytes())
        skills[name] = {"version": vers.get(name, "?"), "sha256": _tree_sha(tgt)}
    lock_p = proj / ".claude" / "framework.lock"
    lock = rj(lock_p) if lock_p.exists() else {}
    lock.update({"framework": "ai-dlc-pleasanter", "path": lock.get("path") or _relpath(fw, proj),
                 "commit": _framework_commit(fw), "synced": datetime.now().astimezone().isoformat(timespec="seconds"),
                 "skills": skills})
    wj(lock_p, lock)
    return lock


def skills_check(proj: Path, fw: Path = FRAMEWORK) -> list[str]:
    lock = rj(proj / ".claude" / "framework.lock")
    fw_skills, problems = _framework_skills(fw), []
    for name, entry in sorted((lock.get("skills") or {}).items()):
        d = proj / ".claude" / "skills" / name
        if not isinstance(entry, dict) or "sha256" not in entry:
            problems.append(f"{name}: no hash in the lock (old format) - run `pls skills sync`")
        elif not d.exists():
            problems.append(f"{name}: missing in .claude/skills")
        elif _tree_sha(d) != entry["sha256"]:
            problems.append(f"{name}: project copy was edited (differs from the lock) - change skills in the framework, then sync")
        elif name in fw_skills and _tree_sha(fw_skills[name]) != entry["sha256"]:
            problems.append(f"{name}: framework has a newer version ({_skill_versions(fw).get(name, '?')}) - `pls skills sync` to upgrade")
    for name in sorted(set(fw_skills) - set(lock.get("skills") or {})):
        problems.append(f"{name}: in the framework but not installed - `pls skills sync`")
    return problems


def init_project(target: Path, stage: str, release_target: str, approver: str | None, fw: Path = FRAMEWORK) -> None:
    if target.exists() and any(target.iterdir()):
        raise Fail(f"{target} exists and is not empty - pls init only creates new projects")
    tpl = fw / "templates" / "project"
    for f in tpl.rglob("*"):
        if f.is_file():
            out = target / f.relative_to(tpl)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(f.read_bytes())
    for d in PROJECT_DIRS:
        (target / d).mkdir(parents=True, exist_ok=True)
        if not any((target / d).iterdir()):
            (target / d / ".keep").write_text("", encoding="utf-8")
    cm = target / "CLAUDE.md"
    text = cm.read_text(encoding="utf-8")
    text = re.sub(r"\| Stage \|.*\|", f"| Stage | `{stage}` |", text, count=1)
    text = re.sub(r"\| Release target \|.*\|", f"| Release target | `{release_target}` |", text, count=1)
    if approver:
        text = re.sub(r"\| Approvers \|.*\|", f"| Approvers | {approver} (all gates) |", text, count=1)
    text = re.sub(r"\| Role tests \|.*\|", "| Role tests | `deferred` |" if stage == "demo" else "| Role tests | `per-role keys` |", text, count=1)
    cm.write_text(text, encoding="utf-8")
    (target / "pls.py").write_text(LAUNCHER, encoding="utf-8")
    (target / ".claude").mkdir(exist_ok=True)
    wj(target / ".claude" / "framework.lock", {"path": _relpath(fw, target.resolve())})
    sync_skills(target, fw)


# ---------------------------------------------------------------- machine profile: one-time setup (D4 simplification)

def profile_dir() -> Path:
    import os
    return Path(os.environ.get("PLS_PROFILE_DIR") or Path.home() / ".pls" / "profiles")


def _lookup(client, path: str, column: str, value: str, id_field: str) -> int | None:
    """Exact match by name through /api/groups/get or /api/users/get (1.5.2, verified with an admin user)."""
    try:
        st, js, _ = client.call(path, {"View": {"ColumnFilterHash": {column: value}}})
    except Exception:          # noqa: BLE001 — lookup is a convenience; the person is asked instead
        return None
    hits = [x for x in ((js or {}).get("Response") or {}).get("Data") or [] if x.get(column) == value]
    return int(hits[0][id_field]) if st == 200 and len(hits) == 1 else None


def setup_profile(name: str, ask=input, ask_secret=None) -> dict:
    """Ask once per machine and Pleasanter environment; every `pls init` afterwards reuses the answers."""
    import getpass
    import pls_http as H
    ask_secret = ask_secret or getpass.getpass
    d = profile_dir()
    pf = d / f"{name}.json"
    old = rj(pf) if pf.exists() else {}

    def q(prompt, default=None):
        v = ask(f"{prompt}" + (f" [{default}]" if default else "") + ": ").strip()
        return v or (default or "")
    url = q("Pleasanter URL (e.g. https://pleasanter.example.com)", old.get("url")).rstrip("/")
    folder = q("Folder for the apps - its URL or id", str(old.get("parent_id") or "") or None)
    m = re.search(r"/items/(\d+)", folder) or re.fullmatch(r"\s*(\d+)\s*", folder)
    if not m:
        raise Fail(f"cannot read a folder id from {folder!r}")
    parent = int(m.group(1))
    d.mkdir(parents=True, exist_ok=True)
    keyfile = d / f"{name}.admin.key"
    secret = ask_secret("Your API key (hidden; Enter keeps the stored one): ").strip()
    if secret:
        keyfile.write_text(secret + "\n", encoding="utf-8")
        try:
            keyfile.chmod(0o600)
        except OSError:
            pass
    if not keyfile.exists():
        raise Fail("no API key stored yet - create one in Pleasanter (user menu > API settings) and run pls setup again")
    client = H.Client(url, keyfile.read_text(encoding="utf-8").strip())
    st, js, _ = client.call(f"/api/items/{parent}/getsite")
    if st != 200 or not js or js["Response"]["Data"].get("ReferenceType") != "Sites":
        raise Fail(f"folder {parent}: HTTP {st} - check the URL, the key and that the id is a folder")
    print(f"ok: folder {parent} '{js['Response']['Data'].get('Title')}' readable with your key")
    login = q("Your login id", old.get("login"))
    uid = _lookup(client, "/api/users/get", "LoginId", login, "UserId") if login else None
    if uid is None:
        uid = int(q(f"Your user id (login '{login}' not found automatically)", str(old.get("user_id") or "") or None))
    print(f"ok: you = User,{uid} (principal 'admin')")
    principals = {"admin": f"User,{uid}"}
    prof = {"url": url, "parent_id": parent, "login": login, "user_id": uid, "principals": principals,
            "keys": {"admin": f"file:{keyfile.as_posix()}"}, "default_key": "admin", "allow_write": True,
            "saved": datetime.now().astimezone().isoformat(timespec="seconds")}
    wj(pf, prof)
    print(f"profile '{name}' saved in {pf} (no key inside; the key file is next to it, outside every repository)")
    return prof


def apply_profile(target: Path, prof: dict, env: str = "dev") -> None:
    ev = rj(target / "environments.json")
    e = ev["envs"].setdefault(env, {"role": "dev", "sites": {}, "values": {}})
    e["parent_id"] = prof["parent_id"]
    e["principals"] = dict(prof["principals"])
    wj(target / "environments.json", ev)
    wj(target / ".pls" / "connections.json", {env: {"url": prof["url"], "keys": prof["keys"], "default_key": prof["default_key"],
                                                    "allow_write": prof.get("allow_write", True)}})


def bind_principals(r: Path, env: str, client) -> list[str]:
    """design/roles.json (written by P2, permission design) → envs.<env>.principals, ids looked up by name.
    Returns the groups/users that do not exist yet (the person creates them in Pleasanter)."""
    rf = r / "design" / "roles.json"
    if not rf.exists():
        raise Fail("design/roles.json not found - the roles come from the permission design in P2")
    roles = rj(rf).get("roles") or {}
    ev = rj(r / "environments.json")
    e = ev["envs"][env]
    pr = e.setdefault("principals", {})
    missing = []
    for role, spec in roles.items():
        if pr.get(role) and "<" not in str(pr[role]):
            print(f"{role}: {pr[role]} (already bound)")
            continue
        if spec.get("principal") == "User":
            uid = _lookup(client, "/api/users/get", "LoginId", spec.get("login", ""), "UserId")
            found, what = (f"User,{uid}" if uid else None), f"user with login '{spec.get('login')}'"
        else:
            gid = _lookup(client, "/api/groups/get", "GroupName", spec.get("group_name") or role, "GroupId")
            found, what = (f"Group,{gid}" if gid else None), f"group '{spec.get('group_name') or role}'"
        if found:
            pr[role] = found
            print(f"{role}: {found} ({what})")
        else:
            missing.append(what)
            print(f"{role}: MISSING - create the {what} in Pleasanter, then run pls principals again")
    wj(r / "environments.json", ev)
    return missing


def _git_first_commit(target: Path) -> str:
    import subprocess
    try:
        subprocess.run(["git", "init", "-q"], cwd=target, check=True, capture_output=True, timeout=30)
        subprocess.run(["git", "add", "-A"], cwd=target, check=True, capture_output=True, timeout=30)
        c = subprocess.run(["git", "commit", "-qm", "project created by pls init"], cwd=target, capture_output=True, text=True, timeout=30)
        return "git: first commit done" if c.returncode == 0 else "git: initialised; commit it yourself (" + (c.stderr.strip().splitlines() or ["?"])[-1] + ")"
    except (OSError, subprocess.SubprocessError):
        return "git: not found - run git init yourself"


# ---------------------------------------------------------------- HTTP transport commands (ADR-0008)

def _client(r: Path, env: str, key: str | None = None):
    import pls_http as H
    conn = H.load_connection(r, env)
    return H, conn, H.Client(conn["url"], H.resolve_key(conn, key))


def _confirm(release: str, yes: bool, what: str) -> bool:
    if yes:
        return True
    print(what)
    try:
        typed = input(f"type the release id to confirm ({release}): ").strip()
    except EOFError:
        typed = ""
    if typed != release:
        print("not confirmed — nothing written")
        return False
    return True


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def http_cmd(r: Path, a) -> int:
    import pls_http as H
    try:
        if a.cmd == "http-check":
            e = env_conf(r, a.env)
            conn = H.load_connection(r, a.env)
            sid = next((v["id"] for v in e["sites"].values() if v.get("id")), None) or e.get("parent_id")
            if not sid:
                raise H.TransportError(f"{a.env}: no site id or parent_id to read")
            bad = 0
            seen: dict = {}
            for k in sorted(conn.get("keys") or {}):
                try:
                    v = H.resolve_key(conn, k)
                except H.TransportError:
                    continue
                if v in seen:
                    bad += 1
                    print(f"{a.env}: keys '{seen[v]}' and '{k}' are the SAME key — role tests would run with one user's rights")
                seen.setdefault(v, k)
            for k in (a.key or sorted(conn.get("keys") or {})):
                try:
                    c = H.Client(conn["url"], H.resolve_key(conn, k))
                    st, js, _ = c.call(f"/api/items/{sid}/getsite")
                    note = (f" ({js['Response']['Data'].get('Title')})" if st == 200 and js else
                            " — key valid, this user has no access to that site (expected for restricted roles)" if st in (403, 404) else
                            " — key REJECTED" if st == 401 else " — unexpected")
                    print(f"{a.env} key '{k}': getsite {sid} → HTTP {st}{note}")
                    bad += st not in (200, 403, 404)
                except H.TransportError as ex:
                    bad += 1
                    print(f"{a.env} key '{k}': {ex}")
            print(f"writes: {'allowed' if e.get('role') in H.WRITABLE_ROLES and conn.get('allow_write') is True else 'refused'} "
                  f"(role {e.get('role')!r}, allow_write {conn.get('allow_write')!r})")
            try:
                print(SE.describe(a.env, SE.effects(e)))
            except ValueError as ex:
                bad += 1
                print(f"{a.env}: {ex} (ADR-0010)")
            rec = e.get("pleasanter") or {}
            build = None
            if rec:
                try:
                    build = PV.build_token(PV.fetch_login_page(conn["url"], timeout=5))
                except PV.PageError:
                    build = None
            if not rec:
                print(f"pleasanter: version not recorded — run `pls version --env {a.env}` (ADR-0009)")
            elif not build:
                print(f"pleasanter: recorded app {rec.get('app')}, build {rec.get('build')} — build NOT verified "
                      "(login page unreachable or token not found)")
            elif rec.get("build") and build != rec["build"]:
                print(f"pleasanter: WARNING build changed {rec['build']} → {build} since {rec.get('checked')} — "
                      f"run `pls version --env {a.env}` and record the new version (ADR-0009)")
            else:
                print(f"pleasanter: app {rec.get('app')}, build {rec.get('build')}, schema {rec.get('schema')} (checked {rec.get('checked')})")
            return 1 if bad else 0

        if a.cmd == "export":
            e = env_conf(r, a.env)
            _, _, c = _client(r, a.env)
            for site in a.site:
                if not e["sites"].get(site, {}).get("id"):
                    raise H.TransportError(f"site '{site}' has no id in {a.env}")
                out = r / ".pls" / "exports" / f"{a.env}-{site}-{_stamp()}.json"
                wj(out, c.export_site(e["sites"][site]["id"]))
                print(f"{site}: {out.relative_to(r)}")
            return 0

        if a.cmd == "apply":
            rel = r / "releases" / a.release
            plan = rj(rel / "plan.json")
            if not plan.get("sites"):
                raise H.TransportError("single-site plans: use pls release-plan (multi-site format) for the HTTP transport")
            e = env_conf(r, plan["env"])
            H_, conn, c = _client(r, plan["env"])
            H.assert_writable(e, conn, plan["env"])
            if plan.get("status") != "planned":
                raise H.TransportError(f"{a.release} has status {plan.get('status')!r}, not 'planned'")
            files = {f.name: rj(f) for f in rel.glob("*.json") if f.name.startswith(("payload-", "rollback-"))}
            try:
                eff = SE.effects(e)
            except ValueError as ex:
                raise H.TransportError(f"envs.{plan['env']}.{ex}")
            refusal, warning = SE.apply_refusal(plan["env"], eff, {s: plan["per_site"][s].get("side_effects") for s in plan["sites"]})
            if refusal:
                raise H.TransportError(refusal)
            if warning:
                print(warning)
            if not _confirm(a.release, a.yes, f"apply {a.release} to {plan['env']} ({conn['url']}): {' → '.join(plan['sites'])}, "
                                             f"{plan.get('classification')}" + (f"\n{warning}" if warning else "")):
                return 1
            res = H.apply_release(c, plan, files)
            for line in res["log"]:
                print(line)
            wj(rel / "apply-log.json", {"transport": "http", "at": datetime.now().astimezone().isoformat(timespec="seconds"), **res})
            if res["status"] != "applied-unverified":
                print(f"{a.release}: {res['status']}")
                return 1
            exports = []
            for site in plan["sites"]:
                out = r / ".pls" / "exports" / f"{plan['env']}-{site}-after-{a.release}.json"
                wj(out, c.export_site(plan["per_site"][site]["site_id"]))
                exports += ["--export", f"{site}={out}"]
            return main(["mark-applied", a.release, *exports])

        if a.cmd == "bootstrap":
            bp = r / "releases" / a.release / "bootstrap.json"
            plan = rj(bp)
            e = env_conf(r, plan["env"])
            if plan.get("status") == "created":
                raise H.TransportError(f"{a.release} was already created ({plan.get('created')}) — never create twice (S1)")
            done = set(plan.get("created") or {}) | {s for s, v in e["sites"].items() if v.get("id")}
            plan = dict(plan, steps=[s for s in plan["steps"] if s["site"] not in done])
            if not plan["steps"]:
                print(f"{a.release}: every site already has an id — nothing to create")
                return 0
            _, conn, c = _client(r, plan["env"])
            H.assert_writable(e, conn, plan["env"])
            if not _confirm(a.release, a.yes, f"create {[s['site'] for s in plan['steps']]} under {plan['parent_id']} in "
                                             f"{plan['env']} ({conn['url']}) — undo is manual (ADR-0007)"):
                return 1
            res = H.bootstrap(c, plan)
            for line in res["log"]:
                print(line)
            if res["created"]:
                bind(r, plan["env"], a.release, res["created"])
            return 0 if res["status"] == "created" else 1

        if a.cmd == "test":
            e = env_conf(r, a.env)
            conn = H.load_connection(r, a.env)
            cache: dict = {}

            def clients(role):
                k = role or conn.get("default_key") or "admin"
                if k not in cache:
                    cache[k] = H.Client(conn["url"], H.resolve_key(conn, k))
                return cache[k]
            H.assert_writable(e, conn, a.env)        # tests create records (TD-14b)
            fixtures = dict(x.split("=", 1) for x in a.var)
            missing = sorted({f"{sp_['id']}:{k}" for f in a.specs for sp_ in rj(Path(f))
                              for k, v in (sp_.get("vars") or {}).items() if str(v).startswith("<") and k not in fixtures})
            if missing:                                  # TD-14c: never send a literal "$name"
                raise H.TransportError("fixtures not given (use --var NAME=VALUE): " + ", ".join(missing))
            specs = []
            for f in a.specs:
                for spec in from_refs(rj(Path(f)), e):
                    if spec.get("vars") or fixtures:
                        spec["vars"] = {**{k: v for k, v in (spec.get("vars") or {}).items() if not str(v).startswith("<")}, **fixtures}
                    specs.append(spec)
            # A role test run with another role's key is worse than useless: refusals it expects may succeed
            # (slice #3: a 社員 test with the admin key deleted its fixture). Refuse before sending anything.
            roles = {x for sp_ in specs for x in [sp_.get("as_key")] + [st.get("as_key") for st in sp_["steps"]] if x}
            vals = {}
            for role in sorted(roles | {conn.get("default_key") or "admin"}):
                v = H.resolve_key(conn, role)
                if v in vals:
                    raise H.TransportError(f"keys '{vals[v]}' and '{role}' are the same key — use a key created by a user of each role")
                vals[v] = role
            sid = e["sites"][a.site]["id"]
            try:
                eff = SE.effects(e)
            except ValueError as ex:
                raise H.TransportError(f"envs.{a.env}.{ex}")
            if eff["mail"] not in SE.MAIL_SAFE:
                all_sites = {v["id"] for v in e["sites"].values() if v.get("id")}
                written = sorted({x for sp_ in specs if SE.test_writes(sp_) for x in SE.test_sites(sp_, sid, all_sites)})
                mailing = {}
                for x in written:
                    live = clients(None).export_site(x)["Response"]["Data"]["SiteSettings"]
                    els = sorted(SE.mail_elements(live))
                    if els:
                        mailing[x] = els
                refusal = SE.test_refusal(a.env, eff, mailing)
                if refusal:
                    raise H.TransportError(refusal)
            res = H.run_tests(clients, sid, specs, a.env)
            res["executed_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
            res["specs"] = [str(Path(f)) for f in a.specs]
            for t in res["tests"]:
                print(f"{t['status']:13} {t['id']:6} as {t['as']:8} {t.get('title') or ''}")
                if t["status"] not in ("pass", "pass-api-only"):
                    for line in t["log"]:
                        print(f"      {line}")
            name = "-".join(Path(f).stem for f in a.specs)
            out = Path(a.out) if a.out else r / "tests" / "results" / f"{a.env}-{datetime.now():%Y%m%d}-{name}-http.json"
            wj(out, res)
            print(f"results: {out}")
            return 0 if all(t["status"] in ("pass", "pass-api-only") for t in res["tests"]) else 1

        if a.cmd == "adopt":
            adopt_check_name(a.name)
            env_conf(r, a.env)
            _, _, c = _client(r, a.env)
            exp = c.export_site(a.site)                      # the only call to Pleasanter: getsite (read)
            stamp = _stamp()
            out = r / ".pls" / "exports" / f"{a.env}-{a.name}-adopt-{stamp}.json"
            wj(out, exp)
            return adopt(r, a.env, a.name, exp, datetime.now().astimezone().date().isoformat(), stamp)

        if a.cmd == "version":
            env_conf(r, a.env)                               # unknown env → clear error, not a traceback
            ev = rj(r / "environments.json")
            e = ev["envs"][a.env]
            conn = H.load_connection(r, a.env)
            try:
                build = PV.build_token(PV.fetch_login_page(conn["url"]))
            except PV.PageError as ex:
                raise H.TransportError(f"{a.env}: login page not readable ({ex})")
            client = H.Client(conn["url"], H.resolve_key(conn, None))
            schema = None
            for sid in [v["id"] for v in (e.get("sites") or {}).values() if v.get("id")] + [e.get("parent_id")]:
                if not sid:
                    continue
                try:                                         # first site this key can read
                    schema = PV.schema_version(client.export_site(sid)["Response"]["Data"])
                    break
                except H.TransportError:
                    continue
            new, msgs = PV.update_record(e.get("pleasanter"), build, schema, a.app, datetime.now().astimezone().date().isoformat())
            e["pleasanter"] = new
            wj(r / "environments.json", ev)
            print(f"{a.env}: app {new['app']}, build {new['build']}, schema {new['schema']}")
            for m in msgs:
                print(f"  {m}")
            return 1 if new["app"] == PV.UNKNOWN or not build or schema is None else 0

        if a.cmd == "backup":
            e = env_conf(r, a.env)
            _, _, c = _client(r, a.env)
            b = c.backup_records(e["sites"][a.site]["id"])
            out = Path(a.out) / f"{a.env}-{a.site}-{_stamp()}.json"
            wj(out, b)
            print(f"{b['count']} record(s) → {out}  (never commit backups, I7)")
            return 0
    except H.TransportError as ex:
        print(f"pls: {ex}", file=sys.stderr)
        return 2
    return 2


# ---------------------------------------------------------------- CLI

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="pls")
    sp = ap.add_subparsers(dest="cmd", required=True)
    for c in ("unpack", "diff", "drift", "classify", "plan", "slots"):
        s = sp.add_parser(c)
        s.add_argument("export")
        s.add_argument("--env", required=True)
        s.add_argument("--site", required=True)
        if c == "drift":
            s.add_argument("--baseline", help="payload.json to compare with (default: last applied release)")
        if c == "plan":
            s.add_argument("--release", required=True)
            s.add_argument("--accept-drift", help="path to the drift decision record that allows planning over drift")
            s.add_argument("--migration", action="append", help="migration folder required for data-impacting changes (ADR-0004); repeatable")
    s = sp.add_parser("pack")
    s.add_argument("--env", required=True)
    s.add_argument("--site", required=True)
    s.add_argument("--out")
    s = sp.add_parser("canon")
    s.add_argument("--site", required=True)
    s = sp.add_parser("release-plan")
    s.add_argument("--env", required=True)
    s.add_argument("--release", required=True)
    s.add_argument("--export", action="append", required=True, metavar="SITE=EXPORT", help="one per site in the release")
    s.add_argument("--accept-drift", help="path to the drift decision record that allows planning over drift")
    s.add_argument("--migration", action="append", help="migration folder required for data-impacting changes (ADR-0004); repeatable")
    s.add_argument("--accept-unverified", help="decision record that accepts components without round-trip evidence (ADR-0001)")
    s = sp.add_parser("bootstrap-plan")
    s.add_argument("--env", required=True)
    s.add_argument("--release", required=True)
    s = sp.add_parser("bind")
    s.add_argument("--env", required=True)
    s.add_argument("--release", required=True)
    s.add_argument("--created", action="append", required=True, metavar="SITE=ID", help="id returned by createsite")
    # HTTP transport (ADR-0008) — talks to Pleasanter with keys from .pls/connections.json
    s = sp.add_parser("http-check", help="check the connection and the key(s) of an environment")
    s.add_argument("--env", required=True)
    s.add_argument("--key", action="append", help="key name to check (default: every key of the connection)")
    s = sp.add_parser("export", help="getsite → .pls/exports/<env>-<site>-<time>.json")
    s.add_argument("--env", required=True)
    s.add_argument("--site", action="append", required=True)
    s = sp.add_parser("apply", help="apply a planned release over HTTP, then export and mark-applied")
    s.add_argument("release")
    s.add_argument("--yes", action="store_true", help="skip typing the release id (only when the person asks for it)")
    s = sp.add_parser("bootstrap", help="create the sites of a bootstrap plan over HTTP, then bind (ADR-0007)")
    s.add_argument("release")
    s.add_argument("--yes", action="store_true")
    s = sp.add_parser("test", help="run test specs over HTTP; each spec's as_key picks the role's key")
    s.add_argument("specs", nargs="+")
    s.add_argument("--env", required=True)
    s.add_argument("--site", required=True, help="default site of the specs (processes are read from it)")
    s.add_argument("--out", help="result file (default tests/results/<env>-<date>-<name>.json)")
    s.add_argument("--var", action="append", default=[], metavar="NAME=VALUE", help="fixture for spec vars (e.g. e=44656)")
    s = sp.add_parser("adopt", help="read-only: bring an existing site into this project (config, ledger, drift baseline, report)")
    s.add_argument("--env", required=True)
    s.add_argument("--site", required=True, type=int, help="id of the existing site")
    s.add_argument("--name", required=True, help="stable logical name, e.g. anken")
    s = sp.add_parser("version", help="record the Pleasanter version of an environment (build and schema detected; app label from /versions)")
    s.add_argument("--env", required=True)
    s.add_argument("--app", help="application version read on <url>/versions by a logged-in person, e.g. 1.5.2.0")
    s = sp.add_parser("backup", help="every record of a site → migrations/<dir>/backup/ (ADR-0004)")
    s.add_argument("--env", required=True)
    s.add_argument("--site", required=True)
    s.add_argument("--out", required=True)
    s = sp.add_parser("mark-applied")
    s.add_argument("release")
    s.add_argument("export", nargs="?", help="export of the target site taken right after applying (single-site plan)")
    s.add_argument("--export", dest="exports", action="append", metavar="SITE=EXPORT", help="multi-site plan: one per site")
    sp.add_parser("lint")
    sp.add_parser("coverage")
    s = sp.add_parser("init", help="create a new project repository (templates/project + skills + launcher)")
    s.add_argument("dir")
    s.add_argument("--stage", choices=["demo", "project"], default="demo")
    s.add_argument("--target", choices=["dev", "stg", "prod"], default="dev", help="release target of the project")
    s.add_argument("--approver", help="name of the person who approves the gates (demo stage)")
    s.add_argument("--profile", help="machine profile from `pls setup` (default: 'dev' if it exists)")
    s.add_argument("--no-git", action="store_true", help="do not run git init / first commit")
    s = sp.add_parser("setup", help="one-time: connect this machine to a Pleasanter environment (profile for every pls init)")
    s.add_argument("--profile", default="dev")
    s = sp.add_parser("principals", help="bind the roles of design/roles.json to group/user ids of an environment (read-only lookup)")
    s.add_argument("--env", required=True)
    s = sp.add_parser("skills", help="check the project skills against the lock and the framework, or sync them")
    s.add_argument("action", choices=["check", "sync"])
    a = ap.parse_args(argv)
    if a.cmd == "setup":
        setup_profile(a.profile)
        print("next: python <framework>/tools/pls/pls.py init <new project folder>")
        return 0
    if a.cmd == "init":
        target = Path(a.dir).resolve()
        pname = a.profile or ("dev" if (profile_dir() / "dev.json").exists() else None)
        prof = rj(profile_dir() / f"{pname}.json") if pname else None
        if a.profile and not prof:
            raise Fail(f"profile '{a.profile}' not found - run pls setup --profile {a.profile}")
        init_project(target, a.stage, a.target, a.approver)
        if prof:
            apply_profile(target, prof)
        msg = _git_first_commit(target) if not a.no_git else "git: skipped"
        if prof:
            print(f"created {target} with profile '{pname}' ({prof['url']}, folder {prof['parent_id']}); {msg}\n"
                  f"next: cd {target}  ->  python pls.py http-check --env dev  ->  open Claude Code here and give it the spec")
        else:
            print(f"created {target}; {msg}\nno machine profile yet: run `pls setup` once (docs/setup.md), "
                  "or fill environments.json and .pls/connections.json by hand")
        return 0
    r = root()
    if a.cmd == "skills":
        if a.action == "sync":
            lock = sync_skills(r)
            print("synced " + ", ".join(f"{k} {v['version']}" for k, v in lock["skills"].items()) + f" (framework {lock['commit']})")
            return 0
        problems = skills_check(r)
        print("\n".join(problems) if problems else "skills match the lock and the framework")
        return 1 if problems else 0

    if a.cmd == "principals":
        import pls_http as H
        try:
            _, _, c = _client(r, a.env)
            missing = bind_principals(r, a.env, c)
        except H.TransportError as ex:
            print(f"pls: {ex}", file=sys.stderr)
            return 2
        return 1 if missing else 0

    if a.cmd == "canon":
        p = r / "config" / a.site / "site.json"
        before = rj(p)
        after = canonicalize(before)
        wj(p, after)
        print(f"config/{a.site}/site.json: {'canonicalised' if after != before else 'already canonical'}")
        return 0

    if a.cmd in ("http-check", "export", "apply", "bootstrap", "test", "backup", "version", "adopt"):
        return http_cmd(r, a)

    if a.cmd == "bootstrap-plan":
        return bootstrap_plan(r, a.env, a.release)

    if a.cmd == "bind":
        return bind(r, a.env, a.release, dict(x.split("=", 1) for x in a.created))

    if a.cmd == "release-plan":
        exports = dict(x.split("=", 1) for x in a.export)
        return release_plan(r, a.env, a.release, exports, a.accept_drift, a.migration, a.accept_unverified)

    if a.cmd == "mark-applied" and (rj(r / "releases" / a.release / "plan.json").get("sites")):
        rel = r / "releases" / a.release
        plan = rj(rel / "plan.json")
        e = env_conf(r, plan["env"])
        exports = dict(x.split("=", 1) for x in (a.exports or []))
        if set(exports) != set(plan["sites"]):
            print(f"NOT marked as applied: need --export for exactly {plan['sites']}")
            return 1
        bad = False
        for site in plan["sites"]:
            pl = rj(rel / plan["per_site"][site]["payload_file"])
            want = logical({"SiteSettings": pl["SiteSettings"], "ReferenceType": pl.get("ReferenceType"), "Body": pl.get("Body", "")}, e)
            diffs = flat_diff(same_meta(logical(rj(Path(exports[site])), e), want), want)
            if diffs:
                bad = True
                print(md_diff(diffs, labels(want), f"{plan['env']}/{site}: live after apply vs release payload"))
        if bad:
            # The release WAS applied; Pleasanter stored some values differently (D8). Record that state as the
            # baseline so the fold-back release (P3 step 6) is not refused as drift (S2).
            for site in plan["sites"]:
                d = site_data(rj(Path(exports[site])))
                wj(rel / f"live-{site}.json", {k: d[k] for k in ("Title", "Body", "ReferenceType", "SiteSettings") if k in d})
            plan.update(status="applied-differs", applied_at=datetime.now().astimezone().isoformat(timespec="seconds"),
                        post_apply_check="live differs from the payload; live-<site>.json is the baseline — fold the "
                                         "differences into config/ and plan a follow-up release")
            wj(rel / "plan.json", plan)
            print(f"{a.release}: APPLIED WITH DIFFERENCES — fold them into config/ (P3 step 6) and plan the next release")
            return 1
        plan.update(status="applied", applied_at=datetime.now().astimezone().isoformat(timespec="seconds"),
                    post_apply_check="every site: live equals payload (pls mark-applied)")
        wj(rel / "plan.json", plan)
        print(f"{a.release} marked as applied to {plan['env']}: {', '.join(plan['sites'])}")
        return 0

    if a.cmd == "mark-applied":
        rel = r / "releases" / a.release
        plan = rj(rel / "plan.json")
        e = env_conf(r, plan["env"])
        pl = rj(rel / "payload.json")
        want = logical({"SiteSettings": pl["SiteSettings"], "ReferenceType": pl.get("ReferenceType"), "Body": pl.get("Body", "")}, e)
        got = same_meta(logical(rj(Path(a.export)), e), want)
        diffs = flat_diff(got, want)
        if diffs:
            print(md_diff(diffs, labels(want), f"{plan['env']}/{plan['site']}: live after apply vs release payload"))
            print("NOT marked as applied: the environment does not match the release payload")
            return 1
        plan.update(status="applied", applied_at=datetime.now().astimezone().isoformat(timespec="seconds"),
                    post_apply_check="live equals payload (pls mark-applied)")
        wj(rel / "plan.json", plan)
        print(f"{a.release} marked as applied to {plan['env']}/{plan['site']}")
        return 0

    if a.cmd == "unpack":
        e = env_conf(r, a.env)
        write_tree(logical(rj(Path(a.export)), e), r / "config" / a.site)
        print(f"unpacked {a.export} → config/{a.site}")
        return 0

    if a.cmd == "pack":
        e = env_conf(r, a.env)
        p = payload(read_tree(r / "config" / a.site), e, a.site)
        text = json.dumps(p, ensure_ascii=False, indent=2)
        (Path(a.out).write_text(text + "\n", encoding="utf-8") if a.out else print(text))
        return 0

    if a.cmd == "lint":
        issues = lint(r)
        for i in issues:
            print(f"{i['rule']}  {i['site']}  {i['msg']}")
        print(f"{len(issues)} issue(s)")
        return 1 if issues else 0

    if a.cmd == "coverage":
        c = coverage(r)
        for row in c["rows"]:
            print(f"{row['status']:8} {row['req']:10} config={row['config']} tests={row['passed']}/{row['tests']}"
                  + (f" missing={row['missing_config']}" if row["missing_config"] else ""))
        return 0 if c["ok"] else 1

    e = env_conf(r, a.env)
    live = logical(rj(Path(a.export)), e)
    git = read_tree(r / "config" / a.site)
    diffs = flat_diff(same_meta(live, git), git)

    if a.cmd == "diff":
        print(md_diff(diffs, labels(git) | labels(live), f"{a.env}/{a.site}: live vs git"))
        return 0

    if a.cmd == "drift":
        ddiffs, text = drift_report(r, e, a.env, a.site, rj(Path(a.export)), a.baseline)
        print(text)
        return 1 if ddiffs else 0

    if a.cmd == "classify":
        print(json.dumps(classify(diffs), ensure_ascii=False, indent=2))
        return 0

    if a.cmd == "slots":
        led = rj(r / "design/slot-ledger.json").get(a.site, {})
        coll = slot_collisions(live["settings"], git["settings"], led)
        for c in coll:
            print(f"SLOT {c['kind']:15} {c['msg']}")
        print(f"{a.env}/{a.site}: {len(coll)} slot issue(s)")
        return 1 if coll else 0

    if a.cmd == "plan":
        if e.get("role") == "prod":
            print("note: production plans are executed by the customer-side runner (ADR-0003)")
        export = rj(Path(a.export))
        drift_note = "no applied release recorded: first release, drift not checkable"
        if releases_for(r, a.env, a.site, "applied"):
            ddiffs, dtext = drift_report(r, e, a.env, a.site, export, None)
            if ddiffs and not a.accept_drift:
                print(dtext)
                print("plan REFUSED: the environment drifted from its last release (I2, D11). "
                      "Resolve the drift, or pass --accept-drift <decision record>.")
                return 1
            drift_note = "clean" if not ddiffs else f"drift accepted by {a.accept_drift}"
        ledger_p = r / "design/slot-ledger.json"
        if not ledger_p.exists():
            print("plan REFUSED: design/slot-ledger.json is missing — the slot-collision check cannot run (A2)")
            return 1
        coll = slot_collisions(live["settings"], git["settings"], rj(ledger_p).get(a.site, {}))
        if coll:
            for c in coll:
                print(f"SLOT {c['kind']:15} {c['msg']}")
            print("plan REFUSED: column-slot check failed (A2, ADR-0002). Resolve in the ledger / git first.")
            return 1
        cls = classify(diffs)
        if cls["classification"] == "data-impacting":
            probs = migration_problems(r, a.migration)
            if probs:
                for x in cls["data_impacting"]:
                    print(f"DATA {x}")
                for x in probs:
                    print(f"MIGRATION {x}")
                print("plan REFUSED: data-impacting change needs a migration (ADR-0004)")
                return 1
        live_site = site_data(export)
        new = payload(git, e, a.site)
        missing = sorted(set(live_site["SiteSettings"]) - set(new["SiteSettings"]) - {"ServerScripts", "Scripts", "Styles", "Htmls"})
        rel = r / "releases" / a.release
        snap = json.dumps(export, ensure_ascii=False, sort_keys=True)
        plan = {
            "release": a.release, "env": a.env, "site": a.site, "site_id": e["sites"][a.site]["id"],
            "status": "planned",
            "snapshot_sha256": hashlib.sha256(snap.encode()).hexdigest(),
            "checks": {"L-DEP-01_complete_payload": not missing, "keys_missing_from_payload": missing,
                       "drift_vs_last_release": drift_note, "slot_collisions": "clean",
                       "migration": a.migration if cls["classification"] == "data-impacting" else None},
            "classification": classify(diffs),
            "steps": [{"op": "updatesite", "site_id": e["sites"][a.site]["id"], "payload_file": "payload.json"}],
            "rollback": [{"op": "updatesite", "site_id": e["sites"][a.site]["id"], "payload_file": "rollback.json"}],
        }
        wj(rel / "plan.json", plan)
        wj(rel / "payload.json", new)
        wj(rel / "rollback.json", {k: live_site[k] for k in ("Title", "Body", "ReferenceType", "SiteSettings") if k in live_site})
        (rel / "raw-diff.md").write_text(md_diff(diffs, labels(git) | labels(live), f"{a.env}/{a.site}: live (before) vs git (after)"), encoding="utf-8")
        print(f"plan written to releases/{a.release}/ — {len(diffs)} change(s), {plan['classification']['classification']}"
              + ("" if not missing else f"; L-DEP-01 FAILED: {missing}"))
        return 1 if missing else 0
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Fail as ex:
        print(f"pls: {ex}", file=sys.stderr)
        sys.exit(2)
