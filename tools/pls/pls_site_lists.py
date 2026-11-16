"""Site ids inside the site lists of SiteSettings.

Pleasanter_1.5.2.0 names other sites in these places, by site id or by `SiteName` / `SiteGroupName`:
- `MoveTargets` — `List<long>` of site ids (SiteSettings.cs l.193);
- `IntegratedSites` — `List<string>`, each a site name / group name or an id; the name is tried first
  (SiteSettings.GetIntegratedSites);
- `DashboardParts[].TimeLineSites / CalendarSites / IndexSites / KambanSites` — comma-separated text, each element an
  id or a name, the id tried first (DashboardPart.GetDashboardPartSites), and their parsed copies `*SitesData`;
- `DashboardParts[].QuickAccessSites` — JSON text `[{"Id": "<id or name>", …}]`, or comma / line separated ids or
  names (DashboardPart.SetQuickAccessSitesData).

An element made only of ASCII digits is a site id: it becomes `${site:x}` when environments.json knows the site and
stays raw otherwise (lint L-PERM-01 reports it, pack refuses it). Anything else is a name and is kept as written.
Limits: a name is resolved by Pleasanter on each environment against that tenant's SiteName / SiteGroupName — pls
neither deploys nor checks those names, so `${site:x}` is the safe form; an all-digit SiteGroupName in
IntegratedSites cannot be written (it reads as an id); QuickAccessSites text that starts with "[" but is not JSON
Python can read is reported and refused rather than guessed.
"""
from __future__ import annotations

import json
import re
from typing import Callable

REF = re.compile(r"\$\{site:([A-Za-z0-9_\-]+)\}")
SITE_ID = re.compile(r"[0-9]+")                 # ASCII digits only: full-width digits are a name to Pleasanter
TEXT_KEYS = ("TimeLineSites", "CalendarSites", "IndexSites", "KambanSites")
DATA_KEYS = ("TimeLineSitesData", "CalendarSitesData", "IndexSitesData", "KambanSitesData")


class Unreadable(ValueError):
    """QuickAccessSites starts like JSON but cannot be read."""


def is_id(x) -> bool:
    return isinstance(x, int) and not isinstance(x, bool) or isinstance(x, str) and bool(SITE_ID.fullmatch(x.strip()))


def _split_keep(s: str, fn: Callable[[str], str]) -> str:
    """Apply fn to each comma / line separated element, keeping separators and surrounding whitespace."""
    out, cur = [], ""
    for ch in s + "\0":
        if ch in ",\n\0":
            core = cur.strip()
            if core:
                lead, trail = cur[:len(cur) - len(cur.lstrip())], cur[len(cur.rstrip()):]
                cur = lead + fn(core) + trail
            out.append(cur + (ch if ch != "\0" else ""))
            cur = ""
        else:
            cur += ch
    return "".join(out)


def _quick_access(s: str, fn: Callable[[str], str]) -> str:
    if not s.strip().startswith("["):
        return _split_keep(s, fn)
    try:
        items = json.loads(s)
    except ValueError as ex:
        raise Unreadable(f"QuickAccessSites is not readable JSON ({ex})")
    changed = False                                              # text starting with "[" that parses is a list
    for it in items:
        if not isinstance(it, dict):
            continue
        for k in [k for k in it if k.lower() == "id"]:            # Newtonsoft matches property names ignoring case
            v = it[k]
            raw = str(v) if is_id(v) else v
            if not isinstance(raw, str):
                continue
            new = fn(raw)
            if new != raw:                                        # only a mapped or resolved id is rewritten
                it[k], changed = new, True
    return json.dumps(items, ensure_ascii=False) if changed else s


def _walk(settings: dict, on_id: Callable[[str, str], str], on_bad: Callable[[str, Exception], None]) -> None:
    """on_id(where, element) → replacement, for every string element of every site list (MoveTargets excepted);
    on_bad(where, error) for QuickAccessSites text that cannot be read (the other lists are still walked)."""
    if isinstance(settings.get("IntegratedSites"), list):
        settings["IntegratedSites"] = [on_id("IntegratedSites", x) if isinstance(x, str) else x
                                       for x in settings["IntegratedSites"]]
    for part in settings.get("DashboardParts") or []:
        if not isinstance(part, dict):
            continue
        where = f"DashboardParts[{part.get('Id', '?')}]"
        for k in TEXT_KEYS:
            if isinstance(part.get(k), str):
                part[k] = _split_keep(part[k], lambda x, k=k: on_id(f"{where}.{k}", x))
        if isinstance(part.get("QuickAccessSites"), str):
            try:
                part["QuickAccessSites"] = _quick_access(part["QuickAccessSites"],
                                                         lambda x: on_id(f"{where}.QuickAccessSites", x))
            except Unreadable as ex:
                on_bad(f"{where}.QuickAccessSites", ex)
        for k in DATA_KEYS:
            if isinstance(part.get(k), list):
                part[k] = [on_id(f"{where}.{k}", x) if isinstance(x, str) else x for x in part[k]]


def to_refs(settings: dict, ids: dict[str, str]) -> None:
    """Export → git, in place: a known site id → ${site:x}; names and unknown ids unchanged. Unreadable
    QuickAccessSites text is left as it is (lint reports it)."""
    def ref(x: str) -> str:
        return "${site:%s}" % ids[x.strip()] if is_id(x) and x.strip() in ids else x
    if isinstance(settings.get("MoveTargets"), list):
        settings["MoveTargets"] = [ref(str(x)) if is_id(x) and str(x) in ids else x for x in settings["MoveTargets"]]
    _walk(settings, lambda _w, x: ref(x), lambda _w, _ex: None)


def from_refs(settings: dict, site_id: Callable[[str], int], site: str, fail: Callable[[str], Exception]) -> None:
    """Git → payload, in place: ${site:x} → this environment's id (an int in MoveTargets); a raw id refuses."""
    if isinstance(settings.get("MoveTargets"), list):
        out = []
        for x in settings["MoveTargets"]:
            m = REF.fullmatch(x) if isinstance(x, str) else None
            if not m:
                raise fail(f"{site}: MoveTargets uses the environment-specific site id {x} (L-PERM-01) — write "
                           "${site:<name>} for it")
            out.append(site_id(m.group(1)))
        settings["MoveTargets"] = out

    def on_id(where: str, x: str) -> str:
        m = REF.fullmatch(x.strip())
        if m:
            return x.replace(m.group(0), str(site_id(m.group(1))))
        if is_id(x):
            raise fail(f"{site}: {where} uses the environment-specific site id {x.strip()} (L-PERM-01) — write "
                       "${site:<name>} for it")
        return x
    def on_bad(where: str, ex: Exception):
        raise fail(f"{site}: {where}: {ex} — fix the text so its site ids can be checked (L-PERM-01)")
    _walk(settings, on_id, on_bad)


def raw_ids(settings: dict) -> list[str]:
    """`where: value` of every site id left raw in git, and of unreadable QuickAccessSites (lint L-PERM-01)."""
    import copy
    found: list[str] = []
    for x in settings.get("MoveTargets") or []:
        if not (isinstance(x, str) and REF.fullmatch(x)):
            found.append(f"MoveTargets: {x}")

    def note(where: str, x: str) -> str:
        if is_id(x):
            found.append(f"{where}: {x.strip()}")
        return x
    _walk(copy.deepcopy({k: v for k, v in settings.items() if k != "MoveTargets"}), note,
          lambda where, ex: found.append(f"{where}: {ex}"))
    return found
