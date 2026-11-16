# Log — proposed ADRs for probe steps and summary sync

- 2026-11-16 Settings coverage WS3c (probes) needs kb-verify capabilities not built (a second settings save, `updatesitesettings`, principal ids in probe settings) and Nam's decision 2 of 2026-11-15 (disabled notifications in probes) needs ADR text; WS4.1 is a new write path. All are stop point 1 → written as Proposed ADRs: 0027, 0028. Nothing built.
- Source: `Controllers/Api/ItemsController.cs` l.293 (SynchronizeSummaries), l.318 (updatesitesettings), Pleasanter_1.5.2.0; bodies not read (item models not in the clone).
- Tier: Light (Proposed text, no code); no review; Nam decides.
- Committed (see git log); REPORT SENT
