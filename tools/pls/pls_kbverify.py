"""Executable verification of the knowledge base (ADR-0009 part 2, plan BR8).

Each KB entry that skills rely on has probes in skills/pls-kb-pleasanter/references/probes/<name>.json:

    {"entry": "D10", "title": "…",
     "site": {"ReferenceType": "Issues", "SiteSettings": {…}},          # the probe site's configuration
     "expect_save": 200,                                                 # HTTP of updatesite (D30: 500)
     "expect_stored": {"Columns[ColumnName=Status].DefaultInput": null}, # stored settings (null = absent, D8)
     "control": "<other probe>",                                         # this result counts only if that one passes
     "observe": true,                                                    # records what happens (no expected outcome yet)
     "server_dates": true,                                               # $today/$yesterday… from the server's clock; $today+90, $today-1
     "tests": [ … specs in the `pls test` format, confined to the probe site … ],
     "teardown": {"SiteSettings": {…}}}                                 # saved after the run: leave the site harmless

A probe may own further probe sites (ADR-0026):

     "sites": {"<key>": {"ReferenceType": "Results", "SiteSettings": {…}, "teardown": {"SiteSettings": {…}}}},
     # in any probe site's settings "${probe_site:<key>}" / "${probe_site:main}" becomes that probe site's id
     # (an int when it is the whole value); a create or list step may say "site": "<key>" or "main"

Safety: a probe can only create records on its own sites and act on records it created (ops create/get/list/exec/
update; `get`, `exec`, `update` name a record a create of the same spec returned — checked in the file (a save
name is never a kb-verify variable, a create expected to be refused saves nothing) and again at run time; no
`delete`, `run_on`, `vars`, no `site` on a spec, and `site` on a step only names one of the probe's own sites; a
probe file name has no `__`). Probe sites have no notifications or reminders
at any depth. A server script at the top level of the main site's settings, `as_key` for a declared test-user role
and `$group_<role>` (that role's group id) are allowed only under the guards of pls_kbverify_guarded (ADR-0025,
ADR-0026). kb-verify reuses a probe site only when the site is provably its own (parent folder, title, type).
"""
from __future__ import annotations

import datetime as _dt
import json
import re
from pathlib import Path
from typing import Any

import pls_kbverify_guarded as KG

SELECTOR = re.compile(r"^(\w+)\[(\w+)=([^\]]*)\]$")
OPS = ("create", "get", "list", "exec", "update")
RECORD_OPS = ("get", "exec", "update")            # act on one record the probe created
SITE_OPS = ("create", "list")                     # may name one of the probe's own sites
FORBIDDEN_KEYS = ("site", "run_on", "vars")      # as_key: KG.check (declared roles only); a step's site: below
TITLE = "zz_kbprobe_{}"
SITE_KEY = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")      # no leading, trailing or double _
SITE_REF = re.compile(r"\$\{probe_site:([^}]*)\}")
GROUP_VAR = re.compile(r"^\$group_(\w+)$")
RESERVED_SAVES = ("today", "yesterday", "tomorrow", "lastweek", "admin_uid")   # and group_*: kb-verify's own variables


def _mail_parts(o: Any, path: str = "") -> list[str]:
    out = []
    if isinstance(o, dict):
        for k, v in o.items():
            p = f"{path}.{k}" if path else k
            if k in ("Notifications", "Reminders", "ServerScripts") and v:
                out.append(p)
            out += _mail_parts(v, p)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            out += _mail_parts(v, f"{path}[{i}]")
    return out


def extra_sites(p: dict) -> dict:
    """The probe's further sites {key: {ReferenceType, SiteSettings, teardown?}} (ADR-0026); {} when none."""
    sites = p.get("sites")
    if sites is None:
        return {}
    if not isinstance(sites, dict) or not sites:
        raise ValueError("sites must be an object {key: {ReferenceType, SiteSettings}}")
    for k, s in sites.items():
        if not SITE_KEY.match(str(k)) or k == "main":
            raise ValueError(f"sites.{k}: a key of a-z, 0-9 and single inner _ (not 'main')")
        if not isinstance(s, dict) or not s.get("ReferenceType") or not isinstance(s.get("SiteSettings") or {}, dict):
            raise ValueError(f"sites.{k}: an object with ReferenceType and SiteSettings")
    return sites


def probe_sites(p: dict) -> list[dict]:
    """Every site of a probe, main first: key, state name (also the title's suffix), type, settings, teardown."""
    out = [{"key": "main", "state": p["_name"], "rt": p["site"]["ReferenceType"],
            "settings": p["site"].get("SiteSettings") or {}, "teardown": p.get("teardown")}]
    for k, s in extra_sites(p).items():
        out.append({"key": k, "state": f"{p['_name']}__{k}", "rt": s["ReferenceType"],
                    "settings": s.get("SiteSettings") or {}, "teardown": s.get("teardown")})
    return out


def site_refs(o: Any) -> set:
    """Keys named by `${probe_site:<key>}` anywhere in o."""
    return {k for text in _strings(o) for k in SITE_REF.findall(text)}


def substitute_sites(o: Any, ids: dict) -> Any:
    """`${probe_site:<key>}` → that probe site's id: an int when it is the whole value, else text inside a string.
    KeyError when a key has no id (a site not created)."""
    if isinstance(o, str):
        m = SITE_REF.fullmatch(o)
        if m:
            return int(ids[m.group(1)])
        return SITE_REF.sub(lambda x: str(int(ids[x.group(1)])), o)
    if isinstance(o, list):
        return [substitute_sites(x, ids) for x in o]
    if isinstance(o, dict):
        return {k: substitute_sites(v, ids) for k, v in o.items()}
    return o


def _strings(o: Any) -> list:
    if isinstance(o, str):
        return [o]
    if isinstance(o, list):
        return [s for x in o for s in _strings(x)]
    if isinstance(o, dict):
        return [s for x in o.values() for s in _strings(x)]
    return []


def check_probe(p: dict) -> None:
    """Raise ValueError when a probe could send mail or touch anything but its own sites and records."""
    sites = extra_sites(p)
    own = {k: v for k, v in (p["site"].get("SiteSettings") or {}).items() if k != "ServerScripts"}   # KG.check
    mail = _mail_parts(own) + _mail_parts((p.get("teardown") or {}).get("SiteSettings") or {})
    for k, s in sites.items():                       # a further site holds no script at all (ADR-0026)
        mail += [f"sites.{k}.{x}" for x in _mail_parts(s.get("SiteSettings") or {})
                 + _mail_parts((s.get("teardown") or {}).get("SiteSettings") or {})]
    if mail:
        raise ValueError(f"probe sites must not send mail, and server scripts are allowed only at the top level of "
                         f"the probe's main site settings (ADR-0025, ADR-0026): {mail}")
    keys = {"main", *sites}
    refs = set()
    for o in [p["site"], p.get("teardown"), p.get("expect_stored")] + list(sites.values()):
        for text in _strings(o):
            refs |= set(SITE_REF.findall(text))
    if refs - keys:
        raise ValueError(f"${{probe_site:...}} names {sorted(refs - keys)}: only main and the probe's sites "
                         f"({', '.join(sorted(keys))})")
    KG.check(p)
    roles = set(p.get("roles") or {})
    for spec in (p.get("tests") or []) + ([{"id": "cleanup", "steps": p["cleanup"]}] if p.get("cleanup") else []):
        bad = [k for k in FORBIDDEN_KEYS if k in spec]
        saved: set[str] = set()                    # run-time variables are per spec: so are the records it may name
        for st in spec.get("steps") or []:
            bad += [k for k in FORBIDDEN_KEYS if k in st and k != "site"]
            if st.get("op") not in OPS:
                raise ValueError(f"spec {spec.get('id')}: op {st.get('op')!r} not allowed (only {', '.join(OPS)})")
            if "site" in st and (not isinstance(st["site"], str) or st.get("op") not in SITE_OPS
                                 or st["site"] not in keys):
                raise ValueError(f"spec {spec.get('id')}: site {st['site']!r} on a {st.get('op')} step - only create "
                                 f"and list, and only the probe's own sites ({', '.join(sorted(keys))})")
            if st.get("op") in RECORD_OPS and "record" not in st:
                raise ValueError(f"spec {spec.get('id')}: {st['op']} needs a record created earlier by this probe")
            if st.get("op") == "exec" and any(t.startswith("$") for t in _strings(st.get("data") or {})):
                raise ValueError(f"spec {spec.get('id')}: exec data is sent as written — no $variables")
            groups = {m.group(1) for t in _strings(st.get("data") or {}) for m in [GROUP_VAR.match(t)] if m}
            if groups - roles:
                raise ValueError(f"spec {spec.get('id')}: $group_{sorted(groups - roles)[0]} - only the group of a "
                                 "role declared in roles (ADR-0026)")
            if "record" in st:
                name = str(st["record"])
                if not name.startswith("$") or name[1:] not in saved:
                    raise ValueError(f"spec {spec.get('id')}: record {name!r} must be a record created earlier by this probe")
            if st.get("op") == "create" and st.get("save"):
                name = str(st["save"])
                if name in RESERVED_SAVES or name.startswith("group_"):
                    raise ValueError(f"spec {spec.get('id')}: save {name!r} is the name of a kb-verify variable — a "
                                     "record name must not stand for an id the probe did not create")
                if not st.get("expectHttp"):          # a create expected to be refused saves no record
                    saved.add(name)
        if bad:
            raise ValueError(f"spec {spec.get('id')}: keys {sorted(set(bad))} not allowed in probes (confined to the probe site)")


def load_probes(kb_dir: Path) -> list[dict]:
    out = []
    for f in sorted((kb_dir / "references" / "probes").glob("*.json")):
        if f.name == "index.json":
            continue
        try:
            p = json.loads(f.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeDecodeError, ValueError) as ex:
            raise ValueError(f"probe {f.name}: not readable JSON ({ex})") from ex
        if not isinstance(p, dict):
            raise ValueError(f"probe {f.name}: must be a JSON object")
        p["_name"] = f.stem
        if "__" in f.stem or f.stem.startswith("_") or f.stem.endswith("_"):   # `<probe>__<key>`: a further site
            raise ValueError(f"probe {f.name}: a probe file name must not contain '__' nor start or end with '_' "
                             "(reserved for further sites)")
        try:
            check_probe(p)
        except ValueError as ex:
            raise ValueError(f"probe {f.name}: {ex}") from ex
        out.append(p)
    names = {p["_name"] for p in out}
    for p in out:
        if p.get("control") and p["control"] not in names:
            raise ValueError(f"probe {p['_name']}: control {p['control']!r} does not exist")
    return out


def get_path(o: Any, path: str) -> Any:
    """Dotted path with list selectors: `Columns[ColumnName=Status].DefaultInput`, `Views.0.Name`."""
    for part in path.split("."):
        if o is None:
            return None
        m = SELECTOR.match(part)
        if m:
            lst = o.get(m.group(1)) if isinstance(o, dict) else None
            o = next((x for x in lst or [] if isinstance(x, dict) and str(x.get(m.group(2))) == m.group(3)), None)
        elif isinstance(o, list):
            o = o[int(part)] if part.isdigit() and int(part) < len(o) else None
        else:
            o = o.get(part) if isinstance(o, dict) else None
    return o


def date_vars(today: _dt.date | None = None) -> dict[str, str]:
    t = today or _dt.date.today()
    return {"today": t.isoformat(), "yesterday": (t - _dt.timedelta(days=1)).isoformat(),
            "tomorrow": (t + _dt.timedelta(days=1)).isoformat(), "lastweek": (t - _dt.timedelta(days=7)).isoformat()}


def admin_uid(principals: dict) -> str:
    kind, _, uid = str((principals or {}).get("admin", "")).partition(",")
    if kind != "User" or not uid.isdigit():
        raise ValueError(f"principals.admin must be 'User,<id>' (got {(principals or {}).get('admin')!r})")
    return uid


def is_own_probe_site(site: dict, name: str, rt: str, parent: int, app_ids: set[int]) -> bool:
    return (int(site.get("SiteId") or 0) not in app_ids and int(site.get("ParentId") or -1) == parent
            and site.get("Title") == TITLE.format(name) and site.get("ReferenceType") == rt)


def entry_results(rows: list[dict]) -> dict[str, str]:
    """An entry passes only when all its probes pass; error wins over fail, fail over inconclusive."""
    out: dict[str, str] = {}
    rank = ["pass", "inconclusive", "fail", "error"]
    for r in rows:
        cur = out.get(r["entry"], "pass")
        st = "pass" if r["status"] == "observed" else r["status"]      # an observation does not decide the entry
        out[r["entry"]] = max(cur, st, key=rank.index)
    return out


def report(env: str, version: dict | None, rows: list[dict], no_probe: list[str], today: str) -> str:
    app = (version or {}).get("app", "unknown")
    entries = entry_results(rows)
    out = [f"# KB verification — {env} — {today}", "", f"- **Pleasanter:** {app} (build {(version or {}).get('build')}, "
           f"schema {(version or {}).get('schema')})",
           f"- **Result:** {sum(v == 'pass' for v in entries.values())}/{len(entries)} entries verified "
           f"({sum(r['status'] == 'pass' for r in rows)}/{len(rows)} probes pass)", "",
           "| Entry | Result |", "|---|---|"]
    out += [f"| {k} | {v} |" for k, v in sorted(entries.items(), key=lambda x: int(x[0][1:]))]
    out += ["", "| Entry | Probe | Status | Detail |", "|---|---|---|---|"]
    for r in rows:
        out.append(f"| {r['entry']} | {r['probe']} | {r['status']} | {'; '.join(r['log'])[:300].replace('|', '/')} |")
    out += ["", "## Entries without a probe", "", ", ".join(no_probe) or "none", "",
            "A failing entry does not hold on this version: correct or split it by version (I9). "
            "`error` = the probe could not run (infrastructure), not a verdict on the entry; `inconclusive` = its control failed; `observed` = recorded behaviour without an expected outcome (read the detail)."]
    return "\n".join(out) + "\n"
