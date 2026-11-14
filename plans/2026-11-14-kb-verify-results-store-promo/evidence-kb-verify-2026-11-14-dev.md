# KB verification — dev — 2026-11-14

- **Pleasanter:** 1.5.2.0 (build 201520, schema 1.017)
- **Result:** 12/14 entries verified (18/20 probes pass)

| Entry | Result |
|---|---|
| D8 | pass |
| D10 | pass |
| D21 | pass |
| D24 | pass |
| D27 | pass |
| D28 | pass |
| D30 | pass |
| D33 | pass |
| D36 | pass |
| D37 | pass |
| D39 | pass |
| D40 | fail |
| D41 | fail |
| D42 | pass |

| Entry | Probe | Status | Detail |
|---|---|---|---|
| D8 | D08-canonical-defaults | pass | ok save → HTTP 200 (expected 200); ok stored Columns[ColumnName=CompletionTime].ValidateRequired = null; ok stored Columns[ColumnName=Status].DefaultInput = null; ok stored Columns[ColumnName=Status].ChoicesText = "100,未処理,未,status-inprogress\n900,完了,完,status-closed"; ok stored EditorColumnHash.Gene |
| D10 | D10-display-condition-enforced | pass | ok save → HTTP 200 (expected 200); exec close(Id 1) → HTTP 200; exec close(Id 1) → HTTP 400 |
| D21 | D21-process-view-without-filter | pass | ok save → HTTP 200 (expected 200); ok stored Processes[Name=nofilter].View.Id = 0; exec nofilter(Id 1) → HTTP 200; teardown → HTTP 200 |
| D21 | D21-process-without-condition | pass | ok save → HTTP 200 (expected 200); exec noview(Id 1) → HTTP 500; exec withview(Id 2) → HTTP 200; teardown → HTTP 200 |
| D24 | D24-overdue-view | pass | ok save → HTTP 200 (expected 200); server date 2026-11-14; exec close(Id 1) → HTTP 200; exec close(Id 1) → HTTP 200 |
| D27 | D27-required-is-screen-only | pass | ok save → HTTP 200 (expected 200); ok stored Columns[ColumnName=ClassA].ValidateRequired = true |
| D28 | D28-user-choice | pass | ok save → HTTP 200 (expected 200); ok stored Columns[ColumnName=ClassA].ChoicesText = "[[Users*]]" |
| D30 | D30-dashboard-part-with-view | pass | ok save → HTTP 200 (expected 200) |
| D30 | D30-dashboard-part-without-view | pass | ok save → HTTP 500 (expected 500) |
| D33 | D33-near-completion-range | pass | ok save → HTTP 200 (expected 200); ok stored NearCompletionTimeBeforeDays = 0.0; ok stored NearCompletionTimeAfterDays = 90.0; ok stored Views[Id=1].NearCompletionTime = true; server date 2026-11-14 |
| D36 | D36-permission-for-creating-child-site | pass | ok save → HTTP 200 (expected 200); ok save lines → HTTP 200 (expected 200); ok stored PermissionForCreating.Group = 15; teardown → HTTP 200; site 44939 deleted (deletesite, then getsite no longer finds it); teardown → HTTP 200; site 44938 deleted (deletesite, then getsite no longer finds it) |
| D36 | D36-permission-for-creating-group-column | pass | ok save → HTTP 200 (expected 200); ok stored PermissionForCreating.ClassD = 15; ok stored Columns[ColumnName=ClassD].ChoicesText = "[[Groups*]]"; teardown → HTTP 200; site 44944 deleted (deletesite, then getsite no longer finds it) |
| D36 | D36-permission-for-creating-group | pass | ok save → HTTP 200 (expected 200); ok stored PermissionForCreating.Group = 15; teardown → HTTP 200; site 44947 deleted (deletesite, then getsite no longer finds it) |
| D37 | D37-process-validate-inputs-required-api | pass | ok save → HTTP 200 (expected 200); ok stored Processes[Id=1].ValidateInputs.0.Required = true; exec sendback(Id 1) → HTTP 200 |
| D39 | D39-crosstab-view-settings | pass | ok save → HTTP 200 (expected 200); ok stored Views[Id=1].CrosstabGroupByX = "DateA"; ok stored Views[Id=1].CrosstabGroupByY = "ClassA"; ok stored Views[Id=2].CrosstabGroupByX = "DateA"; ok stored Views[Id=2].CrosstabGroupByY = "ClassA"; ok stored Views[Id=2].CrosstabAggregateType = "Average"; ok sto |
| D40 | D40-link-lookup-copy | fail | ok save → HTTP 200 (expected 200); ok save lines → HTTP 200 (expected 200); NG  NumHash.NumB = 0.0 (expected 1000); NG  NumHash.NumB = 0.0 (expected 1000) |
| D41 | D41-formula-after-lookup | fail | ok save → HTTP 200 (expected 200); ok save lines → HTTP 200 (expected 200); NG  NumHash.NumB = 0.0 (expected 1000); NG  NumHash.NumC = 0.0 (expected 3000) |
| D41 | D41-formula-multiply | pass | ok save → HTTP 200 (expected 200); ok stored Formulas[Id=1].Target = "NumC" |
| D42 | D42-status-control-column-readonly-api | pass | ok save → HTTP 200 (expected 200); ok stored StatusControls[Id=1].ColumnHash.Status = "ReadOnly" |
| D42 | D42-status-control-readonly-record | pass | ok save → HTTP 200 (expected 200); ok stored StatusControls[Id=1].ReadOnly = true; exec to200(Id 1) → HTTP 200 |

## Entries without a probe

D3, D4, D5, D7, D9, D11, D12, D13, D14, D15, D16, D17, D18, D19, D20, D22, D23, D25, D26, D29, D31, D32, D34, D35, D38

A failing entry does not hold on this version: correct or split it by version (I9). `error` = the probe could not run (infrastructure), not a verdict on the entry; `inconclusive` = its control failed; `observed` = recorded behaviour without an expected outcome (read the detail).
