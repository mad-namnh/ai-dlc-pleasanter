# Evidence — kb-verify 2026-11-16, MADLAB dev (sanitized)

- **Run by:** Nam (a person), `pls kb-verify --env dev` in a trial project repository (not this repository), 2026-11-16.
- **Server:** MADLAB dev, Pleasanter 1.5.2.0, build 201520, schema 1.017.
- **Report in the trial repository:** `ops/kb-verify/2026-11-16-dev.md` and `.json` (not copied: they hold dev site and record ids). Below: the results this repository relies on, with ids removed.

| Entry | Probe | Result | Keys read back as sent |
|---|---|---|---|
| D43 | `D43-site-scalars-editor` | pass | 20 of 20 |
| D44 | `D44-site-scalars-grid-filters` | pass | 27 of 27 |
| D45 | `D45-site-scalars-view-modes` | pass | 14 of 14 |
| D46 | `D46-site-scalars-formulas-code` | fail | 9 of 10 — log line: `NG stored DashboardPartsAsynchronousLoading = null` (sent `true`) |
| D47 | `D47-site-scalars-import-export-form-mail` | pass | 15 of 15 (incl. `AddressBook`, `MailToDefault`, `MailCcDefault`, `MailBccDefault`, example.invalid addresses) |

Each probe's `expect_stored` equals what it sent; the keys are those of the probe files at commit `2dca8a3`.

Other entries in the same run repeat earlier results: D8, D10, D21, D24, D27, D28, D30, D33, D36, D37, D39, D41, D42 pass; D40, D41a fail (`NumB` = 0 after an API create, as on 2026-11-14).

Source for the D46 key (Pleasanter_1.5.2.0, read-only clone): `Libraries/Settings/SiteSettings.cs` l.388 (a missing value is filled from `Parameters.Dashboard.AsynchronousLoadingDefault`), l.1254–1257 (recorded only when it differs from that parameter); shipped `App_Data/Parameters/Dashboard.json`: `"AsynchronousLoadingDefault": false`. The dev server's own parameter was not read.
