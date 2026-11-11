# SiteSettings schema facts (verified on 1.5.2)

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
| Issues view | `Overdue: true` (D24); `NearCompletionTime: true` is source-derived only (D33, below); built-in `StartTime` / `CompletionTime`; editor key `IssueId` (Results: `ResultId`) |
| Process data change | `{Type: "InputDate", ColumnName, BaseDateTime: "CurrentDate"}` — `CurrentDate` is the default and is dropped on save (D8) |
| Issues defaults dropped on save (D8) | `Columns[CompletionTime].ValidateRequired: true` and `Columns[Status].DefaultInput: "100"` are defaults — do not keep them in git (equipment demo R-E01) |

## Source-derived, not verified on a server

Everything in this section was read in the Pleasanter source (GitHub Implem/Implem.Pleasanter, tag `Pleasanter_1.5.2.0`, read 2026-11-11) and has **not** been observed on a server. Treat it as an assumption until an entry in `probes/index.json` lists the target version.

| Setting | Shape (source: Pleasanter_1.5.2.0, not verified on a server) |
|---|---|
| Issues view `NearCompletionTime` (D33) | View `{…, NearCompletionTime: true}` (`bool?`). Filter on `CompletionTime` from `today − NearCompletionTimeBeforeDays` to the end of `today + NearCompletionTimeAfterDays`; no Status condition (completed records stay). Probe `D33-near-completion-range` pending |
| Site `NearCompletionTimeBeforeDays`, `NearCompletionTimeAfterDays` (D33) | top-level `SiteSettings` numbers (`decimal?`). Empty = `General.json` value (7 / 7 as shipped); stored only when different (D8 pattern). `General.json` as shipped: Min 0, Max 30 for both. **Open:** whether a value above Max (e.g. 90) sent through `updatesite` is stored and used, or clamped/refused; installations can change `General.json` |
| `Aggregations[]` (grid aggregation) | `{Id (long), GroupBy (string, column name), Type, Target (string, column name)}`; `Type` 0 Count, 1 Total, 2 Average. Computed results (`Data`) are not serialized |
| `Reminders[]` | `{Id, ReminderType, Subject, Body, Line, From, To, Token, Column, StartDateTime, Type (repeat type), Range, SendCompletedInPast, NotSendIfNotApplicable, NotSendHyperLink, ExcludeOverdue, Condition (view Id), Disabled}`. `ReminderType`: 1 Mail, 2 Slack, 3 ChatWork, 4 Line, 5 LineGroup, 6 Teams, 7 RocketChat, 8 InCircle, 9 LineWorks. Probe sites never carry reminders (kb-verify refuses them), so this shape will not be probed by `kb-verify` |
| Reminder `To` tokens | `[<ColumnName>]` (e.g. `[ClassD]`, `[Manager]`) expanded per record; `[Group<id>]` → the group's members, `[User<id>]`, `[Dept<id>]` (`Libraries/Mails/Addresses.cs`). The ids are environment-specific: `pls` stores them as `[${principal:x}]` in git and writes the environment's id back on pack (`tools/pls/pls_address_principals.py`; same idea as D15) |
