# Evidence — kb-verify on MADLAB dev, 2026-11-17 (run by Nam)

Source: `ops/kb-verify/2026-11-17-dev.{md,json}` of the trial project (Pleasanter 1.5.2.0, build 201520, schema 1.017). Result 20/24 entries verified (25/29 probes pass). Only probe-site data appears below (zz_kbprobe sites, ids of the probe folder).

- **D48 notification-and-reminder-shapes — pass.** save 200; read back as sent: Notifications[1] Disabled true, AfterCreate false, Address "zz-to@example.invalid, [Owner]", MonitorChangesColumns ["NumA"]; Types 2, 3, 6, 9, 10; Notifications[5] MethodType 2, MediaType "application/json"; Reminders[1] ReminderType 1, Disabled true, NotSendIfNotApplicable true, Column "DateA". Teardown 200, site deleted.
- **D49 formula-change-existing-records — observed.** NumB × NumA: create → NumC 3000; settings step (NumB + NumA) 200, read back OperatorType 1; the existing record still NumC 3000 (not recomputed by the settings save); after an update of NumA to 4 → NumC 1004 (the new formula applies on update).
- **D50 view-groups-storage — pass.** Views[1].Groups stored [383] (the group id of role accounting, as sent). Site deleted.
- **D51 updatesitesettings-process-upsert — pass.** settings_partial 200; Processes[1].Name "zz-p1-renamed", Processes[2].Name "zz-p2", Columns[NumA].LabelText "zz-a" kept.
- Failing as before: D40 link-lookup-copy (NumB 0 on API create / update), D41a formula-after-lookup (NumB 0, NumC 0), D46 (DashboardPartsAsynchronousLoading not stored).
