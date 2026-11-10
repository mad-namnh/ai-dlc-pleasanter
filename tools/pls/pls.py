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
  gate G1..G4 --approver N --quote Q            record a gate decision the person stated (I4)
  profile set FIELD VALUE [--env E] --approver N --quote Q
                                                set Approvers / Operators / Origin (CLAUDE.md) or role (environments.json)
                                                as the person stated it; recorded under gates/profile/ (I4)
  review as-is SITE --approver N --quote Q      the person reviewed design/as-is/SITE.md (clears L-LAD-01 via DES-000)
  lint                                          rule catalogue (L-SEC-01, L-REF-01, L-SCR-01, L-SCR-02, L-SLOT-01, L-LAD-01, L-CAN-01, L-MAIL-01, L-ENV-02, L-MRG-01, L-PRC-01, L-GATE-01, L-JOB-01, L-ONB-01, L-PRF-01)
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
  jobs-verified <release> --by N --quote "…" [--approved-by G4]
                                                an operator (or G4 approver) deployed and checked the release's scheduled scripts (ADR-0012)
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
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))   # pls_http (ADR-0008)
import pls_side_effects as SE                               # noqa: E402 — mail and job safety (ADR-0010)
import pls_version as PV                                    # noqa: E402 — Pleasanter version label (ADR-0009)
import pls_scope as SC                                      # noqa: E402 — components proven to round-trip (ADR-0001)
import pls_adopt as AD                                      # noqa: E402 — adopting existing sites (BR4)
import pls_compare as CMP                                   # noqa: E402 — one site across environments (BR5)
import pls_scripts as SX                                    # noqa: E402 — script tooling (BR7)
import pls_merge as MG                                      # noqa: E402 — semantic merge of site.json (BR6)
import pls_kbverify as KV                                   # noqa: E402 — executable KB verification (BR8)
import pls_gate as GT                                       # noqa: E402 — gate decisions as records (I4)
import pls_profile_records as PR                            # noqa: E402 — profile records (I4)
import pls_as_is_review_records as AR                       # noqa: E402 — as-is review records (I4, I5)
import pls_log as LG                                        # noqa: E402 — run log and step markers (ADR-0013)
import pls_usage as US                                      # noqa: E402 — LLM token usage per step (ADR-0013)
import pls_spec as SP                                       # noqa: E402 — as-is specification skeleton
import pls_report as RP                                     # noqa: E402 — operator part of the release report

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
    # one quoted literal right after the name (the blob is JSON-escaped: quotes may be \"): the value has no blank
    # and no escape such as \n, and closes with the same quote — so `'…access_token=' + encode(accessToken)` spanning
    # lines is not a secret (PLAY BOARD false alarm, 2026-11-08)
    "assigned-secret": re.compile(r"""(?i)(api[_-]?key|secret|password|token)\\?["']?\s*[:=]\s*\\?(["'])[^"'\s\\]{12,}\\?\2"""),
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
    # only text values can appear inside config text; a number (e.g. kb_probe_parent) is never replaced
    vals = {v: k for k, v in (e.get("values") or {}).items() if isinstance(v, str) and v}
    return ids, vals


def to_refs(obj: Any, ids: dict, vals: dict, key: str = "", literal: dict | None = None,
            reference: dict | None = None) -> Any:
    """Replace env-specific values with ${site:x} / ${env:x} references. Site ids in strings only where they are
    written as site ids (pls_scripts.ID_CONTEXT). `literal` / `reference`: a person's decisions for numbers in the
    script bodies of one site (BR7)."""
    if isinstance(obj, dict):
        return {k: to_refs(v, ids, vals, k, literal, reference) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_refs(v, ids, vals, key, literal, reference) for v in obj]
    if isinstance(obj, int) and not isinstance(obj, bool) and key.endswith("SiteId") and str(obj) in ids:
        return "${site:%s}" % ids[str(obj)]
    if isinstance(obj, str):
        s = obj
        for v, name in sorted(vals.items(), key=lambda x: -len(x[0])):
            s = s.replace(v, "${env:%s}" % name)
        return SX.replace_ids(s, ids, literal, reference)   # id contexts only; a person's decisions (BR7)
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
            return str(val)
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
        "meta": to_refs({k: d.get(k) for k in META_FIELDS if k in d}, ids, vals),
        "settings": to_refs(ss, ids, vals),
        "scripts": to_refs(scripts, ids, vals, literal=SX.for_site(ids.get(str(d.get("SiteId")))),
                           reference=SX.references_for(ids.get(str(d.get("SiteId"))), ids)),
    }
    acl_to_refs(model["settings"], e)
    if "Permissions" in d or "InheritPermission" in d:
        model["permissions"] = perms_to_refs(d, e)
    if "Title" in d:      # per environment (environments.json title): compared on read-back, never written to git
        model["title"] = d["Title"]
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
    if "_pls_conflicts" in model["settings"]:
        raise Fail(f"{site}: unresolved merge conflicts in config/{site}/site.json (_pls_conflicts) — resolve them first")
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
        def k0(x):
            return str(x.get("ColumnName", x.get("Name", x.get("Id"))))
        # Names can repeat (server scripts, processes in real sites). A repeated name is keyed "Name@Id" when every
        # item with that name on both sides has an Id (stable within a site), else by occurrence "Name#2", "Name#3" …
        # Decided on both lists together, so both sides use the same keys; no item is ever hidden behind another.
        repeated = {k for lst in (a, b) for k, n in Counter(map(k0, lst)).items() if n > 1}
        by_id = {k for k in repeated if all("Id" in x for x in a + b if k0(x) == k)}

        def keyed(items):
            out_, seen = {}, Counter()
            for x in items:
                k = k0(x)
                seen[k] += 1
                if k in by_id:
                    k = f"{k}@{x['Id']}"
                elif k in repeated and seen[k] > 1:
                    k = f"{k}#{seen[k]}"
                while k in out_:                 # a real name such as "init#2" must not overwrite a suffixed one
                    k += "#"
                out_[k] = x
            return out_
        ka, kb = keyed(a), keyed(b)
        for k in sorted(set(ka) | set(kb), key=str):
            p = f"{path}[{k}]"
            if k not in kb:
                out.append({"path": p, "kind": "removed", "before": ka[k], "after": None})
            elif k not in ka:
                out.append({"path": p, "kind": "added", "before": None, "after": kb[k]})
            else:
                out += flat_diff(ka[k], kb[k], p)
        if [k for k in ka if k in kb] != [k for k in kb if k in ka]:
            out.append({"path": path, "kind": "reordered", "before": list(ka), "after": list(kb)})
    elif a != b:
        out.append({"path": path, "kind": "changed", "before": a, "after": b})
    return out


def short(v: Any, n: int = 70) -> str:
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    s = s.replace("\n", "⏎").replace("|", "\\|")
    return s if len(s) <= n else s[: n - 1] + "…"


def labels(model: dict) -> dict:
    return {c["ColumnName"]: c.get("LabelText", c["ColumnName"]) for c in model["settings"].get("Columns", [])}


def md_diff(diffs: list[dict], lab: dict, title: str, right: str = "After (git)", kinds: dict | None = None) -> str:
    """`kinds` renames the kind column for the reader (drift: what exists where, not what a release would do)."""
    kinds = kinds or {}
    rows = [f"### {title}", "", f"{len(diffs)} difference(s).", ""]
    if diffs:
        rows += [f"| Path | Kind | Label | Before (live) | {right} |", "|---|---|---|---|---|"]
        for d in diffs:
            m = re.search(r"\[(\w+)\]", d["path"])
            rows.append(f"| `{d['path']}` | {kinds.get(d['kind'], d['kind'])} | {lab.get(m.group(1), '') if m else ''} | "
                        f"{short(d['before']) if d['before'] is not None else ''} | {short(d['after']) if d['after'] is not None else ''} |")
    return "\n".join(rows) + "\n"


# ---------------------------------------------------------------- classify (ADR-0004)

def _lookup_json(text: Any) -> Any:
    """A ChoicesText that is a JSON lookup / link definition (`[{"SiteId": …}]`), normalised for comparison: layout,
    and numbers versus strings (`"Status": 1` / `"1"`, as a site package import re-serialises it), do not count.
    None when the text is a list of choices."""
    s = str(text or "").strip()
    if not s.startswith(("[", "{")) or s.startswith("[["):
        return None
    try:
        lenient = re.sub(r",(\s*[}\]])", r"\1", SX.REF_TOKEN.sub(lambda m: json.dumps(m.group(0)), s))
        doc = json.loads(lenient)                       # Pleasanter accepts trailing commas; an import drops them
    except ValueError:
        return None

    def norm(v: Any) -> Any:
        if isinstance(v, dict):
            return {k: norm(x) for k, x in v.items()}
        if isinstance(v, list):
            return [norm(x) for x in v]
        return v if isinstance(v, (bool, type(None))) else str(v)
    return norm(doc)


def classify(diffs: list[dict]) -> dict:
    data, perm, cfg = [], [], []
    for d in diffs:
        p = d["path"]
        if p.startswith("settings.Columns[") and d["kind"] == "removed" and p.count("[") == 1:
            data.append(f"{p}: column definition removed")
        elif re.match(r"settings\.Columns\[\w+\]\.ChoicesText", p) and d["kind"] in ("changed", "removed"):
            before = set(str(d["before"] or "").splitlines())
            after = set(str(d["after"] or "").splitlines())
            jb, ja = _lookup_json(d["before"]), _lookup_json(d["after"])
            if jb is not None and ja is not None:       # a lookup / link definition, not a list of choices
                if jb == ja:
                    cfg.append(p)
                else:
                    data.append(f"{p}: lookup / link definition changed")
            elif before - after:
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

VIEW_DEFAULTS = {"Id", "ApiColumnKeyDisplayType", "ApiColumnValueDisplayType", "ApiDataType", "CalendarSiteId"}


def unconditioned_processes(settings: dict, view_missing_only: bool = False) -> list[str]:
    """Processes without a display condition. view_missing_only=True: only those with no View object at all (D21: API
    execution fails with HTTP 500 and opening the site's records fails in the UI). Otherwise also those whose View holds
    only defaults (they work, through the UI and the API; the button shows in every record of their CurrentStatus)."""
    out = []
    for p in settings.get("Processes") or []:
        view = p.get("View")
        if not isinstance(view, dict):
            out.append(str(p.get("Name") or p.get("DisplayName") or p.get("Id")))
        elif not view_missing_only and not {k: v for k, v in view.items() if k not in VIEW_DEFAULTS and v not in (None, {}, [], "")}:
            out.append(str(p.get("Name") or p.get("DisplayName") or p.get("Id")))
    return out


TOP_LEVEL_DECL = re.compile(r"(?m)^\s*(const|let)\s+\w")


def lint_jobs(r: Path, e_all: dict, all_ids: set) -> list[dict]:
    """The server-script rules on the bodies of scheduled scripts (ADR-0012 decision 2): L-REF-01 (no raw site id in
    an id context), L-SEC-01, L-SCR-01 (top-level const/let in a shared script, D7) and L-SCR-02 (`node --check` of
    the body as deployed: resolved for every environment that can receive it; sandboxes never do). A bad layout is
    L-JOB-01's job, so it is skipped here."""
    issues: list[dict] = []

    def add(rule: str, msg: str) -> None:
        issues.append({"rule": rule, "site": "_tenant", "msg": f"scheduled script {msg}"})
    try:
        raw = SE.load_jobs(r)
    except ValueError:
        return issues
    for name, j in raw.items():
        body = j["body"] or ""
        for i in sorted(all_ids):
            if SX.literal_left(body, i):
                add("L-REF-01", f"{name}: site id {i} written as a site id; use ${{site:…}}")
        blob = json.dumps(j, ensure_ascii=False)
        for sname, rx in SECRET_RES.items():
            if rx.search(blob):
                add("L-SEC-01", f"{name}: secret-like value ({sname})")
        entry = j["entry"] if isinstance(j["entry"], dict) else {}
        if (entry.get("shared") or entry.get("Shared")) and TOP_LEVEL_DECL.search(body):
            add("L-SCR-01", f"{name}: shared script declares top-level const/let (D7)")
    code: dict[str, list[str]] = {}                               # resolved body → "<name> (<env>)" labels
    for env_name, ec in sorted(e_all["envs"].items()):
        if ec.get("sandbox_of"):
            continue
        try:
            jobs = SE.load_jobs(r, lambda x, ec=ec: from_refs(x, ec))
        except Fail as ex:
            add("L-REF-02", f"references cannot be resolved for env '{env_name}': {ex}")
            continue
        for name, j in jobs.items():
            if j["body"] is not None:
                code.setdefault(j["body"], []).append(f"{name} ({env_name})")
    if code and not SX.node_available():
        print("warning: _tenant: L-SCR-02 skipped for scheduled scripts — node not found", file=sys.stderr)
    elif code:
        try:
            for err in SX.syntax_errors([(f"scheduled/{', '.join(labels)}", body, True) for body, labels in code.items()]):
                add("L-SCR-02", f"{err['label']} line {err['line']}: {err['message']}")
        except RuntimeError as ex:
            add("L-SCR-02", f"syntax check not run: {ex}")
    return issues


def lint(r: Path) -> list[dict]:
    issues: list[dict] = []
    e_all = envs(r)
    all_ids = {str(s["id"]) for e in e_all["envs"].values() for s in e["sites"].values() if s.get("id")}
    ledger = rj(r / "design/slot-ledger.json") if (r / "design/slot-ledger.json").exists() else None
    decided = AR.ladder_decided(r)                              # L-LAD-01: a reviewed as-is counts only via its record
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
    for x in SE.job_problems(r):                                  # L-JOB-01: scheduled scripts declared consistently (ADR-0012)
        issues.append({"rule": "L-JOB-01", "site": "_tenant", "msg": f"{SE.JOBS_DIR.as_posix()}/{x}"})
    issues += lint_jobs(r, e_all, all_ids)
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
                    if SX.literal_left(body, i, SX.for_site(site)):
                        issues.append({"rule": "L-REF-01", "site": site, "msg": f"{kind}/{nm}: site id {i} written as a site id; "
                                       "use ${site:…}, or record it as a literal number (pls refs --keep)"})
                for name in sorted(set(SX.unstable_refs(body, site))):        # L-REF-03: round trip would lose it
                    issues.append({"rule": "L-REF-03", "site": site, "msg": f"{kind}/{nm}: ${{site:{name}}} outside a site-id context "
                                   "becomes a plain number on the next unpack; write it as a site id (…SiteId = ${site:…}) "
                                   "or record it (pls refs --ref)"})
                if kind == "ServerScripts" and it.get("Shared") and TOP_LEVEL_DECL.search(body):
                    issues.append({"rule": "L-SCR-01", "site": site, "msg": f"shared server script '{nm}' declares top-level const/let (D7)"})
                if kind == "ServerScripts" and not it.get("Shared") and nm and not decided(nm):
                    issues.append({"rule": "L-LAD-01", "site": site, "msg": f"server script '{nm}' has no design decision (ladder reason, I5)"})
        for name in unconditioned_processes(m["settings"], view_missing_only=True):   # L-PRC-01 (D21)
            issues.append({"rule": "L-PRC-01", "site": site, "msg": f"process '{name}' has no View object: API execution fails "
                           "(HTTP 500) and opening the site's records fails in the UI (D21) — give it a View with its display "
                           "condition, at least the status it starts from"})
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
        code = [(f"{k}/{it.get('Name') or it.get('Title') or it.get('Id')}", it.get("Body") or "", k == "ServerScripts")
                for k in ("ServerScripts", "Scripts") for it in m["scripts"].get(k) or []]
        if code and not SX.node_available():                      # L-SCR-02: scripts compile (nothing is run)
            print(f"warning: {site}: L-SCR-02 skipped — node not found, scripts were not compiled", file=sys.stderr)
        elif code:
            try:
                for err in SX.syntax_errors(code):
                    issues.append({"rule": "L-SCR-02", "site": site, "msg": f"{err['label']} line {err['line']}: {err['message']}"})
            except RuntimeError as ex:
                issues.append({"rule": "L-SCR-02", "site": site, "msg": f"syntax check not run: {ex}"})
        if "_pls_conflicts" in m["settings"]:
            issues.append({"rule": "L-MRG-01", "site": site, "msg": f"unresolved merge conflicts: {m['settings']['_pls_conflicts']}"})
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
    issues += GT.lint(r)                                          # L-GATE-01: approvals in documents have records (I4)
    issues += PR.lint(r)                                          # L-PRF-01: guard inputs set through pls profile set
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


def _jobs_verified_holds(r: Path, v, env: str) -> bool:
    """A `jobs.verified` entry counts only as `pls jobs-verified` writes it: the person's words, and a name the profile
    still accepts for this environment (a hand-written entry by anyone else is not a confirmation)."""
    if not isinstance(v, dict) or not isinstance(v.get("quote"), str) or not v["quote"].strip() or v.get("env") != env:
        return False
    try:
        GT.job_verifier(r, str(v.get("by") or ""), env, v.get("approved_by"))
    except GT.GateError:
        return False
    return True


def last_applied_jobs(r: Path, env: str) -> dict | None:
    """Scheduled-script fingerprints of the last applied release of env whose jobs are known to be on the tenant
    (ADR-0012): it changed none, or a person recorded the manual deploy (`pls jobs-verified`). None when there is no
    such release (releases made before the jobs check, adoption records, sandboxes, hand-broken records)."""
    best = None
    for p in sorted((r / "releases").glob("*/plan.json")) if (r / "releases").exists() else []:
        plan = rj(p)
        jobs = plan.get("jobs")
        if plan.get("env") != env or plan.get("status") not in APPLIED or SE.bad_plan_jobs(jobs) or jobs.get("fingerprints") is None:
            continue
        if jobs["changed"] and not _jobs_verified_holds(r, jobs.get("verified"), env):
            continue                                   # manual deploy not confirmed: its changes are listed again
        key = (_applied_key(plan.get("applied_at")), plan.get("release") or "")
        if best is None or key > best[0]:
            best = (key, jobs["fingerprints"])
    return best[1] if best else None


CHANGE_PHASES = ("P1", "P2", "P3", "P4", "P5", "G1", "G2", "G3", "G4")   # change work; onboarding, P6 and other are not


def need_onboarding(r: Path, what: str) -> None:
    """Change work on a taken-over app (Origin `existing`) waits for its onboarding summary (lifecycle section 0)."""
    try:
        GT.require_onboarding(r, what)
    except GT.GateError as ex:
        raise Fail(str(ex))


def jobs_verified(r: Path, release: str, by: str, quote: str, approved_by: str | None = None) -> int:
    """Record the person's check of the manual scheduled-script deploy (ADR-0012 option B): an operator of the
    release's environment or a G4 approver, in their own words (I4). Until it is recorded, the release is not a
    baseline for jobs and the next release lists the same changes again."""
    p = r / "releases" / release / "plan.json"
    if not p.exists():
        raise Fail(f"releases/{release}/plan.json not found")
    plan = rj(p)
    jobs = plan.get("jobs")
    if SE.bad_plan_jobs(jobs) or not jobs["changed"]:
        raise Fail(f"{release} records no scheduled-script changes — nothing to verify")
    if plan.get("status") not in APPLIED:
        raise Fail(f"{release} has status {plan.get('status')!r}: apply and mark-applied it first")
    if not quote.strip():
        raise Fail("--quote: the person's own words are required (I4)")
    try:
        rec = GT.job_verifier(r, by, plan.get("env") or "", approved_by)
    except GT.GateError as ex:
        raise Fail(str(ex))
    jobs["verified"] = {**rec, "quote": quote.strip(), "at": datetime.now().astimezone().isoformat(timespec="seconds")}
    wj(p, plan)
    print(f"{release}: scheduled scripts on {rec['env']} verified by {rec['by']} ({rec['role']})"
          + (f", approved by {rec['approved_by']}" if rec.get("approved_by") else "") + f": {'; '.join(jobs['changed'])}")
    return 0


def rendered_jobs(r: Path, e: dict) -> dict[str, dict]:
    """The project's scheduled scripts with references resolved for one environment (raises ValueError / Fail)."""
    return SE.load_jobs(r, lambda x: from_refs(x, e))


def env_effects(r: Path, e: dict) -> dict:
    """Declared side effects of an environment; a sandbox shares its base's server and tenant (ADR-0011), so the riskier
    of its own copy and the base's current value counts. Raises ValueError on an unknown value."""
    eff = SE.effects(e)
    return SE.cautious(eff, SE.effects(env_conf(r, e["sandbox_of"]))) if e.get("sandbox_of") else eff


def _applied_key(ts: str | None) -> float:
    """Sort key for applied_at. Timestamps carry different UTC offsets (+09:00 written by hand, +00:00 by
    mark-applied), so they must be compared as instants, not as strings. Missing/naive -> oldest/UTC."""
    if not ts:
        return float("-inf")
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def payload_model(pl: dict, e: dict, site: str | None) -> dict:
    """A release payload read back as the logical model. The payload carries no SiteId, but per-site decisions on
    script numbers (pls refs --ref / --keep) are keyed by the site, so its id in `e` is passed along — without it a
    recorded reference renders as a plain number and every round trip shows false differences."""
    d = {"SiteSettings": pl["SiteSettings"], "ReferenceType": pl.get("ReferenceType"), "Body": pl.get("Body", "")}
    # everything the payload writes is read back: the title and, when git manages them, the permissions (D15)
    d.update({k: pl[k] for k in ("Title", "InheritPermission", "Permissions") if k in pl})
    sid = ((e.get("sites") or {}).get(site) or {}).get("id") if site else None
    if sid:
        d["SiteId"] = sid
    return logical(d, e)


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
    return payload_model(pl, e, site), str(src.relative_to(r) if src.is_absolute() and r in src.parents else src)


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


# Release states in plan.json after `apply` started writing. Only "planned" may be applied; these need a read-back
# (`pls mark-applied` records what the sites really hold) or, for "rolled-back", a new release plan.
OPEN_STATES = ("applying", "applied-unverified", "uncertain", "recovery-required")


def plan_steps_problem(plan: dict) -> str | None:
    """`apply` writes plan["steps"] and plan["rollback"]; the environment check reads plan["per_site"]. Both must
    name the same sites, ids and files, each site once, in the planned order, so no edited step writes elsewhere."""
    sites, per = plan.get("sites") or [], plan.get("per_site") or {}
    for part, file_key, order in (("steps", "payload_file", sites), ("rollback", "rollback_file", sites[::-1])):
        steps = plan.get(part)
        if not isinstance(steps, list) or [s.get("site") if isinstance(s, dict) else None for s in steps] != order:
            return f"plan.json {part} do not list exactly the sites {order}"
        for s in steps:
            ps = per.get(s["site"]) or {}
            if s.get("op") != "updatesite" or s.get("site_id") != ps.get("site_id") or \
                    (ps.get(file_key) and s.get("payload_file") != ps[file_key]):
                return f"plan.json {part} entry for {s['site']} does not match per_site (site id, file or op)"
    return None


def readback_state(rel: Path, plan: dict, step: dict, export: Any, e: dict) -> tuple[str, list[dict]]:
    """Classify one site of a multi-site release from its export: "applied" (live == payload), "not applied"
    (live == rollback file, or the site was not written since the plan) or "differs" (written, equals neither)."""
    site = step["site"]
    want = payload_model(rj(rel / step["payload_file"]), e, site)
    diffs = flat_diff(same_meta(logical(export, e), want), want)
    if not diffs:
        return "applied", []
    back_file = next((s["payload_file"] for s in plan["rollback"] if s["site"] == site), None)
    if back_file is None:
        raise Fail(f"plan.json has no rollback step for {site}")
    back = payload_model(rj(rel / back_file), e, site)
    if not flat_diff(same_meta(logical(export, e), back), back):
        return "not applied", diffs
    updated = site_data(export).get("UpdatedTime")
    if updated is not None and updated == step.get("expect_updated_time"):
        return "not applied", diffs
    return "differs", diffs


def restore_readback(client, plan: dict, files: dict, e: dict, touched: list[str]) -> list[str]:
    """After a rollback: export every touched site and compare it with its rollback file. Returns problems."""
    rel_plan = {s["site"]: s for s in plan["rollback"]}
    bad = []
    for site in touched:
        step = rel_plan[site]
        try:
            live = client.export_site(step["site_id"])
        except H.TransportError as ex:
            bad.append(f"read-back {site}: {ex}")
            continue
        back = payload_model(files[step["payload_file"]], e, site)
        diffs = flat_diff(same_meta(logical(live, e), back), back)
        if diffs:
            bad.append(f"read-back {site}: {len(diffs)} difference(s) from {step['payload_file']} after the restore")
    return bad


def apply_outcome_message(release: str, plan: dict, res: dict) -> str:
    """What happened and what the person does next, for every apply result except success."""
    st, site = res["status"], res.get("failed_site")
    exports = " ".join(f"--export {s}=<file>" for s in plan["sites"])
    if st == "refused":
        return f"{release}: refused — nothing was written"
    if st == "rolled-back":
        return (f"{release}: ROLLED BACK after {site} failed — every touched site was restored and read back equal to "
                f"its rollback file. Fix the cause, then make a new release plan (pls release-plan with a new id).")
    if st == "uncertain":
        return (f"{release}: OUTCOME UNKNOWN — {site} got no answer and may or may not have been written; nothing was "
                f"restored. Do not re-run apply. Export every site of the release (pls export), then "
                f"pls mark-applied {release} {exports} records what each site holds.")
    return (f"{release}: RECOVERY REQUIRED — {site} failed and the restore did not complete "
            f"({', '.join(res.get('failed_restores') or []) or 'see read-back lines above'}). Restore those sites from "
            f"releases/{release}/rollback-<site>.json, then export every site and run pls mark-applied {release} {exports} "
            f"to record the state.")


def same_meta(live: dict, base: dict) -> dict:
    """Release payloads carry only ReferenceType/Body; compare meta on the keys the baseline has."""
    out = dict(live, meta={k: v for k, v in live["meta"].items() if k in base["meta"]})
    if base.get("permissions") is None:
        out.pop("permissions", None)   # permissions not managed in git for this site (opt-in)
    if base.get("title") is None:
        out.pop("title", None)         # git holds no title; a release payload does (environments.json)
    return out


def drift_report(r: Path, e: dict, env: str, site: str, export: Any, explicit: str | None) -> tuple[list[dict], str]:
    base, label = baseline(r, e, env, site, explicit)
    live = same_meta(logical(export, e), base)
    diffs = flat_diff(live, base)
    text = md_diff(diffs, labels(base) | labels(live), f"{env}/{site}: live vs baseline ({label})", "Baseline (last release)",
                   {"removed": f"only on {env} (live)", "added": "only in the baseline", "changed": "changed on live"})
    if diffs:
        rev = classify(diffs)
        text += (f"\n**Reverting this drift would be: {rev['classification']}.**"
                 + ("".join(f"\n- {x}" for x in rev["data_impacting"] + rev["permission_impacting"]))
                 + "\nResolve by accepting (fold into git + requirement) or reverting (via a release with its own gate); see D11.\n"
                 + ("A title lives in environments.json (envs.<env>.sites.<site>.title), not in config/: accept a title "
                    "change there.\n" if any(d["path"] == "title" for d in diffs) else ""))
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
    need_onboarding(r, "release-plan")
    e = env_conf(r, env)
    if (r / "releases" / release / "plan.json").exists():
        raise Fail(f"releases/{release}/plan.json exists — a release id is used once; choose the next id (S3)")
    if accept_drift and not Path(accept_drift).is_file():
        raise Fail(f"--accept-drift must name the drift decision record (file not found: {accept_drift})")
    if accept_unverified and not Path(accept_unverified).is_file():
        raise Fail(f"--accept-unverified must name the decision record (file not found: {accept_unverified})")
    if e.get("role") == "prod":
        print("note: production plans are executed by the customer-side runner (ADR-0003)")
    gate_error = None                                  # reported together with every other refusal reason
    if e.get("role") != "dev":
        try:
            GT.require(r, "G3", release, f"a release plan for {env}")
        except GT.GateError as ex:
            gate_error = str(ex)
    results, failed = {}, False
    for site, path in sorted(exports.items()):
        if site not in e["sites"]:
            raise Fail(f"site '{site}' is not in environments.json for {env}")
        conf = e["sites"][site]
        if conf.get("shared_from") or (e.get("sandbox_of") and not conf.get("sandbox")):
            raise Fail(f"{env}/{site} points to the {conf.get('shared_from') or e.get('sandbox_of')} site (shared, read only) — "
                       "a sandbox deploys only its own copies (ADR-0011)")
        ok, msgs, res = plan_site(r, e, env, site, rj(Path(path)), accept_drift, accept_unverified)
        for m in msgs:
            print(m)
        failed |= not ok
        results[site] = res
    jobs_now: dict = {}
    try:                                               # scheduled scripts travel with every release of the env (ADR-0012)
        SE.declared_jobs(r)                            # layout checked for every env, sandboxes included
        if not e.get("sandbox_of"):
            jobs_now = rendered_jobs(r, e)
    except (ValueError, Fail) as ex:
        print(f"JOBS {SE.JOBS_DIR.as_posix()}: {ex} (ADR-0012)")
        failed = True
    if gate_error:
        print(f"GATE {gate_error}")
    if failed or gate_error:
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
        "release": release, "env": env, "env_role": e.get("role"), "status": "planned", "sites": order,
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
    if e.get("sandbox_of"):                            # the tenant is the base env's: a sandbox never deploys jobs (ADR-0011)
        jobs_changed: list[str] = []
        plan["jobs"] = {"fingerprints": None, "changed": [], "deploy": None, "manual_step": None,
                        "note": f"sandbox: scheduled scripts are tenant-wide; they are deployed through {e['sandbox_of']} releases only"}
    else:
        fps = SE.fingerprints(jobs_now)
        jobs_changed = SE.changed_jobs(last_applied_jobs(r, env), fps)
        plan["jobs"] = {"fingerprints": fps, "changed": jobs_changed, "deploy": "manual" if jobs_changed else None,
                        "manual_step": SE.manual_job_step(env, jobs_changed, release)}
        if jobs_changed:                               # what the operator copies into the tenant, resolved for this env
            jd = rel / "scheduled-scripts"
            jd.mkdir(parents=True, exist_ok=True)
            for n, j in jobs_now.items():
                if j["body"] is not None:
                    (jd / f"{n}.js").write_bytes(j["body"].encode("utf-8"))
            wj(jd / SE.JOBS_INDEX, [j["entry"] for j in jobs_now.values() if j["entry"] is not None])
    for x in plan["version_check"]["differences"]:
        print(f"VERSION {x}")
    wj(rel / "plan.json", plan)
    for x in jobs_changed:
        print(f"JOB {x}")
    if plan["jobs"]["manual_step"]:
        print(plan["jobs"]["manual_step"])
    if e.get("role") != "prod":
        eff = env_effects(r, e)
        if any(per_site[s]["side_effects"] for s in order) and eff["mail"] == "unknown":
            print(f"note: envs.{env}.side_effects.mail is 'unknown' — `pls apply` will refuse this release until a person records it (ADR-0010)")
        if jobs_changed and eff["jobs"] == "unknown":
            print(f"note: envs.{env}.side_effects.jobs is 'unknown' — `pls apply` will refuse this release until a person records it (ADR-0010)")
    LG.record_metric(sites=len(order), changes=sum(p["changes"] for p in per_site.values()), classification=worst)
    (rel / "diff-report.operator.md").write_text(
        RP.operator_report(plan, {n: c.get("title") or n for n, c in e["sites"].items()}), encoding="utf-8")
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


def adopt_package(r: Path, a) -> int:
    """Adopt every site of a UI site package in one run (read only: one getsite per site). Names come from the
    project (same title on another environment) or from the person's --names file; nothing is adopted while a site
    has no name. Referenced sites first; a site that fails (e.g. a secret) does not stop the others; configs created
    in this run are re-mapped at the end, so references between them resolve."""
    import contextlib
    import io
    import pls_http as H
    try:
        pkg = json.loads(Path(a.package).read_text(encoding="utf-8-sig"))
        names = json.loads(Path(a.names).read_text(encoding="utf-8-sig")) if a.names else {}
    except (OSError, ValueError) as ex:
        raise Fail(f"cannot read the package or the names file: {ex}")
    ev = rj(r / "environments.json")
    known: dict[str, set[str]] = {}
    for ec in ev["envs"].values():
        for n, c in (ec.get("sites") or {}).items():
            if c.get("title"):
                known.setdefault(c["title"], set()).add(n)
    plan = AD.package_plan(pkg, known, names)
    for sid, title in plan["missing"]:
        print(f"NAME NEEDED  {sid}  {title}")
    if plan["missing"]:
        print(f"{len(plan['missing'])} site(s) without a logical name — nothing adopted. A person names them in a JSON "
              'file {"<site id or title>": "<name>" | null} (null skips the site) and passes it with --names')
        LG.record_metric(missing_names=len(plan["missing"]))
        return 1
    env_conf(r, a.env)
    _, _, c = _client(r, a.env)
    registered = {n: conf.get("id") for n, conf in (ev["envs"][a.env].get("sites") or {}).items()}
    today, created, done, failed = datetime.now().astimezone().date().isoformat(), [], [], []
    for sid, name, title in plan["order"]:
        if registered.get(name) == sid:
            print(f"already   {sid:>7}  {name:24} {title}")
            continue
        try:
            adopt_check_name(name)
            exp = c.export_site(sid)                                  # the only call to Pleasanter: getsite (read)
            stamp = _stamp()
            out = r / ".pls" / "exports" / f"{a.env}-{name}-adopt-{stamp}.json"
            wj(out, exp)
            new = not (r / "config" / name / "site.json").exists()
            with contextlib.redirect_stdout(io.StringIO()):
                adopt(r, a.env, name, exp, today, stamp)
            if new:
                created.append((name, out))
            done.append(name)
            print(f"adopted   {sid:>7}  {name:24} {title}{'' if new else '  (id registered; config exists)'}")
        except Exception as ex:                                       # noqa: BLE001 — one site never stops the others
            failed.append(name)
            print(f"FAILED    {sid:>7}  {name:24} {title}: {(str(ex) or type(ex).__name__).splitlines()[0][:160]}")
    for sid, title in plan["skipped"]:
        print(f"skipped   {sid:>7}  {'(null in --names)':24} {title}")
    for name, out in created:                                         # every id is known now: map references again
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                ok = main(["unpack", str(out), "--env", a.env, "--site", name]) == 0 and main(["canon", "--site", name]) == 0
        except Exception:                                             # noqa: BLE001
            ok = False
        if not ok:                                                    # a rerun prints "already": say how to finish
            failed.append(name)
            print(f"REMAP FAILED  {name}: run `pls unpack {out.relative_to(r).as_posix()} --env {a.env} --site {name}` "
                  f"then `pls canon --site {name}`")
    LG.record_metric(adopted=len(done), failed=len(failed), skipped=len(plan["skipped"]), remapped=len(created))
    print(f"{len(done)} adopted, {len(failed)} failed, {len(plan['skipped'])} skipped — reports in ops/adopt/; "
          f"read only, nothing written to Pleasanter")
    return 1 if failed else 0


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
    decided = AR.ladder_decided(r)                              # L-LAD-01: a reviewed as-is counts only via its record
    undecided = [it.get("Name") or f"(no name, Id {it.get('Id')})" for it in ss.get("ServerScripts") or []
                 if not it.get("Shared") and not decided(it.get("Name"))]
    counts = {"slots used": len(entries) - nf, "slots only in filters": nf}
    counts |= {k: len(ss.get(k) or []) for k in ("Columns", "Processes", "Views", "Notifications", "Reminders", "Summaries",
                                                  "Links", "ServerScripts", "Scripts", "Styles", "Htmls", "DashboardParts")}
    extra = {
        "Literal mail addresses (L-MAIL-01)": [f"{p}: {a}" for p, a in SE.literal_addresses(ss)],
        "Processes with no View object (L-PRC-01, D21: API and record screen fail)": unconditioned_processes(ss, True),
        "Processes whose View has no filter (they work; the button shows in every record of their CurrentStatus — review)":
            [x for x in unconditioned_processes(ss) if x not in unconditioned_processes(ss, True)],
        "Numbers equal to a site id inside script bodies (written as a site id → ${site:x}; POSSIBLE lines stay as written)": AD.script_id_uses(raw_scripts, ids_all),
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
    n_sus = sum(1 for x in extra["Numbers equal to a site id inside script bodies (written as a site id → ${site:x}; POSSIBLE lines stay as written)"] if x.startswith("POSSIBLE"))
    print(f"adopted site {sid} as '{name}' ({d.get('ReferenceType')}) from {env} — read only; nothing written to Pleasanter")
    if second_env:
        print(f"  second environment: id registered, config/{name} unchanged; "
              f"{len(extra[f'Differences from config/{name} (this environment vs git)'])} difference line(s) in the report")
    else:
        print(f"  config/{name}/, slot ledger: {len(entries) - nf} slot(s) defined or placed + {nf} only in the filter list "
              f"(zone customer)")
    print(f"  record releases/{rel}/ (drift baseline, not a release)")
    print(f"  findings: {len(SC.unverified(ss))} unverified component(s), {len(principals)} unmapped principal(s), "
          f"{len(undecided)} server script(s) without a decision, {n_sus} possible site id(s) in scripts kept as written (pls refs)")
    print(f"  report: {out.relative_to(r)}")
    return 0


def load_source(r: Path, env: str, path: str, site: str) -> tuple[dict, dict]:
    """(logical model, info) of one comparison source: `git` (config/<site>), a getsite export or a site package."""
    if path == "git":
        model = read_tree(r / "config" / site)
        model["settings"] = canonicalize(model["settings"])       # same form as the exports below (D8)
        return model, {"missing": [], "label": "git"}
    e = env_conf(r, env)
    info = {"missing": [], "label": f"{env}:{Path(path).name}"}
    try:
        doc = rj(Path(path))
        if CMP.is_package(doc):
            doc, pinfo = CMP.from_package(doc, (e["sites"].get(site) or {}).get("id"))
            info |= pinfo
        model = logical(doc, e)
    except (OSError, ValueError, TypeError, KeyError) as ex:
        raise Fail(f"--source {env}={path}: {ex}")
    model["settings"] = canonicalize(model["settings"])
    return model, info


def env_compare(r: Path, site: str, sources: list[str], today: str) -> int:
    """Compare every source with the first one after mapping ids to logical names (read-only, local files)."""
    if len(sources) < 2:
        raise Fail("give at least two --source ENV=FILE (or --source git)")
    loaded = []
    for s_ in sources:
        env, _, path = s_.partition("=") if s_ != "git" else ("", "", "git")
        if s_ != "git" and (not path or path == "git"):
            raise Fail(f"--source {s_!r}: use ENV=FILE, or git on its own")
        loaded.append(load_source(r, env, path, site))
    (m0, i0), rows, notes = loaded[0], [], []
    values = {str(v) for _, ec in envs(r)["envs"].items() for v in (ec.get("values") or {}).values()}
    for m, info in loaded:
        if info.get("site"):
            notes.append(f"{info['label']}: package site {info['site']}")
        if info.get("app"):
            notes.append(f"{info['label']}: site package of Pleasanter {info['app']} ({info.get('package_time')})")
        if info.get("missing"):
            notes.append(f"{info['label']}: package exported without {', '.join(info['missing'])}")
    for m, info in loaded[1:]:
        missing = i0.get("missing", []) + info.get("missing", [])
        perms = m0.get("permissions") is not None and m.get("permissions") is not None and "permissions" not in missing
        if not perms:
            notes.append(f"{i0['label']} → {info['label']}: permissions not compared (one side has none)")
        for d_ in flat_diff(CMP.comparable(m0, perms), CMP.comparable(m, perms)):
            rows.append(d_ | {"pair": f"{i0['label']} → {info['label']}", "class": CMP.classify(d_, missing, values)})
    out = r / "ops" / "env-compare" / f"{today}-{datetime.now():%H%M%S}-{site}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(CMP.report(site, rows, [i["label"] for _, i in loaded], notes, today, short), encoding="utf-8")
    by = {c: sum(1 for x in rows if x["class"] == c) for c in ("content", "id-like", "not-in-package")}
    print(f"{site}: {len(rows)} difference(s) after mapping ids — content {by['content']}, id-like {by['id-like']}, "
          f"not in package {by['not-in-package']}; report {out.relative_to(r)}")
    for n in notes:
        print(f"  {n}")
    return 1 if by["content"] or by["id-like"] else 0


def refs_cmd(r: Path, a) -> int:
    """List site ids inside the scripts of a site, or keep one as a literal number (a person's decision, BR7)."""
    e = env_conf(r, a.env)
    resolve = {k: str(v["id"]) for k, v in e["sites"].items() if v.get("id")}
    d = r / "config" / a.site
    model = read_tree(d)
    if a.ref:
        return _record_reference(r, a, d, resolve)
    if not a.keep:
        uses = SX.site_refs(model["scripts"], resolve)
        for u in uses:
            print(f"{u['kind']}/{u['script']} line {u['line']}: ${{site:{u['site']}}} = {u['number']} … `{u['context']}`")
        possible, groups = 0, Counter()
        for kind, items in model["scripts"].items():
            for it in items or []:
                body = it.get("Body") or ""
                for name, num in resolve.items():
                    for pos in SX.possible_ids(body, num):
                        possible += 1
                        ls, le = body.rfind("\n", 0, pos) + 1, body.find("\n", pos)
                        group = SX.possible_group(body[ls:(le if le != -1 else len(body))])
                        groups[group] += 1
                        if a.summary and group != "other":
                            continue                    # summary: only the lines a person has to read
                        ctx = body[max(ls, pos - 30):(le if le != -1 else len(body))][:70].replace("\r", "")
                        print(f"POSSIBLE [{group}] {kind}/{it.get('Name') or it.get('Title')} line "
                              f"{body.count(chr(10), 0, pos) + 1}: {num} (= {name}?) … `{ctx}`")
        LG.record_metric(references=len(uses), possible=possible, possible_groups=dict(groups))
        if a.summary:
            print("POSSIBLE by group: " + ", ".join(f"{g} {n}" for g, n in groups.most_common()))
        print(f"{a.site}: {len(uses)} site reference(s) in scripts; {possible} number(s) equal to a site id kept as "
              "written — mark a real one with --ref \"<context>\" --reason … --by <name> --quote \"<their words>\"")
        return 0
    if not (a.reason and a.by and (a.quote or "").strip()):
        raise Fail("--keep needs --reason, --by (the person who decided) and --quote (their own words)")
    found = [(name, num) for name, num in resolve.items() if re.search(SX.id_pattern(num), a.keep)]
    if len(found) != 1:
        raise Fail(f"the context must contain exactly one site id of {a.env} (found {[n for _, n in found] or 'none'})")
    name, num = found[0]
    why = SX.check_context(a.keep, num)
    if why:
        raise Fail(f"--keep {a.keep!r}: {why}")
    targets = []
    for kind, (folder, _ext) in SCRIPT_KINDS.items():
        idx = d / folder / "_index.json"
        for entry in rj(idx) if idx.exists() else []:
            path = d / folder / entry["File"]
            with open(path, encoding="utf-8", newline="") as fh:     # keep CRLF as stored (S7)
                body = fh.read()
            new, n = SX.keep_literal(body, name, num, a.keep, resolve)
            if n:
                targets.append((path, new, n))
    changed = sum(n for _, _, n in targets)
    if not changed:
        raise Fail(f"context {a.keep!r} not found around a ${{site:{name}}} in config/{a.site} scripts (copy it from `pls refs`)")
    f = r / "design" / "refs-literal.json"                  # the decision first: a later unpack applies it anyway
    doc = rj(f) if f.exists() else {"literal": []}
    doc["literal"].append({"site": a.site, "number": num, "context": a.keep, "reason": a.reason, "by": a.by,
                           "quote": a.quote.strip(),
                           "date": datetime.now().astimezone().date().isoformat()})
    wj(f, doc)
    SX.load_literal(r)
    for path, new, _n in targets:
        path.write_text(new, encoding="utf-8", newline="")
    print(f"kept {changed} occurrence(s) of {num} as a literal number in config/{a.site}; decision recorded in design/refs-literal.json")
    return 0


def _record_reference(r: Path, a, d: Path, resolve: dict) -> int:
    """A person says: this number, in this context, is a site id. Recorded first, then the git scripts change."""
    if not (a.reason and a.by and (a.quote or "").strip()):
        raise Fail("--ref needs --reason, --by (the person who decided) and --quote (their own words)")
    found = [(name, num) for name, num in resolve.items() if re.search(SX.id_pattern(num), a.ref)]
    if len(found) != 1:
        raise Fail(f"the context must contain exactly one site id of {a.env} (found {[n for _, n in found] or 'none'})")
    name, num = found[0]
    why = SX.check_context(a.ref, num)
    if why:
        raise Fail(f"--ref {a.ref!r}: {why}")
    targets = []
    for kind, (folder, _ext) in SCRIPT_KINDS.items():
        idx = d / folder / "_index.json"
        for entry in rj(idx) if idx.exists() else []:
            path = d / folder / entry["File"]
            with open(path, encoding="utf-8", newline="") as fh:     # keep CRLF as stored (S7)
                body = fh.read()
            new = SX.replace_ids(body, {num: name}, None, {num: [a.ref]})
            if new != body:
                targets.append((path, new))
    if not targets:
        raise Fail(f"context {a.ref!r} not found as written in config/{a.site} scripts (copy it from `pls refs`)")
    f = r / "design" / "refs-literal.json"
    doc = rj(f) if f.exists() else {"literal": []}
    doc.setdefault("reference", []).append({"site": a.site, "target": name, "number": num, "context": a.ref, "reason": a.reason,
                                            "by": a.by, "quote": a.quote.strip(), "date": datetime.now().astimezone().date().isoformat()})
    wj(f, doc)
    SX.load_literal(r)                                       # the decision holds for the rest of this run too
    for path, new in targets:
        path.write_text(new, encoding="utf-8", newline="")
    print(f"{num} in {a.ref!r} is now ${{site:{name}}} in config/{a.site} ({len(targets)} file(s)); decision recorded")
    return 0


# ---------------------------------------------------------------- sandboxes, harvest, merge (ADR-0011)

def _git(r: Path, *args: str) -> str:
    import subprocess
    try:
        res = subprocess.run(["git", *args], cwd=r, capture_output=True, text=True, encoding="utf-8")
    except OSError as ex:
        raise Fail(f"git not available: {ex}")
    if res.returncode != 0:
        raise Fail(f"git {' '.join(args)}: {res.stderr.strip()[:200]}")
    return res.stdout


def _writes_to(model: dict, dep: str) -> list[str]:
    """Places where a site's configuration may WRITE to site `dep` when records are saved: summaries aggregate into
    the parent, scripts may call items.Update/Create on it (a reference in a script counts, read or write)."""
    ref = "${site:%s}" % dep
    out = [f"Summaries[{x.get('Id')}]" for x in model["settings"].get("Summaries") or [] if str(x.get("SiteId")) == ref]
    out += [f"{k}/{it.get('Name') or it.get('Title') or it.get('Id')}" for k in ("ServerScripts",)
            for it in model["scripts"].get(k) or [] if ref in (it.get("Body") or "")]
    return out


def sandbox_create(r: Path, name: str, sites: list[str], parent: int, base: str = "dev", allow_shared_writes: bool = False) -> int:
    """Register env dev-<name> with copies of `sites` (to be created by the normal bootstrap) and plan their
    bootstrap. Sites they reference but that are not copied point to the base environment's sites (read only).
    Nothing is written to Pleasanter here."""
    if not AD.SAFE_NAME.fullmatch(name):
        raise Fail(f"--name {name!r}: lower-case letters, digits, - and _")
    ev = rj(r / "environments.json")
    env = f"dev-{name}"
    if env in ev["envs"]:
        raise Fail(f"environment {env} exists — use pls sandbox refresh, or drop it first")
    b = ev["envs"].get(base)
    if not b or b.get("role") != "dev":
        raise Fail(f"base environment {base!r} must exist with role dev")
    managed = ev.get("managed_sites") or []
    unknown = [s for s in sites if s not in managed or not (r / "config" / s / "site.json").exists()]
    if unknown:
        raise Fail(f"not managed sites with config: {unknown}")
    e = {"role": "dev", "connection": base, "sandbox_of": base, "parent_id": parent,
         "principals": dict(b.get("principals") or {}), "values": dict(b.get("values") or {}),
         "side_effects": dict(b.get("side_effects") or {}), "sites": {}}
    if b.get("pleasanter"):                                # same server as the base: same version (ADR-0009)
        e["pleasanter"] = dict(b["pleasanter"])
    for s in sites:
        e["sites"][s] = {"title": f"{name}_{(b['sites'].get(s) or {}).get('title') or s}", "sandbox": True}
    for s in sites:                                        # references to sites that are not copied
        model = read_tree(r / "config" / s)
        for dep in sorted(site_deps(model, s, set(managed))):
            if dep not in e["sites"]:
                writes = _writes_to(model, dep)
                if writes and not allow_shared_writes:
                    raise Fail(f"{s} may write to {dep} ({', '.join(writes)}); in a sandbox that would change {base} data. "
                               f"Copy {dep} too (--sites {s},{dep}), or pass --allow-shared-writes after checking")
                bid = (b["sites"].get(dep) or {}).get("id")
                if not bid:
                    raise Fail(f"{s} references {dep}, which has no id in {base}: add it to --sites")
                e["sites"][dep] = {"id": bid, "title": b["sites"][dep].get("title"), "shared_from": base}
    ev["envs"][env] = e
    wj(r / "environments.json", ev)
    release = f"B-{_stamp()}-{env}"
    bootstrap_plan(r, env, release)
    shared = [k for k, v in e["sites"].items() if v.get("shared_from")]
    print(f"sandbox {env}: copies of {', '.join(sites)} under folder {parent}"
          + (f"; references to {', '.join(shared)} point to {base} (read only)" if shared else ""))
    print(f"next: pls bootstrap {release}   (creates the sites; asks for confirmation)\n"
          f"      pls sandbox refresh --name {name}   (deploys the git configuration to them)")
    return 0


def sandbox_sites(e: dict) -> dict:
    return {k: v for k, v in e["sites"].items() if v.get("sandbox")}


def sandbox_refresh(r: Path, name: str) -> int:
    """Plan a release of the current git configuration to the sandbox sites (exports read, nothing written)."""
    import pls_http as H
    env = f"dev-{name}"
    e = env_conf(r, env)
    if not e.get("sandbox_of"):
        raise Fail(f"{env} is not a sandbox")
    own = sandbox_sites(e)
    missing = [s for s, v in own.items() if not v.get("id")]
    if missing:
        raise Fail(f"{env}: {missing} not created yet — run the bootstrap first")
    _, _, c = _client(r, env)
    exports = {}
    for s, v in own.items():
        out = r / ".pls" / "exports" / f"{env}-{s}-{_stamp()}.json"
        wj(out, c.export_site(v["id"]))
        exports[s] = str(out)
    release = f"R-{_stamp()}-{env}"
    code = release_plan(r, env, release, exports, None)
    if code == 0:
        print(f"next: pls apply {release}   (asks for confirmation)")
    else:
        print(f"{env}: if the sandbox drifted, harvest it first: pls harvest --env {env} --site <site>")
    return code


def sandbox_drop(r: Path, name: str) -> int:
    """Forget a sandbox environment. Its sites stay in Pleasanter: a person deletes them (agents never delete)."""
    env = f"dev-{name}"
    ev = rj(r / "environments.json")
    e = ev["envs"].get(env)
    if not e or not e.get("sandbox_of"):
        raise Fail(f"{env} is not a sandbox")
    own = {s: v.get("id") for s, v in sandbox_sites(e).items()}
    del ev["envs"][env]
    wj(r / "environments.json", ev)
    print(f"{env} removed from environments.json. Delete its sites in Pleasanter by hand: "
          + ", ".join(f"{s} ({i})" for s, i in own.items() if i))
    return 0


def harvest(r: Path, env: str, site: str) -> int:
    """Bring the configuration of a site as it is on `env` into config/<site> (read only towards Pleasanter).
    Refuses when config/<site> has uncommitted changes, so a harvest never mixes with unsaved work."""
    e = env_conf(r, env)
    if e.get("role") == "prod":
        raise Fail("harvest reads development environments (dev, sandboxes, stg); prod changes come through drift (P6)")
    if not (e["sites"].get(site) or {}).get("id"):
        raise Fail(f"{site} has no id in {env}")
    if _git(r, "status", "--porcelain", "--", f"config/{site}").strip():
        raise Fail(f"config/{site} has uncommitted changes — commit or stash them before harvesting")
    _, _, c = _client(r, env)
    exp = c.export_site(e["sites"][site]["id"])
    out = r / ".pls" / "exports" / f"{env}-{site}-harvest-{_stamp()}.json"
    wj(out, exp)
    model = logical(exp, e)
    model["settings"] = canonicalize(model["settings"])
    pf = r / "config" / site / "permissions.json"
    perms_before = pf.read_bytes() if pf.exists() else None
    model["permissions"] = None             # permissions are designed (P2) and opt-in (ADR-0006): never harvested
    write_tree(model, r / "config" / site)
    if perms_before is not None:
        pf.write_bytes(perms_before)
    stat = _git(r, "status", "--porcelain", "--", f"config/{site}").strip()
    print(f"harvested {site} from {env} (read only) → config/{site}")
    print(stat and f"changes:\n{stat}\nreview with `git diff config/{site}`, commit on the ticket branch" or "no changes")
    return 0


def merge_site_files(base: str, ours: str, theirs: str) -> int:
    """git merge driver: merged result written to `ours` (%A); exit 1 with the conflicts listed when any."""
    conflicts: list[str] = []
    merged = MG.merge(rj(Path(base)) if Path(base).stat().st_size else {}, rj(Path(ours)), rj(Path(theirs)),
                      conflicts=conflicts)
    if conflicts:                   # visible in the file: lint and pack refuse it until a person resolves them
        merged["_pls_conflicts"] = conflicts
    wj(Path(ours), merged)
    for c in conflicts:
        print(f"pls merge-site: CONFLICT {c}", file=sys.stderr)
    return 1 if conflicts else 0


def merge_install(r: Path) -> int:
    """Register the semantic merge for config/*/site.json in this repository (local git config + .gitattributes)."""
    if not (r / "pls.py").exists():
        raise Fail("merge-install runs in a project repository (pls.py launcher at its root)")
    ga = r / ".gitattributes"
    line = "config/*/site.json merge=pls-site"
    text = ga.read_text(encoding="utf-8") if ga.exists() else ""
    if line not in text:
        ga.write_text(text + ("" if text.endswith("\n") or not text else "\n") + line + "\n", encoding="utf-8")
    _git(r, "config", "merge.pls-site.name", "pls semantic merge of site.json (ADR-0011)")
    _git(r, "config", "merge.pls-site.driver", f'"{Path(sys.executable).as_posix()}" "{(r / "pls.py").as_posix()}" merge-site %O %A %B')
    print("merge driver installed: .gitattributes (commit it) + .git/config (every clone runs pls merge-install once)")
    return 0


# ---------------------------------------------------------------- new sites (ADR-0007)

def bootstrap_plan(r: Path, env: str, release: str) -> int:
    """Phase 1 of a first release: empty skeleton sites for every managed site that has no id in `env` yet.
    Phase 2 is the normal release-plan (updatesite with the complete payload) once the ids are bound, so every
    ${site:x} reference — also between new sites and inside scripts (D3) — resolves before anything is configured."""
    need_onboarding(r, "bootstrap-plan")
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
        if e.get("sandbox_of") and not conf.get("sandbox"):
            continue                                       # a sandbox holds copies of the chosen sites only (ADR-0011)
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
    plan = {"release": release, "env": env, "env_role": e.get("role"), "status": "planned", "parent_id": parent, "steps": steps,
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


def init_project(target: Path, stage: str, release_target: str, approver: str | None, fw: Path = FRAMEWORK,
                 origin: str = "new") -> None:
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
    text = re.sub(r"\| Origin \|.*\|", f"| Origin | `{origin}` |", text, count=1)
    text = re.sub(r"\| Stage \|.*\|", f"| Stage | `{stage}` |", text, count=1)
    text = re.sub(r"\| Release target \|.*\|", f"| Release target | `{release_target}` |", text, count=1)
    if approver:
        text = re.sub(r"\| Approvers \|.*\|", f"| Approvers | {approver} (all gates) |", text, count=1)
        text = re.sub(r"\| Operators \|.*\|", f"| Operators | dev: {approver}; stg: {approver}; prod: <customer operator> |", text, count=1)
    text = re.sub(r"\| Role tests \|.*\|", "| Role tests | `deferred` |" if stage == "demo" else "| Role tests | `per-role keys` |", text, count=1)
    cm.write_text(text, encoding="utf-8")
    if approver:          # the person running init states these values: recorded so a later hand edit is visible (L-PRF-01)
        said = f"pls init {target.name} --approver {approver} --origin {origin}"
        for field in ("Approvers", "Operators", "Origin"):
            m = re.search(rf"^\|\s*{field}\s*\|(.*)\|\s*$", text, re.M)
            PR.set_field(target, field, m.group(1).strip(), approver, said, recorded_by="pls init")
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
    return H, conn, H.Client(conn["url"], H.resolve_key(conn, key), timeout=H.conn_timeout(conn))


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
                    c = H.Client(conn["url"], H.resolve_key(conn, k), timeout=H.conn_timeout(conn))
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
                print(SE.describe(a.env, env_effects(r, e)))
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
            if e.get("role") != "dev":
                try:
                    GT.require(r, "G4", a.release, f"applying to {plan['env']}")
                except GT.GateError as ex:
                    raise H.TransportError(str(ex))
            if plan.get("status") != "planned":
                raise H.TransportError(f"{a.release} has status {plan.get('status')!r}, not 'planned'")
            for s_ in plan["sites"]:                         # the plan's ids must be this env's own sites (ADR-0011)
                conf = e["sites"].get(s_) or {}
                if conf.get("id") != plan["per_site"][s_].get("site_id") or conf.get("shared_from") or \
                        (e.get("sandbox_of") and not conf.get("sandbox")):
                    raise H.TransportError(f"{a.release}: {s_} → site {plan['per_site'][s_].get('site_id')} is not a site this "
                                           f"release may write in {plan['env']} (stale plan, or a shared site)")
            bad_step = plan_steps_problem(plan)          # the writes use steps/rollback, not per_site
            if bad_step:
                raise H.TransportError(f"{a.release}: {bad_step} — make a new release plan")
            files = {f.name: rj(f) for f in rel.glob("*.json") if f.name.startswith(("payload-", "rollback-"))}
            try:
                eff = env_effects(r, e)
            except ValueError as ex:
                raise H.TransportError(f"envs.{plan['env']}.{ex}")
            refusal, warning = SE.apply_refusal(plan["env"], eff, {s: plan["per_site"][s].get("side_effects") for s in plan["sites"]})
            pj = plan.get("jobs")                            # None: planned before the jobs check
            if pj is not None and SE.bad_plan_jobs(pj):
                raise H.TransportError(f"{a.release}: {SE.bad_plan_jobs(pj)} — make a new release plan (ADR-0012)")
            try:
                declared = bool(SE.declared_jobs(r))
                if pj is not None and pj.get("fingerprints") is not None and \
                        SE.fingerprints(rendered_jobs(r, e)) != pj["fingerprints"]:
                    raise H.TransportError(f"{a.release}: the scheduled scripts in git (or the environment values they use) "
                                           "changed since the plan — make a new release plan (ADR-0012)")
            except (ValueError, Fail) as ex:
                raise H.TransportError(f"{SE.JOBS_DIR.as_posix()}: {ex} (ADR-0012)")
            jrefusal, jwarning = SE.jobs_apply_refusal(plan["env"], eff, pj["changed"] if pj is not None else None, declared)
            refusal = "\n".join(x for x in (refusal, jrefusal) if x)
            manual = (pj or {}).get("manual_step")
            # the manual step comes after the sites are applied: if the apply is rolled back, nothing is copied
            warning = "\n".join(x for x in (warning, jwarning, manual and "after the sites are applied, this release has a "
                                             "manual step for scheduled scripts (ADR-0012); pls prints it then") if x)
            if refusal:
                raise H.TransportError(refusal)
            if warning:
                print(warning)
            if not _confirm(a.release, a.yes, f"apply {a.release} to {plan['env']} ({conn['url']}): {' → '.join(plan['sites'])}, "
                                             f"{plan.get('classification')}" + (f"\n{warning}" if warning else "")):
                return 1
            # Recorded before the first write: if the process dies mid-way, the release is not "planned" any more,
            # so it cannot be applied again blindly; `pls mark-applied` reads the sites back and records the state.
            plan.update(status="applying", apply_started_at=_now())
            wj(rel / "plan.json", plan)
            try:
                res = H.apply_release(c, plan, files)
            except H.TransportError as ex:           # only the preflight reads raise: nothing was written
                res = {"status": "refused", "log": [f"preflight: {ex}"]}
            except Exception as ex:                  # unknown point of failure: keep "applying" and leave evidence
                wj(rel / "apply-log.json", {"transport": "http", "at": _now(), "status": "applying",
                                            "error": f"{type(ex).__name__}: {ex}"})
                raise
            if res["status"] in ("rolled-back", "recovery-required"):
                # The read-back decides: "rolled-back" only when every touched site equals its rollback file
                # (a failing site may have refused its restore too, yet never changed).
                bad = restore_readback(c, plan, files, e, res["touched"])
                res = dict(res, status="recovery-required" if bad else "rolled-back",
                           log=res["log"] + (bad or ["read-back: every touched site equals its rollback file"]))
            for line in res["log"]:
                print(line)
            wj(rel / "apply-log.json", {"transport": "http", "at": _now(), **res})
            plan.update(status="planned" if res["status"] == "refused" else res["status"], apply_finished_at=_now())
            wj(rel / "plan.json", plan)
            LG.record_metric(sites=len(plan["sites"]), apply_status=res["status"])
            if res["status"] != "applied-unverified":
                print(apply_outcome_message(a.release, plan, res))
                return 1
            exports = []
            for site in plan["sites"]:
                out = r / ".pls" / "exports" / f"{plan['env']}-{site}-after-{a.release}.json"
                wj(out, c.export_site(plan["per_site"][site]["site_id"]))
                exports += ["--export", f"{site}={out}"]
            rc = main(["mark-applied", a.release, *exports])
            if manual:
                print(manual)
            return rc

        if a.cmd == "bootstrap":
            bp = r / "releases" / a.release / "bootstrap.json"
            plan = rj(bp)
            e = env_conf(r, plan["env"])
            if plan.get("status") == "created":
                raise H.TransportError(f"{a.release} was already created ({plan.get('created')}) — never create twice (S1)")
            done = set(plan.get("created") or {}) | {s for s, v in e["sites"].items() if v.get("id")}
            unsure = plan.get("uncertain")
            if unsure and unsure not in done and unsure not in (a.absent or []):
                raise H.TransportError(
                    f"{a.release}: the last run got no answer while creating '{unsure}' — it may exist now. A person checks "
                    f"the folder {plan['parent_id']} in Pleasanter: if it exists, pls bind --env {plan['env']} "
                    f"--release {a.release} --created {unsure}=<id>; if it does not, pls bootstrap {a.release} --absent {unsure}")
            plan = dict(plan, steps=[s for s in plan["steps"] if s["site"] not in done])
            if not plan["steps"]:
                print(f"{a.release}: every site already has an id — nothing to create")
                return 0
            _, conn, c = _client(r, plan["env"])
            H.assert_writable(e, conn, plan["env"])
            if e.get("role") != "dev":
                try:
                    GT.require(r, "G4", a.release, f"creating sites in {plan['env']}")
                except GT.GateError as ex:
                    raise H.TransportError(str(ex))
            if not _confirm(a.release, a.yes, f"create {[s['site'] for s in plan['steps']]} under {plan['parent_id']} in "
                                             f"{plan['env']} ({conn['url']}) — undo is manual (ADR-0007)"):
                return 1
            res = H.bootstrap(c, plan)
            for line in res["log"]:
                print(line)
            if res["created"]:
                bind(r, plan["env"], a.release, res["created"])
            if res["status"] == "uncertain" or unsure:   # record the unknown site, or clear the one a person checked
                rec = rj(bp)
                if res["status"] == "uncertain":
                    rec["uncertain"] = res["uncertain"]
                else:
                    rec.pop("uncertain", None)
                wj(bp, rec)
            if res["status"] == "uncertain":
                print(f"{a.release}: OUTCOME UNKNOWN for '{res['uncertain']}' — it may have been created. Check the folder "
                      f"before any re-run; pls bootstrap refuses until it is bound or confirmed absent.")
            return 0 if res["status"] == "created" else 1

        if a.cmd == "test":
            e = env_conf(r, a.env)
            conn = H.load_connection(r, a.env)
            cache: dict = {}

            def clients(role):
                k = role or conn.get("default_key") or "admin"
                if k not in cache:
                    cache[k] = H.Client(conn["url"], H.resolve_key(conn, k), timeout=H.conn_timeout(conn))
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
            if e.get("sandbox_of"):
                shared = {str(v["id"]) for v in e["sites"].values() if v.get("shared_from") and v.get("id")}
                all_ids = {v["id"] for v in e["sites"].values() if v.get("id")}
                hit = sorted({x for sp_ in specs if SE.test_writes(sp_) for x in SE.test_sites(sp_, sid, all_ids)} & shared)
                if hit:
                    raise H.TransportError(f"{a.env}: these tests may write to shared {e['sandbox_of']} sites {hit} "
                                           "(a --var record counts for every site) — refused (ADR-0011)")
            try:
                eff = env_effects(r, e)
            except ValueError as ex:
                raise H.TransportError(f"envs.{a.env}.{ex}")
            if any(SE.test_writes(sp_) for sp_ in specs):    # jobs first: local files only, no server call (ADR-0012)
                try:
                    jobs = SE.declared_jobs(r)
                except ValueError as ex:
                    raise H.TransportError(f"{SE.JOBS_DIR.as_posix()}: {ex} (ADR-0012)")
                refusal, warning = SE.jobs_test_refusal(a.env, eff, jobs)
                if refusal:
                    raise H.TransportError(refusal)
                if warning:
                    print(warning)
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
            LG.record_metric(tests=len(res["tests"]), passed=sum(t["status"] in ("pass", "pass-api-only") for t in res["tests"]))
            print(f"results: {out}")
            return 0 if all(t["status"] in ("pass", "pass-api-only") for t in res["tests"]) else 1

        if a.cmd == "kb-verify":
            e = env_conf(r, a.env)
            if e.get("role") != "dev" or e.get("sandbox_of"):
                raise H.TransportError("kb-verify creates probe sites: only on a dev environment (not a sandbox)")
            parent = str((e.get("values") or {}).get("kb_probe_parent") or "")
            app_ids = {int(v["id"]) for v in e["sites"].values() if v.get("id")} | {int(e.get("parent_id") or 0)}
            if not parent.isdigit() or int(parent) == 0 or int(parent) in app_ids:
                raise H.TransportError(f"envs.{a.env}.values.kb_probe_parent: the id of a folder for probe sites only, created and "
                                       "recorded by a person — not 0, not the app's folder or one of its sites (ADR-0009)")
            parent_i = int(parent)
            try:
                uid = KV.admin_uid(e.get("principals"))
            except ValueError as ex:
                raise H.TransportError(str(ex))
            _, conn, c = _client(r, a.env)
            H.assert_writable(e, conn, a.env)
            st_, js, _ = c.call(f"/api/items/{parent_i}/getsite")
            if st_ != 200 or ((js or {}).get("Response") or {}).get("Data", {}).get("ReferenceType") != "Sites":
                raise H.TransportError(f"kb_probe_parent {parent_i} is not a folder this key can read (HTTP {st_})")
            kb = FRAMEWORK / "skills" / "pls-kb-pleasanter"
            try:
                probes = KV.load_probes(kb)
            except (OSError, ValueError, KeyError) as ex:
                raise H.TransportError(f"probes: {ex}")
            if not _confirm("kb-verify", a.yes, f"kb-verify writes {len(probes)} probe site(s) and test records under folder "
                                                f"{parent_i} in {a.env} ({conn['url']})"):
                return 1
            state_f = r / ".pls" / f"kb-probes-{a.env}.json"
            state = rj(state_f) if state_f.exists() else {}
            if state.get("url") != conn["url"] or state.get("parent") != parent_i:
                state = {"url": conn["url"], "parent": parent_i, "sites": {}}     # another server or folder: never reuse
            schema = (e.get("pleasanter") or {}).get("schema") or 1.017
            rows, results = [], {}
            for p in probes:
                name, rt, log, status = p["_name"], p["site"]["ReferenceType"], [], "pass"
                row = {"entry": p["entry"], "probe": name, "status": "pass", "log": log}
                try:
                    sid = state["sites"].get(name)
                    if sid:
                        code, sjs, _ = c.call(f"/api/items/{sid}/getsite")
                        if code == 404:
                            sid = None
                        elif code != 200:
                            raise H.TransportError(f"getsite {sid} → HTTP {code}")
                        elif not KV.is_own_probe_site(sjs["Response"]["Data"], name, rt, parent_i, app_ids):
                            raise H.TransportError(f"site {sid} in the state file is not this probe's site (folder, title or type "
                                                   f"differ) — nothing written; check .pls/kb-probes-{a.env}.json")
                    if not sid:
                        code, cjs, text = c.call(f"/api/items/{parent_i}/createsite",
                                                 {"Title": KV.TITLE.format(name), "ReferenceType": rt, "Body": "", "SiteSettings": {}})
                        if code != 200 or not (cjs or {}).get("Id"):
                            raise H.TransportError(f"createsite → HTTP {code}")
                        sid = int(cjs["Id"])
                        state["sites"][name] = sid
                        wj(state_f, state)
                    row["site_id"] = sid
                    settings = {"Version": schema, "ReferenceType": rt, **(p["site"].get("SiteSettings") or {})}
                    code, _, _ = c.call(f"/api/items/{sid}/updatesite", {"Title": KV.TITLE.format(name), "ReferenceType": rt,
                                                                       "Body": "", "SiteSettings": settings})
                    want = p.get("expect_save", 200)
                    ok = code == want
                    log.append(f"{'ok' if ok else 'NG'} save → HTTP {code} (expected {want})")
                    status = status if ok else "fail"
                    if ok and code == 200:
                        data = c.export_site(sid)["Response"]["Data"]
                        for path, exp in (p.get("expect_stored") or {}).items():
                            act = KV.get_path(data["SiteSettings"], path)
                            good = H._check(act, exp)
                            log.append(f"{'ok' if good else 'NG'} stored {path} = {json.dumps(act, ensure_ascii=False)}")
                            status = status if good else "fail"
                        server_day = None
                        if p.get("server_dates"):
                            server_day = datetime.fromisoformat(str(data["UpdatedTime"])[:19]).date()
                            log.append(f"server date {server_day}")
                        vars_ = KV.date_vars(server_day) | {"admin_uid": uid}
                        specs = [dict(t, vars=dict(vars_)) for t in p.get("tests") or []]
                        if specs:
                            res = H.run_tests(lambda role: c, sid, specs, a.env)
                            for t in res["tests"]:
                                log += [x.strip() for x in t["log"] if x.strip().startswith(("NG", "exec", "expected"))]
                                if t["status"] not in ("pass", "pass-api-only"):
                                    status = "fail"
                    if p.get("teardown"):                      # leave the probe site usable in the UI (D21)
                        td = {"Version": schema, "ReferenceType": rt, **(p["teardown"].get("SiteSettings") or {})}
                        code, _, _ = c.call(f"/api/items/{sid}/updatesite", {"Title": KV.TITLE.format(name), "ReferenceType": rt,
                                                                           "Body": "", "SiteSettings": td})
                        log.append(f"teardown → HTTP {code}")
                        if code != 200:
                            raise H.TransportError(f"teardown failed (HTTP {code}): the probe site may stay broken in the UI")
                except (H.TransportError, KeyError, TypeError, ValueError) as ex:
                    status = "error"
                    log.append(str(ex))
                if p.get("observe") and status == "pass":
                    status = "observed"
                row["status"] = status
                results[name] = status
                rows.append(row)
            for row in rows:                                         # a probe whose control failed proves nothing
                ctl = next((p.get("control") for p in probes if p["_name"] == row["probe"]), None)
                if ctl and results.get(ctl) != "pass" and row["status"] == "pass":
                    row["status"] = "inconclusive"
                    row["log"].append(f"control {ctl} did not pass")
            entries = set(re.findall(r"^\| (D\d+) \|", (kb / "references" / "behaviours.md").read_text(encoding="utf-8"), re.M))
            no_probe = sorted(entries - {x["entry"] for x in rows}, key=lambda d: int(d[1:]))
            today = datetime.now().astimezone().date().isoformat()
            out = r / "ops" / "kb-verify" / f"{today}-{a.env}.md"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(KV.report(a.env, e.get("pleasanter"), rows, no_probe, today), encoding="utf-8")
            wj(out.with_suffix(".json"), {"env": a.env, "pleasanter": e.get("pleasanter"), "date": today, "probes": rows,
                                          "entries": KV.entry_results(rows), "without_probe": no_probe})
            for x in rows:
                print(f"{x['status']:12} {x['entry']:4} {x['probe']}")
            ent = KV.entry_results(rows)
            print(f"{sum(v == 'pass' for v in ent.values())}/{len(ent)} entries verified on {a.env} "
                  f"(Pleasanter {(e.get('pleasanter') or {}).get('app', 'unknown')}) → {out.relative_to(r)}")
            if any(x["status"] == "error" for x in rows):
                return 2
            return 0 if all(v == "pass" for v in ent.values()) else 1

        if a.cmd == "adopt-package":
            return adopt_package(r, a)

        if a.cmd == "adopt":
            adopt_check_name(a.name)
            env_conf(r, a.env)
            _, _, c = _client(r, a.env)
            exp = c.export_site(a.site)                      # the only call to Pleasanter: getsite (read)
            stamp = _stamp()
            out = r / ".pls" / "exports" / f"{a.env}-{a.name}-adopt-{stamp}.json"
            wj(out, exp)
            return adopt(r, a.env, a.name, exp, datetime.now().astimezone().date().isoformat(), stamp)

        if a.cmd == "version" and a.from_package:
            env_conf(r, a.env)
            ev = rj(r / "environments.json")
            e = ev["envs"][a.env]
            if a.app:
                raise Fail("--app and --from-package exclude each other: the package states its own version")
            try:
                pkg = rj(Path(a.from_package))
                if not CMP.is_package(pkg):
                    raise ValueError("not a site package (no HeaderInfo/Sites)")
                ids = {int(x["SiteId"]) for x in pkg["Sites"] if x.get("SiteId") is not None}
                sid = next((v["id"] for v in e["sites"].values() if v.get("id") in ids), None)
                doc, info = CMP.from_package(pkg, sid or next(iter(sorted(ids)), None))
            except (OSError, ValueError, TypeError, KeyError) as ex:
                raise Fail(f"--from-package {a.from_package}: {ex}")
            old = e.get("pleasanter") or {}
            if old.get("package_time") and info.get("package_time") and info["package_time"] < old["package_time"]:
                raise Fail(f"the package ({info['package_time']}) is older than the recorded one ({old['package_time']})")
            new, msgs = PV.record_from_package(old, info.get("app"), PV.schema_version(doc["Response"]["Data"]),
                                               info.get("package_time"), datetime.now().astimezone().date().isoformat())
            e["pleasanter"] = new
            wj(r / "environments.json", ev)
            print(f"{a.env}: app {new['app']}, schema {new['schema']}, build {new['build']} (from {new['source']})")
            for m_ in msgs:
                print(f"  {m_}")
            return 0 if new["app"] != PV.UNKNOWN else 1

        if a.cmd == "version":
            env_conf(r, a.env)                               # unknown env → clear error, not a traceback
            ev = rj(r / "environments.json")
            e = ev["envs"][a.env]
            conn = H.load_connection(r, a.env)
            try:
                build = PV.build_token(PV.fetch_login_page(conn["url"]))
            except PV.PageError as ex:
                raise H.TransportError(f"{a.env}: login page not readable ({ex})")
            client = H.Client(conn["url"], H.resolve_key(conn, None), timeout=H.conn_timeout(conn))
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
    """Every command is logged (ops/log/, ADR-0013); the work is done by _main."""
    args = list(sys.argv[1:] if argv is None else argv)
    return LG.run(root, args, lambda: _main(args))


def _main(argv=None) -> int:
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
    s.add_argument("--absent", action="append", metavar="SITE",
                   help="a person checked that SITE (no answer in the last run) was not created; create it again")
    s = sp.add_parser("test", help="run test specs over HTTP; each spec's as_key picks the role's key")
    s.add_argument("specs", nargs="+")
    s.add_argument("--env", required=True)
    s.add_argument("--site", required=True, help="default site of the specs (processes are read from it)")
    s.add_argument("--out", help="result file (default tests/results/<env>-<date>-<name>.json)")
    s.add_argument("--var", action="append", default=[], metavar="NAME=VALUE", help="fixture for spec vars (e.g. e=44656)")
    s = sp.add_parser("kb-verify", help="run the KB probes on a dev environment (creates probe sites in values.kb_probe_parent)")
    s.add_argument("--env", required=True)
    s.add_argument("--yes", action="store_true", help="skip the typed confirmation (only when the person allowed it)")
    s = sp.add_parser("adopt-package", help="read-only: adopt every site of a UI site package (names from the project or --names)")
    s.add_argument("--env", required=True)
    s.add_argument("--package", required=True, help="site package JSON exported from the UI (keep it in .pls/packages/)")
    s.add_argument("--names", help='JSON {"<site id or title>": "<name>" | null} decided by a person; null skips a site')
    s = sp.add_parser("adopt", help="read-only: bring an existing site into this project (config, ledger, drift baseline, report)")
    s.add_argument("--env", required=True)
    s.add_argument("--site", required=True, type=int, help="id of the existing site")
    s.add_argument("--name", required=True, help="stable logical name, e.g. anken")
    s = sp.add_parser("version", help="record the Pleasanter version of an environment (build and schema detected; app label from /versions)")
    s.add_argument("--env", required=True)
    s.add_argument("--app", help="application version read on <url>/versions by a logged-in person, e.g. 1.5.2.0")
    s.add_argument("--from-package", help="site package JSON exported from that environment: its AssemblyVersion is recorded (no HTTP)")
    s = sp.add_parser("refs", help="site ids inside the scripts of a site: list them, keep one as a literal number, or mark a POSSIBLE one as a reference")
    s.add_argument("--site", required=True)
    s.add_argument("--env", default="dev", help="environment whose ids are shown (default dev)")
    s.add_argument("--keep", metavar="CONTEXT", help="text around the number, as printed by `pls refs` (number included)")
    s.add_argument("--ref", metavar="CONTEXT", help="a POSSIBLE number that is a real site id: text around it, as printed")
    s.add_argument("--summary", action="store_true", help="group POSSIBLE numbers; print only the group 'other' line by line")
    s.add_argument("--reason")
    s.add_argument("--by", help="the person who decided")
    s.add_argument("--quote", help="the person's own words for --keep / --ref (never a relayed or paraphrased approval)")
    s = sp.add_parser("sandbox", help="per-developer copies of sites on dev (ADR-0011): create | refresh | drop")
    s.add_argument("action", choices=["create", "refresh", "drop"])
    s.add_argument("--name", required=True, help="developer name; the environment is dev-<name>")
    s.add_argument("--sites", help="create: logical sites to copy, comma separated")
    s.add_argument("--parent", type=int, help="create: id of the developer's folder")
    s.add_argument("--allow-shared-writes", action="store_true",
                   help="create: a copied site may write to a shared dev site (summary, script) — checked by a person")
    s = sp.add_parser("harvest", help="read only: bring a site's configuration from an environment into config/ (ADR-0011)")
    s.add_argument("--env", required=True)
    s.add_argument("--site", required=True)
    s = sp.add_parser("merge-site", help="git merge driver for config/*/site.json (%%O %%A %%B)")
    s.add_argument("base")
    s.add_argument("ours")
    s.add_argument("theirs")
    sp.add_parser("merge-install", help="register the semantic merge driver in this repository")
    s = sp.add_parser("spec-skeleton", help="as-is 画面設計書 tables from the configuration; AI writes only the marked places")
    s.add_argument("--site", required=True)
    s.add_argument("--out", help="default design/as-is/<site>.md")
    s.add_argument("--force", action="store_true", help="overwrite an existing document (its written text is lost)")
    s = sp.add_parser("usage", help="LLM token usage per step from Claude Code transcripts (numbers only)")
    s.add_argument("action", choices=["collect", "report"])
    s.add_argument("--transcripts", help="collect: transcript folder (default: Claude Code's folder for this project)")
    s.add_argument("--since", help="collect: only requests on or after this ISO date")
    s.add_argument("--by", choices=["phase", "step", "agent", "model"], default="phase", help="report: grouping")
    s.add_argument("--json", action="store_true", help="report: machine-readable output (for a UI)")
    s = sp.add_parser("step", help="mark the start of a step (phase + title) in the run log; LLM tokens are attributed to it")
    s.add_argument("phase", choices=LG.PHASES)
    s.add_argument("title")
    s = sp.add_parser("gate", help="record a gate decision the person stated (I4); never approve yourself")
    s.add_argument("gate", choices=GT.GATES)
    s.add_argument("--decision", choices=GT.DECISIONS, default="approved")
    s.add_argument("--approver", required=True, help="name as listed in the profile row Approvers")
    s.add_argument("--quote", required=True, help="the person's own words for this decision")
    s.add_argument("--item", action="append", default=[], help="G1: REQ id, G2: DES id (repeat)")
    s.add_argument("--release", action="append", default=[], help="G3/G4: release id; G4 also a bootstrap id (repeat)")
    s = sp.add_parser("profile", help="set a guarded profile value as the person stated it (I4); never decide it yourself")
    s.add_argument("action", choices=["set"])
    s.add_argument("field", choices=PR.FIELDS + (PR.ROLE,))
    s.add_argument("value")
    s.add_argument("--env", help="role: the environment in environments.json")
    s.add_argument("--approver", required=True, help="an approver of the profile (the first Approvers value: a person it names)")
    s.add_argument("--quote", required=True, help="the person's own words for this decision")
    s = sp.add_parser("review", help="record that the person reviewed an as-is document (I4); never record it yourself")
    s.add_argument("kind", choices=["as-is"])
    s.add_argument("site")
    s.add_argument("--approver", required=True, help="a G2 approver of the profile")
    s.add_argument("--quote", required=True, help="the person's own words for this review")
    s = sp.add_parser("jobs-verified", help="record that a person deployed and checked the scheduled scripts of an applied "
                                            "release (ADR-0012); never record it yourself")
    s.add_argument("release")
    s.add_argument("--by", required=True, help="the person who copied and checked: an operator of the release's env "
                                                "(profile row Operators) or a G4 approver")
    s.add_argument("--quote", required=True, help="the person's own words")
    s.add_argument("--approved-by", help="optional: the G4 approver, when the operator is another person")
    s = sp.add_parser("xref", help="which script uses which column and site (ops/xref/<site>.json)")
    s.add_argument("--site", required=True)
    s = sp.add_parser("env-compare", help="compare one site across environments (exports, site packages or git), ids mapped; local files only")
    s.add_argument("--site", required=True, help="logical site name")
    s.add_argument("--source", action="append", required=True, metavar="ENV=FILE|git", help="first = reference; repeat")
    s = sp.add_parser("backup", help="every record of a site → migrations/<dir>/backup/ (ADR-0004)")
    s.add_argument("--env", required=True)
    s.add_argument("--site", required=True)
    s.add_argument("--out", required=True)
    s = sp.add_parser("mark-applied")
    s.add_argument("release")
    s.add_argument("export", nargs="?", help="export of the target site taken right after applying (single-site plan)")
    s.add_argument("--export", dest="exports", action="append", metavar="SITE=EXPORT", help="multi-site plan: one per site")
    s = sp.add_parser("lint")
    s.add_argument("--summary", action="store_true", help="counts per rule and site instead of every issue")
    sp.add_parser("coverage")
    s = sp.add_parser("init", help="create a new project repository (templates/project + skills + launcher)")
    s.add_argument("dir")
    s.add_argument("--origin", choices=["new", "existing"], default="new",
                   help="new: the app is built by this project; existing: take over an app that already runs (onboarding first)")
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
        if a.origin == "existing" and a.stage == "demo":
            print("note: an existing app in 運用保守 is usually --stage project (customer approves G1/G4) with --target stg or prod")
        init_project(target, a.stage, a.target, a.approver, origin=a.origin)
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
    try:
        SX.load_literal(r)
    except ValueError as ex:
        raise Fail(str(ex))
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

    if a.cmd in ("http-check", "export", "apply", "bootstrap", "test", "backup", "version", "adopt", "adopt-package", "kb-verify"):
        return http_cmd(r, a)

    if a.cmd == "refs":
        return refs_cmd(r, a)

    if a.cmd == "profile":
        try:
            out = PR.set_field(r, a.field, a.value, a.approver, a.quote, a.env)
        except GT.GateError as ex:
            raise Fail(str(ex))
        rec = rj(out)
        print(f"{a.field}{' of ' + a.env if a.env else ''} = {rec['value']!r}, stated by {rec['approver']}: "
              f"{out.relative_to(r).as_posix()}")
        return 0

    if a.cmd == "review":
        try:
            out = AR.record_review(r, a.site, a.approver, a.quote)
        except GT.GateError as ex:
            raise Fail(str(ex))
        print(f"as-is review of {a.site} by {rj(out)['approver']}: {out.relative_to(r).as_posix()} — DES-000-as-is-{a.site}.md "
              f"now clears L-LAD-01 for scripts named in design/as-is/{a.site}.md while that document is unchanged")
        return 0

    if a.cmd == "sandbox":
        if a.action == "create":
            if not (a.sites and a.parent):
                raise Fail("sandbox create needs --sites and --parent (the developer's folder id)")
            return sandbox_create(r, a.name, [x.strip() for x in a.sites.split(",") if x.strip()], a.parent,
                                  allow_shared_writes=a.allow_shared_writes)
        return sandbox_refresh(r, a.name) if a.action == "refresh" else sandbox_drop(r, a.name)

    if a.cmd == "harvest":
        return harvest(r, a.env, a.site)

    if a.cmd == "merge-site":
        return merge_site_files(a.base, a.ours, a.theirs)

    if a.cmd == "merge-install":
        return merge_install(r)

    if a.cmd == "xref":
        model = read_tree(r / "config" / a.site)
        data = SX.xref(model["settings"], model["scripts"])
        out = r / "ops" / "xref" / f"{a.site}.json"
        wj(out, data)
        top = sorted(data["columns"].items(), key=lambda x: -len(x[1]["scripts"]))[:10]
        print(f"{a.site}: {len(data['scripts'])} script(s), {len(data['columns'])} column(s) referenced by scripts → {out.relative_to(r)}")
        for col, v in top:
            print(f"  {col:16} {v['label'][:20]:20} used by {len(v['scripts'])} script(s)")
        return 0

    if a.cmd == "env-compare":
        return env_compare(r, a.site, a.source, datetime.now().astimezone().date().isoformat())

    if a.cmd == "spec-skeleton":
        d = r / "config" / a.site
        if not (d / "site.json").exists():
            raise Fail(f"config/{a.site} not found (adopt the site first)")
        out = Path(a.out) if a.out else r / "design" / "as-is" / f"{a.site}.md"
        if out.exists() and not a.force:
            raise Fail(f"{out} exists — it may hold reviewed text; use --out for a new file or --force to replace it")
        titles = {}
        for ec in envs(r)["envs"].values():
            for n, c in (ec.get("sites") or {}).items():
                titles.setdefault(n, c.get("title") or n)
        text = SP.skeleton(a.site, read_tree(d), titles)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        LG.record_metric(ai_markers=SP.ai_markers(text), lines=text.count(chr(10)) + 1)
        print(f"{out.relative_to(r).as_posix() if out.is_relative_to(r) else out}: {text.count(chr(10)) + 1} lines, "
              f"{SP.ai_markers(text)} place(s) for the AI to write")
        return 0

    if a.cmd == "usage":
        if a.action == "collect":
            tdir = Path(a.transcripts) if a.transcripts else US.transcripts_dir(r)
            if not tdir.exists():
                raise Fail(f"no transcripts at {tdir} (pass --transcripts)")
            me = LG.actor(r)                         # my transcripts, my steps: never a teammate's after a pull
            steps = [e for e in LG.read(r) if e.get("kind") == "step" and e.get("actor") == me]
            files = US.collect(r, steps, tdir, a.since)
            LG.record_metric(sessions=len(files))
            print(f"{len(files)} session(s) → ops/usage/ ({len(steps)} step marker(s) in the run log)")
            return 0
        rows = US.report(US.load(r), a.by)
        if a.json:
            print(json.dumps(rows, ensure_ascii=False, indent=1))
            return 0
        print(f"{a.by:42} {'requests':>8} {'input':>10} {'cache write':>12} {'cache read':>12} {'output':>9} {'total':>12}")
        for x in rows:
            print(f"{str(x['key'])[:42]:42} {x['requests']:>8} {x['input']:>10,} {x['cache_creation']:>12,} "
                  f"{x['cache_read']:>12,} {x['output']:>9,} {x['total']:>12,}")
        return 0

    if a.cmd == "step":
        if a.phase in CHANGE_PHASES:
            need_onboarding(r, f"step {a.phase}")
        f = LG.step(r, a.phase, a.title)
        print(f"step {a.phase}: {a.title} → {f.relative_to(r).as_posix()}")
        return 0

    if a.cmd == "gate":
        need_onboarding(r, f"gate {a.gate}")
        try:
            out = GT.record(r, a.gate, a.decision, a.approver, a.quote, a.item, a.release,
                            datetime.now().astimezone().date().isoformat())
        except GT.GateError as ex:
            raise Fail(str(ex))
        LG.record_metric(gate=a.gate, decision=a.decision, approver=rj(out)["approver"])
        print(f"{a.gate} {a.decision} by {rj(out)['approver']}: {out.relative_to(r).as_posix()}")
        for rel_id, b in (rj(out).get("bound") or {}).items():
            print(f"  {rel_id}: " + (f"bound to its content for {b['env']} (sha256 {b['sha256'][:12]}…) — any later change "
                                     f"to the plan or its files needs a new G4" if b else
                                     "NOT PLANNED YET — apply/bootstrap will refuse; record G4 again after release-plan"))
        return 0

    if a.cmd == "jobs-verified":
        return jobs_verified(r, a.release, a.by, a.quote, a.approved_by)

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
        status = plan.get("status")
        if status in APPLIED:      # re-marking would re-stamp applied_at and could turn drift into the baseline
            print(f"NOT marked again: {a.release} is already recorded as {status} ({plan.get('applied_at')}). "
                  f"Compare live with it: pls drift <export> --env {plan['env']} --site <site>")
            return 1
        if status == "rolled-back":
            print(f"NOT marked: {a.release} was rolled back and read back — none of it is live. Make a new release plan.")
            return 1
        if status != "planned" and status not in OPEN_STATES:
            print(f"NOT marked: {a.release} has status {status!r}")
            return 1
        log_status = rj(rel / "apply-log.json").get("status") if (rel / "apply-log.json").exists() else None
        if status == "planned" and log_status not in (None, "refused", "applied-unverified"):
            print(f"NOT marked: apply-log.json says {log_status!r} but plan.json says planned — read the log and decide "
                  "with the person; a rolled-back or failed apply is never recorded as applied. If the release was "
                  "applied again later (browser runner), the person moves apply-log.json aside and runs mark-applied again")
            return 1
        started = plan.get("apply_started_at")
        if status in OPEN_STATES and started:
            t0 = datetime.fromisoformat(started).timestamp()
            stale = [s_ for s_, f in exports.items() if Path(f).stat().st_mtime < t0]
            if stale:
                print(f"NOT marked: the exports for {stale} are older than the apply ({started}) — export again (pls export)")
                return 1
        states, shown = {}, {}
        for step in plan["steps"]:
            site, sid = step["site"], plan["per_site"][step["site"]]["site_id"]
            exp = rj(Path(exports[site]))
            if site_data(exp).get("SiteId") != sid:
                print(f"NOT marked: the export for {site} is site {site_data(exp).get('SiteId')}, the release wrote site {sid}")
                return 1
            states[site], shown[site] = readback_state(rel, plan, step, exp, e)
        if set(states.values()) == {"not applied"}:
            print(f"NOT marked: no site holds the release payload ({', '.join(states)}).")
            if status == "planned":
                print(f"{a.release} is still planned — was it applied?")
                return 1
            plan.update(status="rolled-back", readback=states, checked_at=_now(),
                        post_apply_check="read back: every site holds its rollback state (pls mark-applied)")
            wj(rel / "plan.json", plan)
            print(f"{a.release}: recorded as rolled-back — make a new release plan")
            return 1
        # After a failed restore, "differs" cannot be told apart from a half-restored or hand-repaired site
        if "not applied" in states.values() or (status == "recovery-required" and "differs" in states.values()):
            # Partly applied: never a success state and never a baseline; a person restores or completes it.
            for site, st_ in states.items():
                print(f"  {site}: {st_}")
            plan.update(status="recovery-required", readback=states, checked_at=_now(),
                        post_apply_check="read back: the release is only partly live")
            wj(rel / "plan.json", plan)
            print(f"{a.release}: RECOVERY REQUIRED — only partly applied. Restore the applied sites from "
                  f"rollback-<site>.json (or complete the others), export every site and run mark-applied again.")
            return 1
        bad = "differs" in states.values()
        for site, st_ in states.items():
            if st_ == "differs":
                want = payload_model(rj(rel / plan["per_site"][site]["payload_file"]), e, site)
                print(md_diff(shown[site], labels(want), f"{plan['env']}/{site}: live after apply vs release payload"))
        if bad:
            # The release WAS applied; Pleasanter stored some values differently (D8). Record that state as the
            # baseline so the fold-back release (P3 step 6) is not refused as drift (S2).
            for site in plan["sites"]:
                d = site_data(rj(Path(exports[site])))
                pl = rj(rel / plan["per_site"][site]["payload_file"])
                perms = ("InheritPermission", "Permissions") if ("Permissions" in pl or "InheritPermission" in pl) else ()
                managed = ("Title", "Body", "ReferenceType", "SiteSettings") + perms     # what the release wrote
                wj(rel / f"live-{site}.json", {k: d[k] for k in managed if k in d})
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
        if plan.get("status") in APPLIED or plan.get("status") == "rolled-back":
            print(f"NOT marked again: {a.release} is already recorded as {plan.get('status')} ({plan.get('applied_at')})")
            return 1
        exp = rj(Path(a.export))
        sid = ((e.get("sites") or {}).get(plan.get("site")) or {}).get("id")
        if sid and site_data(exp).get("SiteId") not in (None, sid):
            print(f"NOT marked: the export is site {site_data(exp).get('SiteId')}, the release is for site {sid}")
            return 1
        pl = rj(rel / "payload.json")
        want = payload_model(pl, e, plan.get("site"))
        got = same_meta(logical(exp, e), want)
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
        by_rule = Counter(i["rule"] for i in issues)
        LG.record_metric(issues=len(issues), by_rule=dict(sorted(by_rule.items())))
        if a.summary:                                   # counts first; the full list stays one command away
            for rule, n in sorted(by_rule.items()):
                sites = Counter(i["site"] for i in issues if i["rule"] == rule)
                top = ", ".join(f"{s} {c}" for s, c in sites.most_common(5))
                print(f"{rule:10} {n:4}  {top}{' …' if len(sites) > 5 else ''}")
        else:
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
        LG.record_metric(differences=len(ddiffs))
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
