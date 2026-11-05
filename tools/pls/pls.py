#!/usr/bin/env python3
"""pls — minimal, deterministic toolchain for AI-DLC Pleasanter projects (architecture §7.1).

Works on files only. Transport to Pleasanter (export / apply / run tests) is done by the
browser runner (tools/pls/browser/pls-runner.js) or a future HTTP client; this tool never
talks to Pleasanter itself, so it can never write to an environment (invariant I3).

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
  mark-applied <release> <export.json>          verify live == release payload, then record the release as applied
  mark-applied <release> --export S=F …         same for a multi-site plan (every site must match)
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
    return json.loads(p.read_text(encoding="utf-8"))


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
    ids = {str(v["id"]): k for k, v in e["sites"].items()}
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
    if "Permissions" in d or "InheritPermission" in d:
        model["permissions"] = perms_to_refs(d, e)
    return model


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
        index = []
        for it in items:
            name = it.get("Name") or f"script-{it.get('Id')}"
            (out / folder).mkdir(parents=True, exist_ok=True)
            (out / folder / f"{name}{ext}").write_text(it.get("Body", ""), encoding="utf-8")
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
                it["Body"] = (d / folder / f).read_text(encoding="utf-8")
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
    m = from_refs(copy.deepcopy(model), e)
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
        else:
            cfg.append(p)
    cls = "data-impacting" if data else "permission-impacting" if perm else "config-only"
    return {"classification": cls, "data_impacting": data, "permission_impacting": perm, "config_only": cfg}


# ---------------------------------------------------------------- lint (architecture §7.2)

def lint(r: Path) -> list[dict]:
    issues: list[dict] = []
    e_all = envs(r)
    all_ids = {str(s["id"]) for e in e_all["envs"].values() for s in e["sites"].values()}
    ledger = rj(r / "design/slot-ledger.json") if (r / "design/slot-ledger.json").exists() else None
    decisions = "\n".join(p.read_text(encoding="utf-8") for p in (r / "design").rglob("*.md")) if (r / "design").exists() else ""
    for site_dir in sorted((r / "config").iterdir()):
        if not site_dir.is_dir():
            continue
        site = site_dir.name
        m = read_tree(site_dir)
        blob = json.dumps(m, ensure_ascii=False)
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
            used = {c["ColumnName"] for c in m["settings"].get("Columns", []) if re.match(r"^(Class|Num|Date|Description|Check|Attachments)\w+$", c["ColumnName"])}
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
        passed = [t for t in tests if results.get(t) == "pass"]
        missing_cfg = [c for c in cfg if not (r / c.split("#")[0]).exists()]
        good = bool(cfg) and not missing_cfg and bool(tests) and len(passed) == len(tests)
        ok &= good
        rows.append({"req": req, "config": len(cfg), "missing_config": missing_cfg, "tests": len(tests),
                     "passed": len(passed), "status": "covered" if good else "GAP"})
    return {"ok": ok, "rows": rows}


# ---------------------------------------------------------------- releases and drift baseline (S2, S3, D11)

def releases_for(r: Path, env: str, site: str, status: str | None = None) -> list[tuple[Path, dict]]:
    out = []
    for p in sorted((r / "releases").glob("*/plan.json")) if (r / "releases").exists() else []:
        plan = rj(p)
        in_plan = plan.get("site") == site or site in (plan.get("sites") or [])
        if plan.get("env") == env and in_plan and (status is None or plan.get("status") == status):
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


def migration_problems(r: Path, mig: str | None) -> list[str]:
    """Data-impacting gate (ADR-0004): a migration folder with the conversion (migration.json: site, keys,
    bulkupsert data or mapping), the backup of the affected records taken before (folder `backup/`,
    exported with the runner's backupRecords) and the log of a dry run on a copy (dry-run.md)."""
    if not mig:
        return ["data-impacting change without --migration DIR (ADR-0004)"]
    d = (r / mig) if not Path(mig).is_absolute() else Path(mig)
    out = [f"{mig}/{f} is missing" for f in MIGRATION_FILES if not (d / f).exists()]
    if (d / "backup").is_dir() and not any((d / "backup").iterdir()):
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


def plan_site(r: Path, e: dict, env: str, site: str, export: Any, accept_drift: str | None) -> tuple[bool, list, dict]:
    """All pre-deploy checks for one site. Returns (ok, messages, result)."""
    msgs = []
    live = logical(export, e)
    git = read_tree(r / "config" / site)
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
        "checks": {"L-DEP-01_complete_payload": True, "drift_vs_last_release": drift_note, "slot_collisions": "clean"},
        "payload": new,
        "rollback": {k: live_site[k] for k in ("Title", "Body", "ReferenceType", "SiteSettings") if k in live_site},
        "raw_diff": md_diff(diffs, labels(git) | labels(live), f"{env}/{site}: live (before) vs git (after)"),
        "deps": site_deps(git, site, set(e["sites"])),
    }


def release_plan(r: Path, env: str, release: str, exports: dict, accept_drift: str | None, migration: str | None = None) -> int:
    e = env_conf(r, env)
    if e.get("role") == "prod":
        print("note: production plans are executed by the customer-side runner (ADR-0003)")
    results, failed = {}, False
    for site, path in sorted(exports.items()):
        if site not in e["sites"]:
            raise Fail(f"site '{site}' is not in environments.json for {env}")
        ok, msgs, res = plan_site(r, e, env, site, rj(Path(path)), accept_drift)
        for m in msgs:
            print(m)
        failed |= not ok
        results[site] = res
    if failed:
        print("release plan REFUSED: no files written")
        return 1
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
        per_site[s] = {k: res[k] for k in ("site_id", "changes", "classification", "snapshot_sha256", "snapshot_updated_time", "checks")}
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
    }
    wj(rel / "plan.json", plan)
    print(f"release plan written to releases/{release}/ — order: {' → '.join(order)}"
          + (f" (cycle: {cyc})" if cyc else "") + f"; {sum(p['changes'] for p in per_site.values())} change(s), {worst}")
    return 0


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
            s.add_argument("--migration", help="migration folder required for data-impacting changes (ADR-0004)")
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
    s.add_argument("--migration", help="migration folder required for data-impacting changes (ADR-0004)")
    s = sp.add_parser("mark-applied")
    s.add_argument("release")
    s.add_argument("export", nargs="?", help="export of the target site taken right after applying (single-site plan)")
    s.add_argument("--export", dest="exports", action="append", metavar="SITE=EXPORT", help="multi-site plan: one per site")
    sp.add_parser("lint")
    sp.add_parser("coverage")
    a = ap.parse_args(argv)
    r = root()

    if a.cmd == "canon":
        p = r / "config" / a.site / "site.json"
        before = rj(p)
        after = canonicalize(before)
        wj(p, after)
        print(f"config/{a.site}/site.json: {'canonicalised' if after != before else 'already canonical'}")
        return 0

    if a.cmd == "release-plan":
        exports = dict(x.split("=", 1) for x in a.export)
        return release_plan(r, a.env, a.release, exports, a.accept_drift, a.migration)

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
            print("NOT marked as applied: at least one site does not match its release payload")
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
