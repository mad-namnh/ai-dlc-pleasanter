"""Configuration scope: which SiteSettings components are proven to round-trip (ADR-0001, plan BR3).

`updatesite` replaces the whole SiteSettings (D4). A component that does not survive export → updatesite → export
can be changed or lost by any deploy. `pls release-plan` therefore refuses a site whose live or git settings use a
component that has no round-trip evidence, unless a person accepts it with a decision record.

Evidence (0 differences after export → updatesite → export, and through pls unpack/pack):
- spike round 1 and slices #1–#3 (MADLAB dev and stg, 1.5.2; releases marked applied with 0 differences in
  pls-demo-inquiry, pls-demo-equipment, demo-equipment): every key below except the four BR3 ones;
- BR3 probe 2026-11-05 (`spike/round-trip/report-br3-20261105.md`): Scripts, Styles, Htmls, DashboardParts of types
  1 (timeline), 3 (HTML) and 4 (calendar).
Add a key here only with such evidence (I9), and record it in the KB and the spike checklist.

Granularity: the evidence is per **top-level key** with the attributes those sites used (columns: label, type,
required, choices, format; notifications: mail; views: filters, sorters, crosstab; Htmls PositionType 1000/1010).
Attributes inside a verified key that were never used (per-column extended HTML, webhook notifications,
calendar/kanban views, …) are not checked here — ADR-0001 "Known limits".
"""
from __future__ import annotations

VERIFIED_KEYS = frozenset({
    # structure and defaults present on every site (D26)
    "Version", "ReferenceType", "NoDisplayIfReadOnly", "NotInheritPermissionsWhenCreatingSite",
    # columns, screens, views, links
    "Columns", "EditorColumnHash", "GridColumns", "FilterColumns", "GridView", "TitleColumns", "TitleSeparator",
    "LinkColumns", "Links", "Views", "ViewLatestId",
    # automation, workflow, aggregation
    "Notifications", "Reminders", "Processes", "Summaries", "Aggregations",
    # code
    "ServerScripts", "Scripts", "Styles", "Htmls",
    # dashboards (part types checked separately)
    "DashboardParts",
})
VERIFIED_DASHBOARD_TYPES = frozenset({1, 3, 4})
DASHBOARD_TYPE_NAMES = {0: "quick access", 1: "timeline", 3: "HTML", 4: "calendar", 5: "kanban"}


VIEW_REQUIRED_TYPES = frozenset({1, 4, 5})    # without "View" updatesite fails with HTTP 500 (D30)


def unverified(settings: dict) -> list[str]:
    """Components of one SiteSettings without round-trip evidence, and dashboard parts that would fail to save."""
    out = [f"{k} (no round-trip evidence)" for k in sorted(set(settings or {}) - VERIFIED_KEYS)]
    for p in (settings or {}).get("DashboardParts") or []:
        if not isinstance(p, dict):
            out.append("DashboardParts item is not an object (no round-trip evidence)")
            continue
        pid, t = p.get("Id", "?"), p.get("Type")
        if "Type" not in p:
            out.append(f"DashboardParts[{pid}] has no Type (a default-valued type is dropped on save, D8; "
                       "type 0 quick access has no round-trip evidence)")
        elif type(t) is not int:
            out.append(f"DashboardParts[{pid}] Type {t!r} is not an integer (no round-trip evidence)")
        elif t not in VERIFIED_DASHBOARD_TYPES:
            out.append(f"DashboardParts[{pid}] type {t} ({DASHBOARD_TYPE_NAMES.get(t, 'unknown type')}) (no round-trip evidence)")
        if type(t) is int and t in VIEW_REQUIRED_TYPES and not isinstance(p.get("View"), dict):
            out.append(f"DashboardParts[{pid}] type {t} has no View object — updatesite would fail with HTTP 500 (D30)")
    return out


def site_findings(live: dict, git: dict) -> list[str]:
    """Unverified components in the live settings or the git settings of a site (deduplicated)."""
    return sorted(set(unverified(live)) | set(unverified(git)))
