# Source notes — Pleasanter 1.5.2.0 (ADR-0023 step 3)

- **Source:** `https://github.com/Implem/Implem.Pleasanter`, tag `Pleasanter_1.5.2.0`, sparse read-only clone (2026-11-14). Nothing about any project was sent.
- Paths relative to `Implem.Pleasanter/`. Everything here is **source-derived, not verified on a server**.
- Starting point: a trial hand-over (gaps G-1…G-8, generic shapes only). Below, what that hand-over said plus what this read added.

## G-1 Record permissions given at creation (`PermissionForCreating`)

- `Libraries/Settings/SiteSettings.cs` l.282–283: `Dictionary<string, Permissions.Types> PermissionForCreating`, `PermissionForUpdating`. Recording (l.1374–1389) keeps only entries with value > 0. The screen setter (l.5484) builds the dictionary from `"<Name>,<Id>,<Value>"` strings with `Name` as key → stored form expected `{"Group": 15}` (enum `long`; serialised as a number is **not** read — the probe checks it).
- `Models/Permissions/PermissionUtilities.cs` `InsertStatements` (l.566): key `Dept` → creating user's dept; `Group` → every group of the creating user; `User` → the creating user; any other key → the column whose key starts with `<key>,` and is of type Dept / Group / User → the principal **stored in that column** (`SiteInfo.Group(...)` must exist).
- `Libraries/Settings/Column.cs`: `ChoicesText` `[[Groups]]` / `[[Groups*]]` → `Type = Group`.
- Not read: whether a user with site permission Create (2) only lists records on which they hold a record permission (grid query). The probe answers it.

## G-2 `Process.ValidateInputs` Required

- `Libraries/Settings/Process.cs`: `ValidationType` (`Merge` 0, `Replacement` 10, `None` 90), `ValidateInputs: SettingList<ValidateInput>`.
- Server side, `ValidateInputs` are read only in:
  - `Models/Issues/IssueValidators.cs` l.1355–1376 (and `ResultValidators.cs` l.1261): only `ServerRegexValidation`, only for a **non-empty** value, only when the process is found by `context.Forms.ControlId()` = `Process_<Id>` (a screen post);
  - `Libraries/Settings/View.cs` l.1894 `SetBulkProcessingFilter`: bulk processing filters out records with an empty Required column;
  - `Libraries/HtmlParts/HtmlProcess.cs` l.84: the list goes to the screen as JSON (client-side check).
- `Required` is therefore **not checked by the server** for a single record, and an API update with `ProcessId` (`IssueUtilities.UpdateByApi` l.4819, no `ControlId`) runs no `ValidateInputs` check at all. Expected: API process execution with the column empty → HTTP 200, status changed (like D27 for `ValidateRequired`).

## G-3 `items.Create` from a server script

- `Libraries/ServerScripts/ServerScriptUtilities.cs` `Create(context, id, model)` → `CreateContext(...)`: for a non-background script a new `Context` from the **same request** (same user); `PermissionHash` recomputed for that user.
- `Models/Issues/IssueUtilities.cs` `CreateByServerScript` (l.3699) → `IssueValidators.OnCreating(api: true, serverScript: true)` → `if (!context.CanCreate(ss) || issueModel.ReadOnly)` → error (403 / NotFound) → `Create` returns false, no record.
- Expected: the executing user needs **Create** on the target site; with Read only no record is created and `items.Create` returns false (the save of the parent record itself is not refused by this).
- Probe: not possible in `kb-verify` (ADR-0025 forbids `items` in a probe script) → manual probe by a person (Nam, 2026-11-14).

## G-4 Crosstab view

- `Libraries/Settings/View.cs` l.102–109: view fields `CrosstabGroupByX`, `CrosstabGroupByY`, `CrosstabColumns`, `CrosstabAggregateType`, `CrosstabValue`, `CrosstabTimePeriod` (strings), `CrosstabMonth` (`DateTime?`), `CrosstabNotShowZeroRows` (`bool?`); `Libraries/Settings/SiteSettings.cs`: `EnableCrosstab`, `NoDisplayCrosstabGraph`, `CrosstabGuide` (read 2026-11-14).
- `Libraries/Settings/SiteSettings.cs` l.3819–3840: `CrosstabAggregationTypeOptions` `Count`, `Total`, `Average`, `Max`, `Min`; `CrosstabTimePeriodOptions` `Yearly`, `Monthly`, `Weekly`, `Daily`.
- `App_Data/Definitions/Definition_ViewMode/Definition.json`: defaults — Issues: X `Status`, Y `Owner`, `Total`, value `RemainingWorkValue`, `Monthly`; Results: X `Status`, Y `Owner`, `Total`, value `NumA`, `Monthly`. `View.Get…` returns the default when the stored value is empty (l.283–332).
- The totals are computed for the screen (`Libraries/HtmlParts/HtmlCrosstab.cs`) and a crosstab export; the items API `get` returns records, not totals. Totals are not checkable by an API probe.

## G-5 Lookups through a link

- `Libraries/Settings/SiteSettings.cs` `SetLinks` (l.4581): a link comes from the column's `ChoicesText` — `[[<siteId>]]` lines or a JSON list of `Link` (then `JsonFormat`); recorded in `SiteSettings.Links` (l.1136).
- `SetLinks(context)` runs whenever site settings are loaded (`Libraries/Settings/SiteSettingsUtilities.cs` l.201, 248, 306, …) and first **removes** every link of the column, then rebuilds it from `ChoicesText`. A `[[<siteId>]]` line gives a link **without** lookups. So `Lookups` must be written inside `ChoicesText` in the JSON form, e.g. `[{"SiteId": <master>, "Lookups": [{"From": "NumA", "To": "NumB"}]}]`; lookups only in the top-level `Links` would be dropped on load (inferred from the code, not observed).
- `Models/Results/ResultModel.cs` `SetByLookups` (l.3258): runs only when the **link column itself** changed (`PropertyUpdated(link.ColumnName)`) or the form posts it. A later change in the master record is **not** copied into existing lines unless the line's link column is set again.
- `Libraries/Settings/Lookups.cs` l.55–66: `Overwrite` default (null) = overwrite; `Overwrite: false` = only into blank targets; the user must be able to **read** the master record (`Permissions.CanRead`).
- Order: constructor `SetByApi` → `SetByLookups` → lookup values applied through `SetByForm`, which ends with `SetByFormula` (l.2592) → a formula over a looked-up column is computed **after** the lookup.

## G-6 Formulas

- `Libraries/Settings/FormulaSet.cs`: `Id`, `CalculationMethod` (`Default` | `Extended`), `Target`, `Condition` (view id), `Formula`, `OutOfCondition`, `FormulaScript`, `FormulaScriptOutOfCondition`, `FormulaMapping`, `NotUseDisplayName`, `IsDisplayError`, `Disabled`.
- `Libraries/Settings/Formula.cs`: node `{ColumnName, RawValue, OperatorType, Children}`; `OperatorType` enum `NotSet` 0, `Addition` 1, `Subtraction` 2, `Multiplication` 3, `Division` 4 (serialised form not read). Evaluation: first pass applies `*` / `/` of a child onto the previous child, second pass adds/subtracts. `NumB × NumA` = `{"Children": [{"ColumnName": "NumB"}, {"ColumnName": "NumA", "OperatorType": 3}]}`.
- `ResultModel.SetByFormula` (l.3516): runs on create/update through API too (`SetByApi` path, l.3032); Default method writes the result with `SetNum`.

## G-7 Permission values

`Libraries/Security/Permissions.cs` `enum Types : long`: NotSet 0, Read 1, Create 2, Update 4, Delete 8, SendMail 16, Export 32, Import 64, ManageSite 128, ManagePermission 256, ManageTenant 1073741824, ManageService 2147483648 (hand-over; consistent with KB 511 = all site rights).

## Serialised enum forms (for `expect_stored`)

- `StatusControl.ControlConstraintsTypes` has `[JsonConverter(typeof(StringEnumConverter))]` → stored as text (`"ReadOnly"`); `Column` and `DataChange` enums too.
- `Formula.OperatorTypes` and `Permissions.Types` have no such attribute → numbers (Newtonsoft default), e.g. `3`, `15`.

## G-8 StatusControl and an API write of Status

- `Models/Issues/IssueModel.cs` constructor (l.745–812): `Get` → `SetByApi` → `SetByLookups` → `SetByStatusControls` — the status controls are evaluated on the status **after** the API data was applied.
- `SetByStatusControls` (l.3627): matching controls set `ReadOnly |= statusControl.ReadOnly` (whole record) and fill `StatusControlHash` (per column).
- `IssueValidators.OnUpdating` l.576: `!CanUpdate || issueModel.ReadOnly` → 403. Per-column `ReadOnly` of a status control is used only for the editor (`Column.StatusReadOnly`, `IssueUtilities` l.617, l.2302); the API column check (l.592) uses column access control, not status controls.
- Expected: a status control cannot stop an API update that changes Status — column `ReadOnly` is screen-only, and the whole-record `ReadOnly` is evaluated on the new status. Fallback: server script `BeforeUpdate` (D25) — whether a script can read the stored status is trial C-1 (AU1).
- Consequences of the same order, also expected: a record in a status with whole-record `ReadOnly` refuses an API update that keeps that status (403), but accepts one that moves it to another status; an API create or update **into** that status is refused (the model is read-only after `SetByApi`), while a process (applied after `OnUpdating`, `IssueUtilities` l.4886 ff.) can move a record into it.
