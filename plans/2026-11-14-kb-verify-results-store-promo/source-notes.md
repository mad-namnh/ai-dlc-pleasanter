# Source notes — why D40's lookup did not copy (Pleasanter 1.5.2.0, not verified)

- **Source:** `https://github.com/Implem/Implem.Pleasanter`, tag `Pleasanter_1.5.2.0`, sparse read-only clone (2026-11-14). Paths relative to `Implem.Pleasanter/`.
- **Observed (kb-verify, dev 1.5.2.0 build 201520):** line created through the items API with `ClassB` = master id; the lines site's `ClassB.ChoicesText` = `[{"SiteId": <master>, "Lookups": [{"From": "NumA", "To": "NumB"}]}]`; `NumB` read back **0** (master `NumA` 1000).

## Path read

- `Libraries/Settings/SiteSettings.cs` `SetLinks(context, column)` (l.4581): `ChoicesText` deserialised as `List<Link>` → each link `JsonFormat = true`, added to `ss.Links` (no permission or `SiteId > 0` check on this branch, unlike the `[[id]]` branch).
- `Models/Results/ResultModel.cs` constructor (l.560–590): `SetByApi` → `SetByLookups` when `resultApiModel != null`.
- `SetByLookups` (l.3258): links with lookups whose column was updated (`PropertyUpdated(ClassB)`) → `Lookups.LookupData(...)`; the result is applied with `SetByForm`.
- `Libraries/Settings/Lookups.cs` `LookupData` (l.19–): `currentSs = ss.Destinations.Get(link.SiteId)`. When `currentSs` is null and the link is not to Depts/Users/Groups, `canRead = false`; the lookup still returns `{"Results_NumB": ""}` (l.~68), which `SetByForm` applies → **NumB set empty → 0**. This matches the observation exactly.
- `ss.Destinations` comes from `SiteSettingsList(direction "Destinations")` (`SiteSettings.cs` l.502): the sites listed for this site in `SiteInfo.Links` — the **Links table**, not `ss.Links`.
- The Links table is rewritten on a site update: `SiteModel.Update` → `UpdateRelatedRecords` → `UpdateRelatedRecordsStatements` (`Models/Sites/SiteModel.cs` l.1422–1446): delete `SourceId = site`, insert one row per `SiteSettings.Links` destination — JSON links included. Then `SiteInfo.Refresh`.

## Hypotheses (not decided by reading)

1. **H1 — no Links-table row:** the row for lines → master is not written on the API `updatesite` path (e.g. `SiteSettings.Links` at that point does not yet contain the JSON link) → `Destinations` empty → lookup writes blank. Distinguishes: re-save the lines site's settings once in the UI (rewrites the Links rows), then create a line through the API again.
2. **H2 — API path differs from the screen:** something on the API create path (constructor branch, `PropertyUpdated`, form keys) keeps the lookup from finding the master. Distinguishes: create a line on the screen, choose the master → is `NumB` filled?
3. Both negative → the JSON form or the `Lookup` fields are wrong for 1.5.2.0.

Until one is confirmed, the KB records D40 as failed for this shape, with these hypotheses as an open question (I9; CLAUDE.md "Do not guess").
