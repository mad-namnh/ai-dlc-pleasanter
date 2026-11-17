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
probe file name has no `__`). Probe sites hold notifications or reminders only when every item is `Disabled`,
addresses only example.invalid and carries no credential field (ADR-0027); never in a teardown. A server script at
the top level of the main site's settings, `as_key` for a declared test-user role, `$group_<role>` (that role's group
id) and such disabled notifications are allowed only under the guards of pls_kbverify_guarded (ADR-0025, ADR-0026,
ADR-0027). A `settings` step (`{"op": "settings", "site": "<key>|main", "SiteSettings": {…}}`, updatesite) or
`settings_partial` step (`"body": {"Processes": […], "StatusControls": […]}`, updatesitesettings, upsert by Id) saves
one of the probe's own sites, never with a server script; a `siteConfig` step reads the main site back (list selectors
such as `Columns[ColumnName=NumA]`, `$admin_uid` / `$group_<role>` in expectations); `$admin_uid` and `$group_<role>` may be whole values in probe site settings and in those steps.
kb-verify reuses or writes a probe site only when the site is provably its own (parent folder, title, type).
"""
from __future__ import annotations

import datetime as _dt
import json
import re
from pathlib import Path
from typing import Any

import pls_kbverify_guarded as KG
import pls_secret_fields as SF
import pls_side_effects as SE

SELECTOR = re.compile(r"^(\w+)\[(\w+)=([^\]]*)\]$")
OPS = ("create", "get", "list", "exec", "update", "settings", "settings_partial", "siteConfig")   # siteConfig reads the main site
RECORD_OPS = ("get", "exec", "update")            # act on one record the probe created
SETTINGS_OPS = ("settings", "settings_partial")   # save settings on one of the probe's own sites (ADR-0027)
SITE_OPS = ("create", "list") + SETTINGS_OPS      # may name one of the probe's own sites
FORBIDDEN_KEYS = ("site", "run_on", "vars")      # as_key: KG.check (declared roles only); a step's site: below
TITLE = "zz_kbprobe_{}"
SITE_KEY = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")      # no leading, trailing or double _
SITE_REF = re.compile(r"\$\{probe_site:([^}]*)\}")
GROUP_VAR = re.compile(r"^\$group_(\w+)$")
SETTINGS_VAR = re.compile(r"^\$(admin_uid|group_\w+)$")    # whole values a probe site's settings may name (ADR-0027)
SAFE_DOMAIN = "@example.invalid"
RESERVED_SAVES = ("today", "yesterday", "tomorrow", "lastweek", "admin_uid")   # and group_*: kb-verify's own variables


PLACEHOLDERS = ("[owner]", "[manager]", "[creator]", "[updator]")   # record fields, never a principal id (ADR-0027 3/4)
ADDRESS_KEY = re.compile(r"(address|^to$|^cc$|^bcc$)", re.I)       # fields that name a recipient or a target
URL = re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://")


def _ci(d: dict, key: str) -> Any:
    """A key read as Pleasanter's JSON reader may read it (property names compared without case: assumed, not
    verified — duplicates under case folding are refused in _mail_parts)."""
    return next((v for k, v in d.items() if str(k).casefold() == key.casefold()), None)


def notice_problems(kind: str, items: Any) -> list[str]:
    """Why notifications or reminders could reach anyone (ADR-0027 item 4); [] when every item is `Disabled`, every
    recipient field holds only example.invalid addresses or the placeholders [Owner] / [Manager] / [Creator] /
    [Updator], no field holds a URL, and no credential field is filled (pls_secret_fields)."""
    if not isinstance(items, list) or not all(isinstance(x, dict) for x in items):
        return [f"{kind} must be a list of objects"]
    out = [f"{kind}[{i}] is not \"Disabled\": true" for i, x in enumerate(items) if _ci(x, "Disabled") is not True]
    canon = {k.casefold(): k for k in ("Token", "Headers", "Type", "ReminderType", "Address", "To", "Disabled")}
    spelled = [{canon.get(str(k).casefold(), k): v for k, v in x.items()} for x in items]   # as Pleasanter may read them
    for i, x in enumerate(items):
        folded = [str(k).casefold() for k in x]
        if len(set(folded)) != len(folded):
            out.append(f"{kind}[{i}]: two keys differ only in case")
        for k, v in x.items():
            texts = _strings(v) + ([str(v)] if isinstance(v, (int, float)) and not isinstance(v, bool) else [])
            if any(URL.search(t) for t in texts):
                out.append(f"{kind}[{i}].{k}: a URL (no target outside the probe, ADR-0027)")
            if ADDRESS_KEY.search(str(k)):
                for t in texts:
                    for tok in (y for y in re.split(r"[,;\s]+", t) if y):
                        if not (tok.lower().endswith(SAFE_DOMAIN) and SE.EMAIL_RE.fullmatch(tok)) \
                                and tok.lower() not in PLACEHOLDERS:
                            out.append(f"{kind}[{i}].{k}: recipient {tok!r} (only …{SAFE_DOMAIN} or "
                                       f"{', '.join(p.title() for p in PLACEHOLDERS)})")
    out += [f"{kind}: address {a} (only {SAFE_DOMAIN[1:]})" for a in sorted({m for t in _strings(items)
                                                                          for m in SE.EMAIL_RE.findall(t)})
            if not a.lower().endswith(SAFE_DOMAIN)]
    whole = "Reminders" if str(kind).casefold() == "reminders" else "Notifications"
    out += [f"{kind}: {n}" for n in SF.secret_fields({whole: spelled})]
    return out


def _json_text(v: Any) -> Any:
    """A string that holds a JSON object or array, parsed (content a step could hide from the key checks)."""
    if isinstance(v, str) and v.strip()[:1] in ("{", "["):
        try:
            return json.loads(v)
        except ValueError:
            return None
    return None


def _mail_parts(o: Any, path: str = "", notices: bool = False) -> list[str]:
    """Paths that could send mail or run a script, keys compared without case, JSON text read as content.
    notices=True: disabled notifications and reminders that pass notice_problems are allowed (probe site settings,
    settings steps); never in a teardown."""
    out = []
    if isinstance(o, dict):
        folded = [str(k).casefold() for k in o]
        if len(set(folded)) != len(folded):
            out.append(f"{path or '(top)'}: two keys differ only in case")
        for k, v in o.items():
            p = f"{path}.{k}" if path else k
            kf = str(k).casefold()
            if kf in ("notifications", "reminders") and v and notices:
                out += [f"{p}: {x}" for x in notice_problems(k, v)]
                continue
            if kf in ("notifications", "reminders", "serverscripts") and v:
                out.append(p)
            out += _mail_parts(v, p, notices)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            out += _mail_parts(v, f"{path}[{i}]", notices)
    elif (parsed := _json_text(o)) is not None:
        out += _mail_parts(parsed, f"{path}(json)", False)      # never notices inside a JSON string
    return out


PRINCIPAL_LISTS = ("users", "groups", "depts")


def literal_principals(o: Any, path: str = "") -> list[str]:
    """Paths of principal lists (`Users`, `Groups`, `Depts`, any depth, case ignored) that hold anything but
    `$admin_uid` / `$group_<role>` — a probe names no other principal (ADR-0027 item 3)."""
    out = []
    if isinstance(o, dict):
        for k, v in o.items():
            p = f"{path}.{k}" if path else str(k)
            if str(k).casefold() in PRINCIPAL_LISTS and isinstance(v, list):
                bad = [x for x in v if not (isinstance(x, str) and SETTINGS_VAR.fullmatch(x))]
                if bad:
                    out.append(f"{p} holds {bad[:3]}")
                continue
            out += literal_principals(v, p)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            out += literal_principals(v, f"{path}[{i}]")
    return out


def _named_lists(o: Any) -> bool:
    """Any non-empty Users / Groups / Depts list, at any depth."""
    if isinstance(o, dict):
        return any((str(k).casefold() in PRINCIPAL_LISTS and bool(v)) or _named_lists(v) for k, v in o.items())
    if isinstance(o, list):
        return any(_named_lists(x) for x in o)
    return False


def substitute_vars(o: Any, vars_: dict) -> Any:
    """`$admin_uid` / `$group_<role>` as a whole value → that id (an int when it is digits) — ADR-0027 item 3."""
    if isinstance(o, str):
        m = SETTINGS_VAR.fullmatch(o)
        if m:
            v = str(vars_[m.group(1)])
            return int(v) if v.isdigit() else v
        return o
    if isinstance(o, list):
        return [substitute_vars(x, vars_) for x in o]
    if isinstance(o, dict):
        return {k: substitute_vars(v, vars_) for k, v in o.items()}
    return o


def settings_steps(p: dict) -> list[dict]:
    return [st for spec in (p.get("tests") or []) for st in spec.get("steps") or [] if st.get("op") in SETTINGS_OPS]


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
    mail = _mail_parts(own, notices=True) + _mail_parts((p.get("teardown") or {}).get("SiteSettings") or {})
    for k, s in sites.items():                       # a further site holds no script at all (ADR-0026)
        mail += [f"sites.{k}.{x}" for x in _mail_parts(s.get("SiteSettings") or {}, notices=True)
                 + _mail_parts((s.get("teardown") or {}).get("SiteSettings") or {})]
    for st in settings_steps(p):                     # a settings step: same content rules, never a script (ADR-0027)
        what = st.get("SiteSettings") if st["op"] == "settings" else st.get("body")
        if not isinstance(what, dict) or not what:
            raise ValueError(f"a {st['op']} step needs a non-empty {'SiteSettings' if st['op'] == 'settings' else 'body'} object")
        if st["op"] == "settings_partial" and (
                not {str(k).casefold() for k in what} <= {"processes", "statuscontrols"}
                or not all(isinstance(v, list) for v in what.values())):
            # updatesitesettings reads the body as SiteSettingsApiModel and upserts by Id only ServerScripts, Scripts,
            # Styles, Htmls, Processes and StatusControls (Pleasanter_1.5.2.0 SiteUtilities.cs l.2358-2440,
            # source-derived); a probe step never carries a script or free HTML, so two lists remain
            raise ValueError("a settings_partial body holds only Processes and / or StatusControls lists — what "
                             "updatesitesettings upserts besides scripts, styles and HTML (ADR-0027, source-derived)")
        mail += [f"{st['op']} step: {x}" for x in _mail_parts(what, notices=True)]
    if mail:
        raise ValueError(f"probe sites must not send mail (notifications and reminders only disabled, to example.invalid, "
                         f"without credentials), and server scripts are allowed only at the top level of the probe's "
                         f"main site settings (ADR-0025, ADR-0026, ADR-0027): {mail}")
    named = literal_principals([p["site"].get("SiteSettings") or {}] + [(x.get("SiteSettings") or {}) for x in sites.values()]
                               + [st.get("SiteSettings") or st.get("body") for st in settings_steps(p)])
    if named:
        raise ValueError(f"principals named by id in probe settings: {named} — only $admin_uid and $group_<declared "
                         "role> (ADR-0027)")
    teardowns = [(p.get("teardown") or {}).get("SiteSettings") or {}] + [
        ((x.get("teardown") or {}).get("SiteSettings") or {}) for x in sites.values()]
    if literal_principals(teardowns) or any(_named_lists(t) for t in teardowns):   # a teardown is sent as written
        raise ValueError("a teardown names principals (Users / Groups / Depts): a teardown gets no variables and "
                         "leaves the site harmless — leave those lists out (ADR-0027)")
    if any(st.get("op") in SETTINGS_OPS for st in p.get("cleanup") or []):
        raise ValueError("cleanup steps never save settings (ADR-0027): only records the probe created")
    roles_declared = set(p.get("roles") or {})
    setting_texts = _strings([p["site"], [s for s in sites.values()],
                              [st.get("SiteSettings") or st.get("body") for st in settings_steps(p)]])
    undeclared = sorted({m.group(1)[6:] for t in setting_texts for m in [SETTINGS_VAR.match(t)]
                         if m and m.group(1).startswith("group_")} - roles_declared)
    if undeclared:
        raise ValueError(f"$group_{undeclared[0]} in probe site settings - only the group of a role declared in roles "
                         "(ADR-0027)")
    keys = {"main", *sites}
    refs = set()
    for o in [p["site"], p.get("teardown"), p.get("expect_stored")] + list(sites.values()) + settings_steps(p):
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
    """An entry passes only when all its judged probes pass; error wins over fail, fail over inconclusive. An observed
    probe decides nothing: an entry with only observations is `observed` (not verified — read the log)."""
    out: dict[str, str] = {}
    rank = ["pass", "inconclusive", "fail", "error"]
    for r in rows:
        if r["status"] == "observed":
            out.setdefault(r["entry"], "observed")
            continue
        cur = out.get(r["entry"], "pass")
        cur = "pass" if cur == "observed" else cur
        out[r["entry"]] = max(cur, r["status"], key=rank.index)
    return out


def entry_key(entry: str) -> tuple:
    """Sort key of a KB entry id: number first, then the letter of a split entry (D4 < D4a < D5)."""
    m = re.match(r"^D(\d+)([a-z]?)$", entry)
    return (int(m[1]), m[2]) if m else (10 ** 9, entry)


def report(env: str, version: dict | None, rows: list[dict], no_probe: list[str], today: str) -> str:
    app = (version or {}).get("app", "unknown")
    entries = entry_results(rows)
    out = [f"# KB verification — {env} — {today}", "", f"- **Pleasanter:** {app} (build {(version or {}).get('build')}, "
           f"schema {(version or {}).get('schema')})",
           f"- **Result:** {sum(v == 'pass' for v in entries.values())}/{len(entries)} entries verified "
           f"({sum(r['status'] == 'pass' for r in rows)}/{len(rows)} probes pass)", "",
           "| Entry | Result |", "|---|---|"]
    out += [f"| {k} | {v} |" for k, v in sorted(entries.items(), key=lambda x: entry_key(x[0]))]
    out += ["", "| Entry | Probe | Status | Detail |", "|---|---|---|---|"]
    for r in rows:
        passed = [x for x in r["log"] if x.startswith("ok")]               # reasons (NG, errors, control) survive the cut
        detail = "; ".join([x for x in r["log"] if not x.startswith("ok")] + passed)
        if len(detail) > 300:
            detail = detail[:300] + " … (full log in the .json)"
        out.append(f"| {r['entry']} | {r['probe']} | {r['status']} | {detail.replace('|', '/')} |")
    out += ["", "## Entries without a probe", "", ", ".join(no_probe) or "none", "",
            "A failing entry does not hold on this version: correct or split it by version (I9). "
            "`error` = the probe could not run (infrastructure), not a verdict on the entry; `inconclusive` = its control failed; `observed` = recorded behaviour without an expected outcome, whatever its checks said (read the detail; not a verification)."]
    return "\n".join(out) + "\n"
