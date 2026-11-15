# Settings coverage — Pleasanter 1.5.2 settings against the framework (inventory)

- **Asked by:** Nam, 2026-11-15: list which Pleasanter 1.5.2 settings the framework already supports and which are missing (at least the settings the API supports), then write a detailed implementation plan (`plan.md`).
- **Sources:**
  - Pleasanter source, tag `Pleasanter_1.5.2.0` (GitHub Implem/Implem.Pleasanter, read 2026-11-15, sparse checkout of `Libraries/Settings`, `Controllers/Api`, `Models/Sites`):
    - `SiteSettings.RecordingData` (`Libraries/Settings/SiteSettings.cs` l.762–1908) lists every key Pleasanter **stores** for a site. A key that is not recorded is not stored, so it cannot be set through `updatesite` either.
    - The `GetRecordingData` / `RecordingData` methods of the item classes (`Column`, `View`, `Process`, …) list the stored attributes.
    - `Controllers/Api/*.cs` lists the API routes.
  - Framework at commit `2168ca4`: `tools/pls/pls_scope.py` (`VERIFIED_KEYS`), `pls.py` (`to_refs` / `acl_to_refs` / `classify`), `pls_address_principals.py`, `pls_scripts.py`, the KB (`skills/pls-kb-pleasanter/references/*.md`) and the skills.
- **What "supported" means.** `pls` carries every key: `unpack` / `pack` keep the whole `SiteSettings` in `config/<site>/site.json` (scripts are split into files). A key is **fully supported** when all four of these hold:
  1. **Round-trip evidence.** The key is in `VERIFIED_KEYS`, so `release-plan` does not refuse it (ADR-0001).
  2. **Environment mapping.** Every environment-specific id inside it is mapped (`${site:x}`, `${principal:x}`, `${env:x}`).
  3. **Classification.** `pls classify` puts a change to it in the right class (ADR-0004).
  4. **Design knowledge.** The KB (and the P2 designer where it matters) knows its shape and behaviour.

  A key without round-trip evidence can still be deployed, but only with `--accept-unverified` and a decision record.
- **Not covered here:** what each setting does on the screen (UI behaviour). The KB records that only from probes or a person's observation (CLAUDE.md, Mandatory 5).

## Summary

| Measure | Count |
|---|---|
| Top-level `SiteSettings` keys Pleasanter 1.5.2.0 stores | **130** |
| — with round-trip evidence (`VERIFIED_KEYS`) | **30** (23 %) |
| — named anywhere in the KB | 29 |
| — without evidence, KB entry or any `pls` code | 94 |
| Keys holding environment-specific ids | 22 |
| — mapped fully | 10 (Columns, Links, Summaries, Processes, Notifications, Reminders, ServerScripts, Scripts, Styles, Htmls) |
| — not (fully) mapped: ids would be deployed raw to another environment | 12 (StatusControls principals — refused today; Views, Exports, DashboardParts, Create/Read/UpdateColumnAccessControls principals; MoveTargets; IntegratedSites; MailTo/Cc/BccDefault tokens) |
| Keys whose change class is wrong or missing in `pls classify` | 5 (Formulas, StatusControls, Views access, Exports access, DashboardParts access) — fixed by WS2 (`plans/2026-11-15-classify-formulas-access-lists/`) |
| API routes (1.5.2.0) | 53 in 12 controllers |
| — used by `pls` | 15 |

**Reading.** The 30 verified keys cover what the demo apps and the trial used: columns, editor, grid, views, links, summaries, processes, status controls, notifications, reminders, formulas, permissions at creation, scripts and dashboards (3 of 5 part types).

Most of the 100 unverified keys are scalar switches: the `Use*Filter` flags, the `Enable*` view modes, `Allow*` features, page sizes and the form dates. A few probes that set non-default values could prove them in batches. The real gaps are:

- (a) **Principals inside views, exports, dashboards, column access control and status controls.** They are not mapped, so a release would deploy dev ids to stg.
- (b) **Change classes.** Changes to `Formulas[]` and to the access lists inside views, exports and dashboards are not classified as data-impacting or permission-impacting. (Fixed by WS2, 2026-11-15.)
- (c) **Column attributes and view attributes.** Only a minority has evidence (table B).
- (d) **API surfaces with no tool:** depts, CSV import/export, `SynchronizeSummaries`, `updatesitesettings` (partial update), binaries, extensions.

## A. Top-level `SiteSettings` keys (130)

"Round-trip evidence": `tools/pls/pls_scope.py` `VERIFIED_KEYS`. "KB": the KB files that name the key (sch = schema.md, beh = behaviours.md, ske = skeletons.md, api = api.md). "Env-specific ids": source class fields plus the `pls` mapping. "Change classification": `pls.py` `classify`.

| # | Key | Round-trip evidence (pls_scope) | KB | Env-specific ids (pls mapping) | Change classification | Note |
|---|---|---|---|---|---|---|
| | **1 Structure** | | | | | |
| 1 | `Version` | yes | api, behaviours, skeletons | — | config-only | set by Pleasanter |
| 2 | `ReferenceType` | yes | api, behaviours, skeletons | — | config-only | fixed at createsite |
| | **2 Editor, columns, record screen** | | | | | |
| 3 | `Columns` | yes | behaviours, schema, skeletons | site ids in `ChoicesText` (`[[id]]`, JSON `SiteId`) — mapped (`${site:x}`); `[[Users*]]`/`[[Groups*]]` — no ids | removed column / removed choices / link change → data-impacting; rest config-only | attributes: see table B |
| 4 | `EditorColumnHash` | yes | behaviours, schema, skeletons | — | config-only |  |
| 5 | `Sections` | — | — | — | config-only | `pls merge` knows the key; no evidence |
| 6 | `SectionLatestId` | — | — | — | config-only | counter: keep with Sections |
| 7 | `Tabs` | — | — | — | config-only | `pls merge` knows the key; no evidence |
| 8 | `TabLatestId` | — | — | — | config-only | counter: keep with Tabs |
| 9 | `GeneralTabLabelText` | — | — | — | config-only |  |
| 10 | `TitleColumns` | yes | — | — | config-only |  |
| 11 | `TitleSeparator` | yes | — | — | config-only |  |
| 12 | `NoDisplayIfReadOnly` | yes | behaviours, skeletons | — | config-only |  |
| 13 | `SwitchRecordWithAjax` | — | — | — | config-only |  |
| 14 | `SwitchCommandButtonsAutoPostBack` | — | — | — | config-only |  |
| 15 | `AutoVerUpType` | — | — | — | config-only |  |
| 16 | `AfterCreateActionType` | — | — | — | config-only |  |
| 17 | `AfterUpdateActionType` | — | — | — | config-only |  |
| 18 | `AllowEditingComments` | — | — | — | config-only |  |
| 19 | `AllowCopy` | — | — | — | config-only |  |
| 20 | `AllowReferenceCopy` | — | — | — | config-only |  |
| 21 | `CharToAddWhenCopying` | — | — | — | config-only |  |
| 22 | `AllowSeparate` | — | — | — | config-only |  |
| 23 | `AllowLockTable` | — | — | — | config-only |  |
| 24 | `OpenEditInNewTab` | — | — | — | config-only |  |
| 25 | `DeleteImageWhenDeleting` | — | — | — | config-only |  |
| 26 | `GuideAllowExpand` | — | — | — | config-only |  |
| 27 | `GuideExpand` | — | — | — | config-only |  |
| 28 | `Responsive` | — | — | — | config-only |  |
| 29 | `HideLink` | — | — | — | config-only |  |
| 30 | `DisableLinkToEdit` | — | — | — | config-only |  |
| 31 | `EnableExpandLinkPath` | — | — | — | config-only |  |
| | **3 Grid, filters, search, history** | | | | | |
| 32 | `GridColumns` | yes | behaviours, schema | — | config-only |  |
| 33 | `FilterColumns` | yes | schema | — | config-only |  |
| 34 | `GridView` | yes | — | — | config-only |  |
| 35 | `GridPageSize` | — | — | — | config-only |  |
| 36 | `GridEditorType` | — | — | — | config-only |  |
| 37 | `HistoryColumns` | — | — | — | config-only |  |
| 38 | `HistoryOnGrid` | — | — | — | config-only |  |
| 39 | `AllowRestoreHistories` | — | — | — | config-only |  |
| 40 | `AllowPhysicalDeleteHistories` | — | — | — | config-only; affects data retention (review) |  |
| 41 | `UseFilterButton` | — | — | — | config-only |  |
| 42 | `UseFiltersArea` | — | — | — | config-only |  |
| 43 | `UseGridHeaderFilters` | — | — | — | config-only |  |
| 44 | `UseNegativeFilters` | — | — | — | config-only |  |
| 45 | `UseRelatingColumnsOnFilter` | — | — | — | config-only |  |
| 46 | `UseIncompleteFilter` | — | — | — | config-only |  |
| 47 | `UseOwnFilter` | — | — | — | config-only |  |
| 48 | `UseNearCompletionTimeFilter` | — | — | — | config-only |  |
| 49 | `UseDelayFilter` | — | — | — | config-only |  |
| 50 | `UseOverdueFilter` | — | — | — | config-only |  |
| 51 | `UseSearchFilter` | — | — | — | config-only |  |
| 52 | `AlwaysRequestSearchCondition` | — | — | — | config-only |  |
| 53 | `DisableSiteConditions` | — | — | — | config-only |  |
| 54 | `AllowViewReset` | — | — | — | config-only |  |
| 55 | `SaveViewType` | — | — | — | config-only |  |
| 56 | `SearchType` | — | — | — | config-only |  |
| 57 | `FullTextIncludeBreadcrumb` | — | — | — | config-only |  |
| 58 | `FullTextIncludeSiteId` | — | — | — | config-only |  |
| 59 | `FullTextIncludeSiteTitle` | — | — | — | config-only |  |
| 60 | `FullTextNumberOfMails` | — | — | — | config-only |  |
| 61 | `LinkColumns` | yes | — | — | config-only |  |
| 62 | `LinkPageSize` | — | — | — | config-only |  |
| 63 | `LinkTableView` | — | — | — | config-only |  |
| 64 | `RelatingColumns` | — | — | — | config-only |  |
| 65 | `BulkUpdateColumns` | — | — | — | config-only |  |
| 66 | `IntegratedSites` | — | — | site ids (`List<string>`) — **not mapped** | config-only |  |
| 67 | `MoveTargets` | — | — | site ids (`List<long>`) — **not mapped** | config-only |  |
| | **4 Views and view modes** | | | | | |
| 68 | `Views` | yes | schema | `Depts/Groups/Users` (view access) — mapped by WS1.1; filter values may hold user/dept ids — **not mapped** (WS1.6) | **was config-only — fixed by WS2 (2026-11-15)**; `Depts/Groups/Users` → should be permission-impacting | attributes: see table B |
| 69 | `ViewLatestId` | yes | — | — | config-only | counter |
| 70 | `EnableCalendar` | — | — | — | config-only |  |
| 71 | `CalendarType` | — | schema | — | config-only |  |
| 72 | `EnableCrosstab` | — | schema | — | config-only |  |
| 73 | `NoDisplayCrosstabGraph` | — | schema | — | config-only |  |
| 74 | `EnableGantt` | — | — | — | config-only |  |
| 75 | `ShowGanttProgressRate` | — | — | — | config-only |  |
| 76 | `EnableBurnDown` | — | — | — | config-only |  |
| 77 | `EnableTimeSeries` | — | — | — | config-only |  |
| 78 | `EnableAnaly` | — | — | — | config-only |  |
| 79 | `EnableKamban` | — | — | — | config-only |  |
| 80 | `EnableImageLib` | — | — | — | config-only |  |
| 81 | `ImageLibPageSize` | — | — | — | config-only |  |
| 82 | `FirstDayOfWeek` | — | — | — | config-only |  |
| 83 | `FirstMonth` | — | — | — | config-only |  |
| 84 | `NearCompletionTimeBeforeDays` | yes | behaviours, schema | — | config-only |  |
| 85 | `NearCompletionTimeAfterDays` | yes | behaviours, schema | — | config-only |  |
| | **5 Links, summaries, formulas, aggregations** | | | | | |
| 86 | `Links` | yes | api, behaviours, schema | `SiteId` — mapped | config-only | JSON form with `Lookups` through `updatesite`: empty drop-down until a screen save (KB D40, TD-50) |
| 87 | `Summaries` | yes | schema | `SiteId` — mapped | added/changed → data-impacting note (D16) |  |
| 88 | `Formulas` | yes | behaviours, schema | — | **was config-only — fixed by WS2 (2026-11-15)** (classify checks `Columns[x].Formula`, which 1.5.2 does not record); whether stored values of existing records are recomputed is not known → treat as data-impacting until probed | D41 verified (Default method) |
| 89 | `FormulasGetErrorDetails` | — | — | — | config-only |  |
| 90 | `OutputFormulaLogs` | — | — | — | config-only |  |
| 91 | `ProcessOutputFormulaLogs` | — | — | — | config-only |  |
| 92 | `Aggregations` | yes | schema | — | config-only |  |
| | **6 Workflow** | | | | | |
| 93 | `Processes` | yes | api, behaviours, schema | `Groups/Users/Depts` — mapped (`${principal:x}`, D20); `Notifications[].Address` tokens — mapped | Groups/Users/Depts → permission-impacting | attributes: see table B |
| 94 | `StatusControls` | yes | behaviours, schema | `Groups/Users/Depts` — mapped by WS1.1 (2026-11-15); release-plan still refuses without evidence (pls_scope) | **was config-only — fixed by WS2 (2026-11-15)** → should be permission-impacting | D42 verified (no principals) |
| | **7 Notifications and mail** | | | | | |
| 95 | `Notifications` | yes | api, schema | address tokens `[Group<id>]`… — mapped (`${principal:x}`); `Token` (webhook secret, I7) | config-only | mail type only verified; webhook types not (ADR-0001 known limits) |
| 96 | `Reminders` | yes | schema | `To` tokens — mapped; `Token` (I7) | config-only |  |
| 97 | `MailToDefault` | — | — | addresses / `[Group<id>]` tokens — **not mapped** (pls_address_principals covers mail elements of Notifications / Reminders / processes only) | config-only |  |
| 98 | `MailCcDefault` | — | — | same | config-only |  |
| 99 | `MailBccDefault` | — | — | same | config-only |  |
| 100 | `AddressBook` | — | — | mail addresses (may be personal data) | config-only |  |
| | **8 Permissions** | | | | | |
| 101 | `PermissionForCreating` | yes | api, behaviours, schema | keys `Group`/`Dept`/`User`/column names — no ids | permission-impacting (name contains Permission) | D36 verified |
| 102 | `PermissionForUpdating` | — | behaviours, schema | same as PermissionForCreating | permission-impacting | D36 source-derived only |
| 103 | `CreateColumnAccessControls` | — | — | `Depts/Groups/Users` — mapped by WS1.1; `RecordUsers` — open (WS1.2) | permission-impacting (AccessControl) |  |
| 104 | `ReadColumnAccessControls` | — | — | same as Create | permission-impacting |  |
| 105 | `UpdateColumnAccessControls` | — | — | same as Create (WS1.1) | permission-impacting |  |
| 106 | `NotInheritPermissionsWhenCreatingSite` | yes | behaviours, skeletons | — | permission-impacting (the key name contains Permission) |  |
| | **9 Import and export** | | | | | |
| 107 | `Exports` | — | — | `Depts/Groups/Users` — mapped by WS1.1; `Columns[].SiteId` (joined columns) — mapped | **was config-only — fixed by WS2 (2026-11-15)**; access lists → should be permission-impacting |  |
| 108 | `AllowStandardExport` | — | — | — | config-only |  |
| 109 | `StandardExportType` | — | — | — | config-only |  |
| 110 | `ImportEncoding` | — | — | — | config-only |  |
| 111 | `UpdatableImport` | — | — | — | config-only |  |
| 112 | `DefaultImportKey` | — | — | — | config-only |  |
| 113 | `RejectNullImport` | — | — | — | config-only |  |
| 114 | `AllowMigrationMode` | — | — | — | config-only |  |
| | **10 Code** | | | | | |
| 115 | `ServerScripts` | yes | behaviours, schema | site ids in id contexts — mapped (BR7) | config-only |  |
| 116 | `Scripts` | yes | behaviours, schema | same | config-only |  |
| 117 | `Styles` | yes | behaviours, schema | same | config-only |  |
| 118 | `Htmls` | yes | behaviours, schema | same | config-only |  |
| 119 | `ServerScriptsAllDisabled` | — | — | — | config-only |  |
| 120 | `ScriptsAllDisabled` | — | — | — | config-only |  |
| 121 | `StylesAllDisabled` | — | — | — | config-only |  |
| 122 | `HtmlsAllDisabled` | — | — | — | config-only |  |
| 123 | `ServerScriptsGetErrorDetails` | — | — | — | config-only |  |
| 124 | `ExtendedHeader` | — | — | HTML text — ids not scanned | config-only |  |
| | **11 Dashboards** | | | | | |
| 125 | `DashboardParts` | yes | behaviours, schema | `SiteId` mapped; `QuickAccessSites/TimeLineSites/CalendarSites/KambanSites/IndexSites` text and `*SitesData` — **not mapped** (WS1.4); `Depts/Groups/Users` — mapped by WS1.1 | **was config-only — fixed by WS2 (2026-11-15)**; access lists → should be permission-impacting | types 1, 3, 4 verified; 0 quick access, 5 kanban not |
| 126 | `DashboardPartsAsynchronousLoading` | — | — | — | config-only |  |
| | **12 Public form** | | | | | |
| 127 | `FormStartDateTime` | — | — | — | config-only |  |
| 128 | `FormEndDateTime` | — | — | — | config-only |  |
| 129 | `FormUnavailableMessage` | — | — | — | config-only |  |
| 130 | `FormThanksMessage` | — | — | — | config-only |  |

<!-- 130 keys -->

## B. Attributes inside the main lists

The evidence in `pls_scope` is per top-level key. Inside a verified key, only the attributes the demo apps, the trial or a probe actually used have evidence. Attribute counts come from each class's recording method in Pleasanter_1.5.2.0. Attributes with evidence are taken from the KB `schema.md` and `behaviours.md`.

| List | Attributes stored (1.5.2.0) | With evidence (KB) | Main gaps |
|---|---|---|---|
| `Columns[]` (by `ColumnName`) | 92 (e.g. `LabelText`, `ChoicesText`, `DefaultInput`, `ValidateRequired`, `EditorReadOnly`, `EditorFormat`, `Unit`, `Description`, `DecimalPlaces`, `Max`/`Min`/`Step`, `MaxLength`, `NoDuplication`, `MessageWhenDuplicated`, `Validate*` / regex, `AutoPostBack`, `ColumnsReturnedWhenAutomaticPostback`, `ControlType`, `ChoicesControlType`, `MultipleSelections`, `CopyByDefault`, `Hide`, `GridLabelText`, `Section`, extended CSS/HTML ×8, `AutoNumbering*` ×4, `Anchor*`, attachment limits ×8, `DateFilter*` ×8, `NumFilter*` ×3, `ImportKey`, `FullTextType`, `ExportFormat`, `GridFormat`, …) | `LabelText`, `ChoicesText` (incl. `[[id]]`, `[[Users*]]`), `ValidateRequired` (screen only, D27), `EditorReadOnly`, `EditorFormat`, `Unit`, `Description`, `DefaultInput` (D8), `AutoPostBack` (screen-observed, D40 — not a probe), `ChoicesText` JSON with `Lookups` (screen only; API path failed, D40 / TD-48) | about 80 attributes with no evidence. Gaps: uniqueness (`NoDuplication`), number bounds and decimals, regex validation, `ChoicesControlType` / `MultipleSelections` (multi-select stores a JSON array — is a change data-impacting?), auto-numbering, attachment limits, extended HTML/CSS |
| `Views[]` | 82 (filters, sorters, `Search`, `Own`, `Incomplete`, `Overdue`, `NearCompletionTime`, `Delay`, grid / filter columns per view, calendar ×12, crosstab ×8, gantt ×4, kanban ×7, time series ×5, command switches ×12, `Depts/Groups/Users`, `KeepFilterState`, …) | `ColumnFilterHash`, `ColumnSorterHash`, `DefaultMode`, `Overdue` (D24), `NearCompletionTime` (D33), `Crosstab*` ×5 (D39) | Gaps: calendar, gantt, kanban, time series and analysis parts; per-view grid columns; view access (`Depts/Groups/Users` — ids not mapped); command switches (e.g. hiding delete or bulk update on a view) |
| `Processes[]` | 27 | all main fields in schema.md; `ValidateInputs.Required` (D37: not checked by the server for an API process execution); access `Groups/Users/Depts` (D20) | `AutoNumbering` (exists, not yet exercised), `AllowBulkProcessing`, `OnClick`, `Icon`, `AfterProcessStatusChangeActionType`, `ValidateInputs` regex / min / max |
| `Processes[].DataChanges[]` | 7 | `Type` values, `BaseDateTime` (D8 default) | `ValueFormula*` options |
| `Notifications[]` | 27 | mail type: `Type 1`, `Address`, `Subject`, `Body`, conditions by view | webhook types (Slack, Teams, ChatWork, LINE, HTTP client: `MethodType`, `Headers`, `MediaType`, `Token` — secret, I7), `MonitorChangesColumns`, `After*` event switches, `Expression`, `UseCustomFormat` / `Format` |
| `Reminders[]` | 18 | `Type 10`, `ReminderType 1`, `Condition`, `Range`, `To: [Owner]` | other reminder types (chat tools), `StartDateTime` / `Type` repeat semantics, `ExcludeOverdue`, `NotSendIfNotApplicable` |
| `DashboardParts[]` | 42 | types 1 timeline, 3 HTML, 4 calendar (BR3); `View` required for types 1/4/5 (D30) | type 0 quick access (`QuickAccessSites` text holds site ids — not mapped), type 5 kanban, index parts (`IndexSites`), access `Depts/Groups/Users`, `ExtendedCss` |
| `Links[]` | 15 | `ColumnName`, `SiteId` | `JsonFormat` / `Lookups` deployed by `updatesite` (D40 (C): empty until a screen save), `View`, `NoAddButton`, `NotReturnParentRecord`, `ExcludeMe`, `MembersOnly`, `LinkActions`, `SearchFormat` |
| `Summaries[]` | 10 | all (D16, D23) | none on the key itself. Existing destination values are not recalculated (D16); a `SynchronizeSummaries` API exists, see C |
| `Formulas[]` | 12 | `Target`, `Formula`, `CalculationMethod` Default (D41) | `Condition` / `OutOfCondition`, `FormulaScript*` (script method), `NotUseDisplayName`, `IsDisplayError`; effect on existing records |
| `StatusControls[]` | 11 | `Status`, `ReadOnly`, `ColumnHash` (D42) | `View` condition; principals (refused) |
| `Aggregations[]` | 4 | `GroupBy: Status`, `Type 0` | `Type` 1/2, `Target` |
| `Sections[]`, `Tabs[]` | 4, 2 | — | everything (editor layout with sections / tabs) |
| `Exports[]` | 12 + columns | — | everything; access lists |
| `*ColumnAccessControls[]` | 6 | — | everything; ids |
| `BulkUpdateColumns[]`, `RelatingColumns[]` | 4, 3 | — | everything |
| `ServerScripts[]` | 25 | `Body`, `Name`, `Shared`, event flags used (D7) | `Background`, `TimeOut`, `Functionalize`, `TryCatch`, `WhenViewProcessing`, `WhenloadingRecord` |
| `Scripts[]` / `Styles[]` / `Htmls[]` | 16 / 16 / 17 | `All`, `New`, `Edit`, `Index`, `Disabled`, `PositionType` 1000/1010 (D29) | per-view switches (`Calendar`, `Gantt`, `Kamban`, …), other `PositionType` values |

## C. API routes (Pleasanter_1.5.2.0 `Controllers/Api`) and the framework

| Controller | Routes | Used by `pls` | Framework tool | Gap |
|---|---|---|---|---|
| Items — site | `GetSite`, `CreateSite`, `UpdateSite`, `DeleteSite` | all | `export`, `bootstrap`, `apply`, kb-verify cleanup | — |
| Items — site, partial | `updatesitesettings`: upserts or deletes items of `ServerScripts`, `Scripts`, `Styles`, `Htmls`, `Processes`, `StatusControls`, `Columns`, `EditorColumnHash`, `GridColumns`, `FilterColumns`, `Sections`, … (`Models/Sites/SiteUtilities.cs` l.2358) | no | — | Not used. It might deploy a JSON link (D40) without a screen save; unknown, needs a probe. |
| Items — site package | `CopySitePackage` | no | `pls package` builds its own package; `adopt-package` reads a site package file | API copy not used; not needed (ADR-0007 bootstrap) |
| Items — records | `Get`, `Create`, `Update`, `Delete`, `BulkUpsert` | yes | `test`, `migrate`, `backup`, kb-verify | — |
| Items — records | `Upsert`, `BulkDelete`, `Import` (CSV), `Export` (CSV) | no | — | `Import` / `Export` could serve master loads and backups; `BulkDelete` would clean up test data at scale |
| Items — summaries | `SynchronizeSummaries` | no | — | D16: an added summary does not recalculate existing values. This route calls `Summaries.Synchronize` (source-derived: `SiteUtilities.cs` l.17352), so it is the API way to recalculate them and **a tool is missing** (a data-impacting step after a summary change). The screen also has `SynchronizeFormulas` (l.9799, l.17394), which has **no API route**. |
| Items — misc | `GetClosestSiteId` | no | — | not needed |
| Users | `Get`, `{id}/Get`, `Create`, `{id}/Update`, `{id}/Delete`, `Import` | get, create, delete | `test-users` (dev role tests, ADR-0018), `principals` | user update / import: not needed for configuration (customer data) |
| Groups | `Get`, `{id}/Get`, `Create`, `{id}/Update`, `{id}/Delete`, `Import` | get, create, update | `principals --create`, group membership of test users | delete: none (deliberate) |
| Depts | `Get`, `{id}/Get`, `Create`, `{id}/Update`, `{id}/Delete`, `Import` | no | — | `${principal:x}` accepts `Dept,<id>`, but no tool reads or creates depts, so a design that uses depts has no `principals` support |
| Binaries | `{guid}/Get`, `getstream`, `upload`, `{guid}/upload` | no | — | Attachments in records are out of configuration scope. The site image is configuration and is not covered. |
| Extensions | `Get`, `{id}/Get`, `Create`, `{id}/Update`, `{id}/Delete` | no | — | tenant-level extensions (e.g. extended SQL, HTML, fields): not covered; KB research needed first |
| Extended | `Sql` | no | — | runs a registered extended SQL; out of scope (needs a security review) |
| OutgoingMails | `{reference}/{id}/{controller}/Send` | no | — | sending mail from tests: not wanted (side effects, ADR-0012) |
| Sessions | `Get`, `Set`, `Delete` | no | — | not needed |
| BackgroundTasks | `RebuildSearchIndexes` ×2 | no | — | operations (P6) only |
| Utility, Demo | `GetLicenseInfo`, `Register` | no | — | not needed |

**Outside the API (screen or server files only).** Tenant settings (`TenantSettings`), background server scripts, contract settings and `Parameters/*.json` (e.g. `General.json`). The framework does not manage them. They belong to the customer's operations and are recorded as open questions only where a design depends on them (e.g. D33: the `General.json` maximum).

## D. Open questions (inputs to the plan, not assumed)

1. Does `updatesitesettings` (partial update) build the Links table and the site cache the way a screen save does? If it does, this would close D40 (C) / TD-50.
2. Does a changed `Formulas[]` entry recompute the stored values of existing records? The source has a screen-only `SynchronizeFormulas` action (`SiteUtilities.cs` l.9799 / l.17394) and no API route for it. That suggests existing records are not recomputed until a person runs it on the screen. This is source-derived and needs a probe.
3. Do view-level `Depts/Groups/Users` restrict who sees the view? Are user / dept ids inside `ColumnFilterHash` (e.g. `Owner`, `Manager` filters) stored as ids?
4. Which of the scalar keys does `updatesite` store exactly as sent (no clamping like `General.json`), and which defaults are dropped (D8)?
5. Extensions API: what is an "extension" in 1.5.2 (tenant-wide fields, SQL, HTML?), and does any customer app rely on it?
