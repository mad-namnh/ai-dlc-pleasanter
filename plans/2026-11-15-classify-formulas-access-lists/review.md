# Review — classify formulas and access lists

## Round 1 (pls-x-reviewer, opus, high) — accept with fixes; no Critical/High

- **F1 Medium:** `startswith("settings.Formulas")` also caught `FormulasGetErrorDetails` → anchored `settings\.Formulas(\[|$)`; StatusControls anchored the same way; test.
- **F2 Medium:** names with `]` (views / exports keyed by Name) missed → rules anchored on the end of the path (`\[.+\]\.(Groups|Users|Depts)`), Processes rule too; test with `[Admin] list`.
- **F3 Low:** tests now also drive `flat_diff` with real shapes (FormulaSet object, Name-keyed views, look-alike keys).
- **F4 Low:** formula message reworded (reordered / enabled; recomputed values as data or 同期; nothing to convert never for production).
- **F5 Low:** inventory rows marked fixed by WS2.
- **F6 Low:** dead `Columns[x].Formula` alternative removed (DefaultInput kept); the G2/G4 permission-matrix listing of WS2.2 is deferred (not part of classify) — noted in the parent plan's WS2 when it is next touched.
- **F7 Low (disposition):** a formula attribute Pleasanter drops when false (`NotUseDisplayName`, `IsDisplayError`, `Disabled` — FormulaSet.GetRecordingData, source-derived) kept as `false` in git would now show as a data-impacting difference: fails safe (refusal), not observed; canonical-defaults gets such rules only from a probe (D8) — WS3 (formula probes).
