# SiteSettings schema facts (verified on 1.5.2)

JSON property names are the UI field ids **without the `Process`/`Column` prefix** (`ProcessDisplayName` → `DisplayName`). Unknown properties are silently dropped on save; default-valued properties are omitted (D8).

## Columns (`SiteSettings.Columns[]`)

Only non-default attributes are stored, keyed by `ColumnName` (`ClassA`…, `NumA`…, `DateA`…, `DescriptionA`…, `CheckA`…, `AttachmentsA`…, plus `Title`, `Body`, `Status`, `Owner`, `Manager`).

| Attribute | Example |
|---|---|
| `LabelText` | `"督促日時"` |
| `ChoicesText` | lines; status lines are `value,label,short,css-class` e.g. `150,督促済,督,status-inprogress`; `[[siteId]]` links choices to another site |
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

## Server scripts (`SiteSettings.ServerScripts[]`)

`{Id, Name, Title, Shared?, BeforeCreate?, BeforeUpdate?, …, Body}`. Shared scripts are prepended to the others — see D7 in `behaviours.md`.
