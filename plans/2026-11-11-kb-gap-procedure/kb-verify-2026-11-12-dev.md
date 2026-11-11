<!-- Copied 2026-11-12 from pls-demo-contracts/ops/kb-verify/2026-11-12-dev.md (trial project, probe sites only, no customer data) as evidence for KB 0.22 / D33 and the probe_runs of 2026-11-12. -->
# KB verification — dev — 2026-11-12

- **Pleasanter:** 1.5.2.0 (build 201520, schema 1.017)
- **Result:** 8/8 entries verified (10/10 probes pass)

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

| Entry | Probe | Status | Detail |
|---|---|---|---|
| D8 | D08-canonical-defaults | pass | ok save → HTTP 200 (expected 200); ok stored Columns[ColumnName=CompletionTime].ValidateRequired = null; ok stored Columns[ColumnName=Status].DefaultInput = null; ok stored Columns[ColumnName=Status].ChoicesText = "100,未処理,未,status-inprogress\n900,完了,完,status-closed"; ok stored EditorColumnHash.Gene |
| D10 | D10-display-condition-enforced | pass | ok save → HTTP 200 (expected 200); exec close(Id 1) → HTTP 200; exec close(Id 1) → HTTP 400 |
| D21 | D21-process-view-without-filter | pass | ok save → HTTP 200 (expected 200); ok stored Processes[Name=nofilter].View.Id = 0; exec nofilter(Id 1) → HTTP 200; teardown → HTTP 200 |
| D21 | D21-process-without-condition | pass | ok save → HTTP 200 (expected 200); exec noview(Id 1) → HTTP 500; exec withview(Id 2) → HTTP 200; teardown → HTTP 200 |
| D24 | D24-overdue-view | pass | ok save → HTTP 200 (expected 200); server date 2026-11-12; exec close(Id 1) → HTTP 200; exec close(Id 1) → HTTP 200 |
| D27 | D27-required-is-screen-only | pass | ok save → HTTP 200 (expected 200); ok stored Columns[ColumnName=ClassA].ValidateRequired = true |
| D28 | D28-user-choice | pass | ok save → HTTP 200 (expected 200); ok stored Columns[ColumnName=ClassA].ChoicesText = "[[Users*]]" |
| D30 | D30-dashboard-part-with-view | pass | ok save → HTTP 200 (expected 200) |
| D30 | D30-dashboard-part-without-view | pass | ok save → HTTP 500 (expected 500) |
| D33 | D33-near-completion-range | pass | ok save → HTTP 200 (expected 200); ok stored NearCompletionTimeBeforeDays = 0.0; ok stored NearCompletionTimeAfterDays = 90.0; ok stored Views[Id=1].NearCompletionTime = true; server date 2026-11-12 |

## Entries without a probe

D3, D4, D5, D7, D9, D11, D12, D13, D14, D15, D16, D17, D18, D19, D20, D22, D23, D25, D26, D29, D31, D32

A failing entry does not hold on this version: correct or split it by version (I9). `error` = the probe could not run (infrastructure), not a verdict on the entry; `inconclusive` = its control failed; `observed` = recorded behaviour without an expected outcome (read the detail).
