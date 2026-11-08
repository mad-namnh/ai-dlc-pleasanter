"""Executable verification of the knowledge base (ADR-0009 part 2, plan BR8).

Each KB entry that skills rely on has probes in skills/pls-kb-pleasanter/references/probes/<name>.json:

    {"entry": "D10", "title": "…",
     "site": {"ReferenceType": "Issues", "SiteSettings": {…}},          # the probe site's configuration
     "expect_save": 200,                                                 # HTTP of updatesite (D30: 500)
     "expect_stored": {"Columns[ColumnName=Status].DefaultInput": null}, # stored settings (null = absent, D8)
     "control": "<other probe>",                                         # this result counts only if that one passes
     "server_dates": true,                                               # $today/$yesterday… from the server's clock
     "tests": [ … specs in the `pls test` format, confined to the probe site … ],
     "cleanup": [ … steps run after the tests (e.g. close what was created) … ]}

Safety: a probe can only create records on its own site and act on records it created (no `site`, `run_on`,
`as_key`, `vars`; ops create/get/list/exec). Probe sites never send mail (no notifications at any depth, no server
scripts). kb-verify reuses a probe site only when the site is provably its own (parent folder, title, type).
"""
from __future__ import annotations

import datetime as _dt
import json
import re
from pathlib import Path
from typing import Any

SELECTOR = re.compile(r"^(\w+)\[(\w+)=([^\]]*)\]$")
OPS = ("create", "get", "list", "exec")
FORBIDDEN_KEYS = ("site", "run_on", "as_key", "vars")
TITLE = "zz_kbprobe_{}"


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


def check_probe(p: dict) -> None:
    """Raise ValueError when a probe could send mail or touch anything but its own site and records."""
    mail = _mail_parts(p["site"].get("SiteSettings") or {})
    if mail:
        raise ValueError(f"probe sites must not send mail or run server scripts: {mail}")
    for spec in (p.get("tests") or []) + ([{"id": "cleanup", "steps": p["cleanup"]}] if p.get("cleanup") else []):
        bad = [k for k in FORBIDDEN_KEYS if k in spec]
        saved: set[str] = set(p.get("_shared_saves") or [])
        for st in spec.get("steps") or []:
            bad += [k for k in FORBIDDEN_KEYS if k in st]
            if st.get("op") not in OPS:
                raise ValueError(f"spec {spec.get('id')}: op {st.get('op')!r} not allowed (only {', '.join(OPS)})")
            if "record" in st:
                name = str(st["record"])
                if not name.startswith("$") or name[1:] not in saved:
                    raise ValueError(f"spec {spec.get('id')}: record {name!r} must be a record created earlier by this probe")
            if st.get("op") == "create" and st.get("save"):
                saved.add(st["save"])
        if bad:
            raise ValueError(f"spec {spec.get('id')}: keys {sorted(set(bad))} not allowed in probes (confined to the probe site)")
        p["_shared_saves"] = sorted(saved)


def load_probes(kb_dir: Path) -> list[dict]:
    out = []
    for f in sorted((kb_dir / "references" / "probes").glob("*.json")):
        if f.name == "index.json":
            continue
        p = json.loads(f.read_text(encoding="utf-8"))
        p["_name"] = f.stem
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
        out[r["entry"]] = max(cur, r["status"], key=rank.index)
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
            "`error` = the probe could not run (infrastructure), not a verdict on the entry; `inconclusive` = its control failed."]
    return "\n".join(out) + "\n"
