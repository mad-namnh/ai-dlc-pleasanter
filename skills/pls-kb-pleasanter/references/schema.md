# SiteSettings schema facts (verified on 1.5.2)

Evidence: spike round 1 (`spike/round-trip/report-20261105.md`) and slices #1–#3 (`docs/slices/slice-01-report.md` … `slice-03-report.md`), MADLAB dev 1.5.2, unless a row names its own D-entry, probe or source; rows marked source-derived are not verified on a server.

JSON property names are the UI field ids **without the `Process`/`Column` prefix** (`ProcessDisplayName` → `DisplayName`). Unknown properties are silently dropped on save; default-valued properties are omitted (D8).

## Columns (`SiteSettings.Columns[]`)

Only non-default attributes are stored, keyed by `ColumnName` (`ClassA`…, `NumA`…, `DateA`…, `DescriptionA`…, `CheckA`…, `AttachmentsA`…, plus `Title`, `Body`, `Status`, `Owner`, `Manager`).

| Attribute | Example |
|---|---|
| `LabelText` | `"督促日時"` |
| `ChoicesText` | lines; status lines are `value,label,short,css-class` e.g. `150,督促済,督,status-inprogress`; `[[siteId]]` links choices to another site; `[[Users*]]` = choose a Pleasanter user, stored as the user id string (D28) |
| `ValidateRequired` | `true` |
| `EditorReadOnly` | `true` |
| `EditorFormat` | `"Ymdhm"` (date-time) |
| `Unit`, `Description` | free text |

Editor layout: `EditorColumnHash.General` (ordered list). Grid: `GridColumns`. Filters shown on the grid: `FilterColumns`.

## Processes (`SiteSettings.Processes[]`)

| Property | Values |
|---|---|
| `Id`, `Name`, `DisplayName` | `Name` is the stable key used by tests and traceability |
| `ScreenType` | `10` create, `20` edit (**default 20 — dropped on save**) |
| `CurrentStatus`, `ChangedStatus` | status value, `-1` = any |
| `ExecutionType` | `0` added button (default), `10` on create/update, `20` both |
| `ActionType` | `0` save (default), `10` postback, `90` none |
| `ValidationType` | `0` merge (default), `10` replace, `90` none |
| `ConfirmationMessage`, `SuccessMessage`, `ErrorMessage`, `Description`, `Tooltip` | text |
| `View.ColumnFilterHash` | **display condition**, e.g. `{"Status": "[\"100\",\"200\"]", "ClassE": "[\"高\"]"}` |
| `DataChanges[]` | `{Id, Type, ColumnName, Value?, BaseDateTime?, …}` |
| `Notifications[]` | `{Id, Type (1 = mail), Address ("[Manager]"), Subject, Body}` — placeholders like `[ClassA]` |
| `Groups[]`, `Users[]`, `Depts[]` | process access control — principal IDs (D20); `pls` stores `${principal:x}` |
| `ValidateInputs[]`, `AutoNumbering*` | exist; not yet exercised |

`DataChanges[].Type`: `CopyValue`, `CopyDisplayValue`, `InputValue`, `InputValueFormula`, `InputDate`, `InputDateTime`, `InputDept`, `InputUser`.
`BaseDateTime`: `CurrentDate`, `CurrentTime`, `UpdatedTime`, or a column name.

## Views (`SiteSettings.Views[]`)

`{Id, Name, ColumnFilterHash, ColumnSorterHash, DefaultMode?, …}` — multi-value filters are JSON strings: `"[\"100\", \"150\"]"`. Site notifications can reference a view as their condition (`BeforeCondition`/`AfterCondition` = view Id).

## Client code (`SiteSettings.Scripts[]`, `Styles[]`, `Htmls[]`) — D29

`{Id, Title, Body, All?, New?, Edit?, Index?, Disabled?}`; `Htmls` also `PositionType` (1000, 1010 seen). Unpacked to `scripts/`, `styles/`, `htmls/` with `_index.json`.

## Dashboards (`SiteSettings.DashboardParts[]`) — D30

`{Id, Title, Type, X, Y, Width, Height, SiteId, …}`. `Type` 0 quick access (`QuickAccessSites` JSON text), 1 timeline (`TimeLineSites`, `TimeLineTitle`, `TimeLineBody`, `TimeLineDisplayType`, `TimeLineItemCount`, **`View`**), 3 HTML (`HtmlContent`), 4 calendar (`CalendarSites`, `CalendarSitesData[]`, `CalendarType`, `CalendarTimePeriod`, `CalendarFromTo`, **`View`**), 5 kanban (`KambanSites`, `KambanGroupByX/Y`, `KambanAggregateType`, `KambanValue`, **`View`**).

## Server scripts (`SiteSettings.ServerScripts[]`)

`{Id, Name, Title, Shared?, BeforeCreate?, BeforeUpdate?, …, Body}`. Shared scripts are prepended to the others — see D7 in `behaviours.md`.

## Summaries, links, views for Issues (verified 2026-11-05, PRB-001)

| Setting | Shape |
|---|---|
| Link (child → parent) | child `Columns[ClassX].ChoicesText = "[[parentSiteId]]"` + `Links: [{ColumnName: "ClassX", SiteId: parentSiteId}]`; record value = parent record Id as string |
| Summary (on the child) | `{Id, SiteId: parent, DestinationReferenceType, DestinationColumn, LinkColumn, Type: Count/Total, SourceColumn?, SourceCondition?: childViewId, SetZeroWhenOutOfCondition?}` (D16, D23) |
| Issues view | `Overdue: true` (D24); `NearCompletionTime: true` (D33); built-in `StartTime` / `CompletionTime`; editor key `IssueId` (Results: `ResultId`) |
| Process data change | `{Type: "InputDate", ColumnName, BaseDateTime: "CurrentDate"}` — `CurrentDate` is the default and is dropped on save (D8) |
| Issues defaults dropped on save (D8) | `Columns[CompletionTime].ValidateRequired: true` and `Columns[Status].DefaultInput: "100"` are defaults — do not keep them in git (equipment demo R-E01) |
| Issues view `NearCompletionTime` (D33, verified 1.5.2 by probe `D33-near-completion-range`, 2026-11-12) | View `{…, NearCompletionTime: true}`, stored as given; also accepted as API `View`. Lists records whose `CompletionTime` is from `today − NearCompletionTimeBeforeDays` to `today + NearCompletionTimeAfterDays` inclusive. Source-derived only, not exercised: no Status condition (completed records stay); the negative filter (`not between`) |
| Site `NearCompletionTimeBeforeDays`, `NearCompletionTimeAfterDays` (D33, verified 1.5.2) | top-level `SiteSettings` numbers; `0` and `90` sent through `updatesite` were stored as `0.0` and `90.0`, and 90 was used by the view filter — the `General.json` Max (30 as shipped) did not limit it. Source-derived only, not exercised: empty = `General.json` value (7 / 7 as shipped), stored only when different (D8 pattern). **Open:** a customer installation may change `General.json` |

## Source-derived, not verified on a server

Everything in this section was read in the Pleasanter source (GitHub Implem/Implem.Pleasanter, tag `Pleasanter_1.5.2.0`, read 2026-11-11) and has **not** been observed on a server, except where a row names round-trip evidence. Treat the rest as an assumption until an entry in `probes/index.json` lists the target version.

| Setting | Shape (source: Pleasanter_1.5.2.0, not verified on a server unless the row says **Verified**) |
|---|---|
| `Aggregations[]` (grid aggregation) | **Verified:** the top-level key round-trips (slices #1–#3, 1.5.2; `tools/pls/pls_scope.py` `VERIFIED_KEYS`), with `GroupBy: "Status"`, `Type: 0`. **Source-derived, not verified:** the full field list `{Id (long), GroupBy (string, column name), Type, Target (string, column name)}`, `Type` 1 Total and 2 Average; computed results (`Data`) are not serialized. No probe yet: a `Type: 1` probe is possible with `expect_stored` only (its result is not visible through the API) and is not written (open item) |
| `Reminders[]` | **Verified:** the top-level key round-trips (slices #1–#3, 1.5.2; `VERIFIED_KEYS`), seen in a canonical export on MADLAB dev with `Type: 10`, `ReminderType: 1`, `Condition`, `Range`, `To: "[Owner]"`. **Source-derived, not verified:** the full field list `{Id, ReminderType, Subject, Body, Line, From, To, Token, Column, StartDateTime, Type (repeat type), Range, SendCompletedInPast, NotSendIfNotApplicable, NotSendHyperLink, ExcludeOverdue, Condition (view Id), Disabled}` and `ReminderType` 2 Slack, 3 ChatWork, 4 Line, 5 LineGroup, 6 Teams, 7 RocketChat, 8 InCircle, 9 LineWorks (1 Mail is the value seen). No probe: reminders cannot be probed by `kb-verify` (probe sites refuse mail elements) |
| Reminder `To` tokens | **Verified:** a column token (`[Owner]`) round-trips (above). **Source-derived, not verified:** other `[<ColumnName>]` tokens (e.g. `[ClassD]`, `[Manager]`) expanded per record; `[Group<id>]` → the group's members, `[User<id>]`, `[Dept<id>]` (`Libraries/Mails/Addresses.cs`). The ids are environment-specific: `pls` stores them as `[${principal:x}]` in git and writes the environment's id back on pack (`tools/pls/pls_address_principals.py`; same idea as D15) |
