"""Configuration scope: which SiteSettings components are proven to round-trip (ADR-0001, plan BR3).

`updatesite` replaces the whole SiteSettings (D4). A component that does not survive export → updatesite → export
can be changed or lost by any deploy. `pls release-plan` therefore refuses a site whose live or git settings use a
component that has no round-trip evidence, unless a person accepts it with a decision record.

Evidence (0 differences after export → updatesite → export, and through pls unpack/pack):
- spike round 1 and slices #1–#3 (MADLAB dev and stg, 1.5.2; releases marked applied with 0 differences in
  pls-demo-inquiry, pls-demo-equipment, demo-equipment): every key below except the four BR3 ones;
- BR3 probe 2026-11-05 (`spike/round-trip/report-br3-20261105.md`): Scripts, Styles, Htmls, DashboardParts of types
  1 (timeline), 3 (HTML) and 4 (calendar);
- KB probe D33 2026-11-12 (`pls kb-verify`, MADLAB dev 1.5.2.0, ADR-0023): NearCompletionTimeBeforeDays /
  NearCompletionTimeAfterDays stored as sent (0 and 90 — above the UI maximum 30 of General.json) and used by a view
  with NearCompletionTime;
- KB probes D36, D41, D42 2026-11-14 (`pls kb-verify`, MADLAB dev 1.5.2.0 build 201520, ADR-0023; report
  `ops/kb-verify/2026-11-14-dev.md` of the trial that ran them): PermissionForCreating (`Group` and a group column
  key, value 15) stored as sent and applied to records created by two roles' test users and the administrator;
  Formulas (Default method, `NumB × NumA` into NumC) computed on API create and update; StatusControls (whole-record
  ReadOnly, and a ReadOnly column in ColumnHash) applied. These probes read back only the paths they name (e.g. a
  formula's Target), not the whole item after a second export. A status control that names principals
  (Depts/Groups/Users) is not covered: pls maps those ids (`${principal:x}`, pls.py ACL_LISTS), but no probe has
  round-tripped a status control with principals.
- KB probes D43–D47 2026-11-16 (`pls kb-verify`, MADLAB dev 1.5.2.0 build 201520, run by a person; evidence
  `plans/2026-11-16-scalar-keys-verified/evidence-kb-verify-2026-11-16-dev.md`): 85 scalar keys set to non-default
  values on probe sites and read back as sent (stored shape only, not their effect on the screen). Each key counts on
  its own: D46 keys read back as sent are here although probe D46 failed for one key (reading confirmed by Nam
  2026-11-16, ADR-0023). `AddressBook`, `MailToDefault`, `MailCcDefault`, `MailBccDefault` (D47) round-trip and are
  here since they are kept out of git (ADR-0010, 2026-11-16): they never appear in config/ or a payload, and every
  write carries the values the site holds (pls_http.LIVE_ONLY_KEYS).
  Not here: `DashboardPartsAsynchronousLoading` (D46) was not stored — it is recorded only when it
  differs from the server parameter Dashboard.AsynchronousLoadingDefault (source-derived);
  `ServerScriptsAllDisabled`, `ScriptsAllDisabled`, `HtmlsAllDisabled`, `AllowPhysicalDeleteHistories`,
  `AllowMigrationMode`, `ExtendedHeader` round-trip and are here since classify names them (2026-11-18, TD-63 closed):
  the first, fourth and fifth are permission-impacting, the others config-only with a rule of their own.
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
    # the 完了間近 range of NearCompletionTime views (KB D33, ADR-0023)
    "NearCompletionTimeBeforeDays", "NearCompletionTimeAfterDays",
    # record permissions at creation, formulas, status controls (KB D36, D41, D42, ADR-0023)
    "PermissionForCreating", "Formulas", "StatusControls",
    # dashboards (part types checked separately)
    "DashboardParts",
    # scalar switches, stored shape (KB D43–D47, ADR-0023)
    "SwitchRecordWithAjax", "SwitchCommandButtonsAutoPostBack", "AutoVerUpType", "AfterCreateActionType",
    "AfterUpdateActionType", "AllowEditingComments", "AllowCopy", "AllowReferenceCopy", "CharToAddWhenCopying",
    "AllowSeparate", "AllowLockTable", "OpenEditInNewTab", "DeleteImageWhenDeleting", "GuideAllowExpand", "GuideExpand",
    "Responsive", "HideLink", "DisableLinkToEdit", "EnableExpandLinkPath", "GeneralTabLabelText",               # D43
    "GridPageSize", "GridEditorType", "HistoryOnGrid", "AllowRestoreHistories",
    "UseFilterButton", "UseFiltersArea", "UseGridHeaderFilters", "UseNegativeFilters", "UseRelatingColumnsOnFilter",
    "UseIncompleteFilter", "UseOwnFilter", "UseNearCompletionTimeFilter", "UseDelayFilter", "UseOverdueFilter",
    "UseSearchFilter", "AlwaysRequestSearchCondition", "DisableSiteConditions", "AllowViewReset", "SaveViewType",
    "SearchType", "FullTextIncludeBreadcrumb", "FullTextIncludeSiteId", "FullTextIncludeSiteTitle",
    "FullTextNumberOfMails", "LinkPageSize", "LinkTableView", "AllowPhysicalDeleteHistories",                    # D44
    "EnableCalendar", "EnableCrosstab", "EnableGantt", "EnableBurnDown", "EnableTimeSeries", "EnableAnaly",
    "EnableKamban", "EnableImageLib", "CalendarType", "NoDisplayCrosstabGraph", "ShowGanttProgressRate",
    "ImageLibPageSize", "FirstDayOfWeek", "FirstMonth",                                                           # D45
    "FormulasGetErrorDetails", "OutputFormulaLogs", "ProcessOutputFormulaLogs", "StylesAllDisabled",
    "ServerScriptsGetErrorDetails", "ServerScriptsAllDisabled", "ScriptsAllDisabled", "HtmlsAllDisabled",
    "ExtendedHeader",                                                                                             # D46
    "AllowStandardExport", "StandardExportType", "ImportEncoding", "UpdatableImport", "DefaultImportKey",
    "RejectNullImport", "FormStartDateTime", "FormEndDateTime", "FormThanksMessage",
    "FormUnavailableMessage", "AddressBook", "MailToDefault", "MailCcDefault", "MailBccDefault",
    "AllowMigrationMode",                                                                                         # D47
})
VERIFIED_DASHBOARD_TYPES = frozenset({1, 3, 4})
DASHBOARD_TYPE_NAMES = {0: "quick access", 1: "timeline", 3: "HTML", 4: "calendar", 5: "kanban"}


VIEW_REQUIRED_TYPES = frozenset({1, 4, 5})    # without "View" updatesite fails with HTTP 500 (D30)


def unverified(settings: dict) -> list[str]:
    """Components of one SiteSettings without round-trip evidence, and dashboard parts that would fail to save."""
    out = [f"{k} (no round-trip evidence)" for k in sorted(set(settings or {}) - VERIFIED_KEYS)]
    for c in (settings or {}).get("StatusControls") or []:
        if isinstance(c, dict) and any(c.get(k) for k in ("Depts", "Groups", "Users")):
            out.append(f"StatusControls[{c.get('Id', '?')}] names principals (Depts/Groups/Users): mapped to "
                       "${principal:x}, but no round-trip evidence for a status control with principals")
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
