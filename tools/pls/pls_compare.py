"""Comparing one site across environments (plan BR5). Pure helpers; pls.py does the I/O.

Sources are local files only — a getsite export (`pls export`, `pls adopt`) or a Pleasanter **site package**
(the JSON a person exports from the UI, e.g. a customer's prod). Nothing is read from or written to Pleasanter.

Each source is turned into the logical model with its own environment's ids (`${site:x}`, `${principal:x}`),
so ids that differ between environments disappear. What remains is classified:
- id-like      — values equal once digits are ignored: an id that is not mapped yet (map it, or adopt that site);
- not-in-package — the package was exported without that part (HeaderInfo Include… flags), not a difference;
- content      — a real difference in configuration: intended per-environment value, or drift to decide on.
"""
from __future__ import annotations

import json
import re
from typing import Any

PACKAGE_PARTS = {"IncludeNotifications": "Notifications", "IncludeReminders": "Reminders"}


def is_package(doc: Any) -> bool:
    return isinstance(doc, dict) and "HeaderInfo" in doc and isinstance(doc.get("Sites"), list)


def from_package(pkg: dict, site_id: int | None = None) -> tuple[dict, dict]:
    """(export-shaped document, info) for one site of a site package. info: app version, missing parts."""
    h = pkg.get("HeaderInfo") or {}
    sites = {int(s["SiteId"]): s for s in pkg["Sites"] if s.get("SiteId") is not None}
    listing = ", ".join(f"{k} {v.get('Title')!r}" for k, v in sorted(sites.items()))
    if site_id is None and len(sites) > 1:
        raise ValueError(f"the package holds several sites ({listing}); map this site's id for that environment first")
    sid = int(site_id or h.get("BaseSiteId") or next(iter(sites), 0))
    if sid not in sites:
        raise ValueError(f"site {sid} is not in the package (sites: {listing})")
    site = dict(sites[sid])
    ss = site.get("SiteSettings")
    site["SiteSettings"] = json.loads(ss) if isinstance(ss, str) else (ss or {})
    perms = next((p.get("Permissions") or [] for p in pkg.get("Permissions") or [] if int(p.get("SiteId", 0)) == sid), None)
    if perms is not None and h.get("IncludeSitePermission", True):
        entries = []
        for x in perms:
            for typ, key in (("Dept", "DeptId"), ("Group", "GroupId"), ("User", "UserId")):
                if x.get(key):
                    entries.append(f"{typ},{x[key]},{x.get('PermissionType')}")
        site["Permissions"] = entries
    missing = [part for flag, part in PACKAGE_PARTS.items() if h.get(flag) is False]
    if not h.get("IncludeSitePermission", True):
        missing.append("permissions")
    names = {f"Group,{g['GroupId']}": g.get("GroupName") for g in (pkg.get("PermissionIdList") or {}).get("GroupIdList") or []}
    names |= {f"User,{u['UserId']}": u.get("LoginId") or u.get("Name") for u in (pkg.get("PermissionIdList") or {}).get("UserIdList") or []}
    return {"StatusCode": 200, "Response": {"Data": site}}, {
        "app": h.get("AssemblyVersion"), "package_time": h.get("PackageTime"), "missing": missing, "principal_names": names,
        "site": f"{sid} {site.get('Title')!r}"}


DIGITS = re.compile(r"\d+")
SEGMENT = re.compile(r"\[[^\]]*\]")


def _id_like(before: Any, after: Any, key: str, values: set[str]) -> bool:
    """True only when the change looks like an unmapped id: an integer under an *Id key, or strings that differ
    only in runs of 3+ digits that are not environment values. Settings numbers, script bodies and versions never."""
    if isinstance(before, bool) or isinstance(after, bool):
        return False
    if isinstance(before, (int, float)) and isinstance(after, (int, float)):
        return key.endswith("Id") and isinstance(before, int) and isinstance(after, int)
    a = json.dumps(before, ensure_ascii=False, sort_keys=True)
    b = json.dumps(after, ensure_ascii=False, sort_keys=True)
    if a == b or DIGITS.sub("#", a) != DIGITS.sub("#", b):
        return False
    changed = [(x, y) for x, y in zip(DIGITS.findall(a), DIGITS.findall(b)) if x != y]
    return all(len(x) >= 3 and len(y) >= 3 and x not in values and y not in values for x, y in changed)


def classify(diff: dict, missing: list[str], values: set[str] | None = None) -> str:
    path = diff["path"]
    parts = [SEGMENT.sub("", p) for p in path.split(".")]
    if any(m in parts for m in missing):
        return "not-in-package"
    if path.startswith("scripts.") or parts[-1] in ("Body", "Version"):
        return "content"
    if diff.get("before") is not None and diff.get("after") is not None and \
            _id_like(diff["before"], diff["after"], parts[-1], values or set()):
        return "id-like"
    return "content"


def comparable(model: dict, with_permissions: bool = True) -> dict:
    """The parts of a logical model that must match across environments. Titles and the site description (Body)
    differ per environment by design and are left out; permissions only when both sides carry them (ADR-0006)."""
    out = {"settings": model["settings"], "scripts": model["scripts"],
           "meta": {k: v for k, v in model["meta"].items() if k in ("ReferenceType",)}}
    if with_permissions:
        out["permissions"] = model.get("permissions")
    return out


def report(site: str, rows: list[dict], sources: list[str], notes: list[str], today: str, short) -> str:
    out = [f"# Environment comparison — {site}", "", f"- **Date:** {today}",
           f"- **Sources (local files; nothing read from Pleasanter):** {', '.join(sources)}", ""]
    out += [f"- {n}" for n in notes] + [""]
    for pair in sorted({r["pair"] for r in rows}):
        rs = [r for r in rows if r["pair"] == pair]
        counts = {c: sum(1 for r in rs if r["class"] == c) for c in ("content", "id-like", "not-in-package")}
        out += [f"## {pair}", "", f"content {counts['content']} · id-like {counts['id-like']} · not in package {counts['not-in-package']}", "",
                "| Class | Path | Left | Right |", "|---|---|---|---|"]
        for r in sorted(rs, key=lambda x: ("content", "id-like", "not-in-package").index(x["class"]))[:200]:
            out.append(f"| {r['class']} | `{r['path']}` | {short(r.get('before'))} | {short(r.get('after'))} |")
        if len(rs) > 200:
            out.append(f"| … | {len(rs) - 200} more | | |")
        out.append("")
    if not rows:
        out.append("No differences after mapping ids to logical names.")
    out += ["", "## How to decide", "",
            "- **content:** an intended per-environment value → move it to `values` and use `${env:x}`; otherwise drift → decide (accept as change request, or revert).",
            "- **id-like:** an id not mapped in `environments.json` (site or principal) → adopt or map it, then compare again.",
            "- **not-in-package:** export the package again with that option, or compare with a getsite export."]
    return "\n".join(out) + "\n"
