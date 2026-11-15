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

## Screen observations by Nam (MADLAB dev 1.5.2.0, 2026-11-14, probe site lines 44954 / master 44953)

1. As left by kb-verify (ChoicesText written through `updatesite`): the ClassB drop-down listed the JSON text ("Lookup…") as plain choices — the link was **not** taken as a link.
2. Nam typed the same JSON form by hand in the column's 選択肢一覧 (multi-line, `[{"SiteId": 44953, "Lookups": [{"From": "NumA", "To": "NumB"}]}]`) and saved the site in the UI: the drop-down then listed the master record ("D40 master"), no error — the link works.
3. With (2), choosing the master on a new record did **not** fill NumB (master NumA 1200).
→ H1/H2 as stated do not explain (1); the difference between the API-written and the UI-written setting is not known yet (stored text not compared). (3) is open: lookup not applied on the screen either, cause unknown.
4. 2026-11-15, after F5 and a new record on 44954 with the UI-saved link: choosing the master still does **not** fill NumB.

## Second source read (2026-11-15, same tag, sparse clone in `../_agent-scratch/pls-src`)

- `Libraries/Settings/Lookup.cs`: fields `From`, `To`, `Type` (Value/DisplayName), `Overwrite`, `OverwriteForm`. `Data(..., ResultModel)` handles `Num` columns (`GetNum(column).ToLookup`) after `column.CanRead` on the master column — Num → Num is a supported shape.
- `Libraries/Settings/Lookups.cs` `LookupData` filters the lookups before copying:
  `(lookup.OverwriteForm == true && formData["ControlId"] == "Results_<link column>") || formData?.ContainsKey("Results_<To>") != true`.
  On the API create path `formData` is null (`ResultModel` constructor l.555–590) → the filter passes. On the screen the posted form is merged into `formData` (`ResultModel.cs` l.3228–3237); when the `To` column (NumB) is on the editor its field is posted → the lookup is filtered out unless `"OverwriteForm": true`.
- `SiteSettings.ReplaceFieldColumns` (l.6083–): when the link column is the control, the `To` columns of its lookups are re-rendered on the screen — the screen path exists; it depends on the filter above.
- `SiteSettings.SetLinks(context, column)` (l.4581): on the JSON branch `column.Link` stays false (only the `[[id]]` branch sets it); `ss.Links` gets the link. `SetLinks` is also run when site settings are loaded (`SiteSettingsUtilities.cs` l.201–462) and on the API column path (`SiteModel.UpsertColumnsByApi`, l.2574–2634); `createsite` with raw `SiteSettings` assigns them as sent (`SiteModel.cs` l.1784).

## Hypotheses after the second read (not verified)

- **H3 — screen: `To` column on the editor.** Observation 3/4 fit: NumB is in the lines editor, so the screen form carries `Results_NumB` and the lookup is skipped. Distinguishes: add `"OverwriteForm": true` to the lookup, save, F5, choose the master → NumB filled?
- **H1 — API: no Destinations row** stays the candidate for the API 0 (`formData` null, so H3 does not apply there). Not yet distinguished.
- Observation 1 (API-written ChoicesText shown as plain choices) is not explained by this read: `SetLinks` re-derives links from `ChoicesText` on load. The stored text of the API-created site was overwritten by Nam's UI edit; a new kb-verify run creates new probe sites whose stored settings can be compared.
5. 2026-11-15, with `"OverwriteForm": true` added (UI save, F5, new record, master chosen): NumB still **not** filled → H3 alone does not explain the screen.

## Third read (2026-11-15)

- The screen re-renders fields on a choice change only when the column has `AutoPostBack == true` (`HtmlFields.ControlCss`, l.243–254: css `control-auto-postback`); `AutoPostBack` defaults to false (`SiteSettings.cs` l.2160), set per column (`SiteSettings.cs` l.4427; UI 自動ポストバック). `ResultUtilities.FieldResponse` (l.2633–) then returns `ReplaceFieldColumns`, which include the lookup `To` columns when the link column is the control.
- **H4 (not verified):** without 自動ポストバック on ClassB, choosing the master sends nothing, so no lookup on the screen; on save the posted NumB makes the lookup skip (H3 filter; `OverwriteForm` needs ControlId = the link column, which a save does not carry). Distinguishes: ClassB 自動ポストバック on + `OverwriteForm: true`, choose the master → NumB filled?
6. 2026-11-15, ClassB 自動ポストバック on + `"OverwriteForm": true`: choosing the master fills NumB (1200) on the screen → H4 confirmed on the screen for this combination. Not yet separated: whether `OverwriteForm` is needed too; whether the value is saved. The API create (NumB 0) is a separate question (H1 open).
7. 2026-11-15, 自動ポストバック on, ChoicesText without `OverwriteForm`: choosing the master fills NumB (1200) — `OverwriteForm` is **not** needed on the screen. Saved value after save/reopen: not yet reported.
8. 2026-11-15, Nam (chat, verbatim "use admin"): the screen checks (observations 1–7) were made with the administrator account.
- Source detail (2026-11-15, clone at tag Pleasanter_1.5.2.0): `SiteSettings.cs` l.4585 `var links = column.ChoicesText.Deserialize<List<Link>>();` — the whole text is deserialised at once (inside `SetLinks`, l.4581).
