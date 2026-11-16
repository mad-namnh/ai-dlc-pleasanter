# Plan — first probes on ADR-0027 (settings coverage WS3b notifications, WS3c-1/2/3)

- **Tier:** Standard (probe definitions, KB rows "not verified — no run yet"); the two small kb-verify changes are reviewed with them.
- **Origin:** Nam 2026-11-17, "cu lam tuan tu het khong can hoi" / "cu lam tiep khong can hoi"; ADR-0027 accepted 2026-11-16 ("3B").
- **Probes:** D48 notification / reminder shapes (all disabled, guarded, site deleted); D49 formula change on existing records (WS3c-2); D50 a view's Groups (WS3c-3, role `staff`); D51 updatesitesettings Process upsert (WS3c-1 / ADR-0027 open question). Values from Pleasanter_1.5.2.0 source (Notification.cs, Reminder.cs, Formula.cs).
- **Code:** kb-verify op `siteConfig` (read-only, main site, after a settings step); `siteConfig` paths take list selectors (`Columns[ColumnName=NumA]`) and `$admin_uid` / `$group_<role>`; `expect_stored` takes those variables too.
- **Next (Nam):** `pls principals --env dev` (role `staff` bound) and test users if not done, mail `sink` or `disabled` on dev, then `pls kb-verify --env dev`; the curator records the results.
- **Acceptance:** (1) probes pass `check_probe` and load with the KB; (2) KB rows say not verified, contained, not covered; (3) new tests fail on the parent; suites green; (4) review no open Critical / High.
