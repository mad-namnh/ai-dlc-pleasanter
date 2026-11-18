# Evidence — screen checks on the deployed app site (MADLAB dev 1.5.2.0, 2026-11-15, Nam; account not stated in these messages)

Site: trial `pls-trial-store-promo`, `request_lines` (dev id 44972), master `items` (44970, 150 records loaded by `pls migrate`). Git settings of `ClassB`: `ChoicesText` `[{"SiteId": ${site:items}, "Lookups": [{"From": "NumA", "To": "NumB"}]}]`, `AutoPostBack: true`, `ValidateRequired`; top-level `Links` entry ClassB → items. Deployed by `pls apply` (release R-20261115-10-dev, `updatesite`), round trip 0 differences (stored settings = git).

Nam's reports (chat, verbatim; English gloss):
1. "dropdown 品目 khong hien thi data gi ca" — after the deploy, the 品目 drop-down listed nothing.
2. "[[44970]] thi hien thi dc 品目、 [{"SiteId": 44970, "Lookups": [{"From": "NumA", "To": "NumB"}]}] thi khong hien thi dc" — with `[[44970]]` in 選択肢一覧 the drop-down listed 品目; with the JSON form it did not.
3. "toi kiem tra qua UI roi, setting hoan toan khong co van de, toi bo check 自動postback -> save, roi lai check 自動 postback va Save, 品目 da hien thi duoc data" — settings checked on the screen, no problem; 自動ポストバック unchecked → saved, checked again → saved: the drop-down then listed 品目 (JSON form).
4. "0-17: phai set 自動postback cho 数値 thi 金額 moi tu dong hien thi ket qua tinh toan" — 金額 (formula NumC = NumB × NumA) shows the computed result on the screen only when 自動ポストバック is set on the 数量 column (NumA) too.
5. "0-16: luu lai thi van dung" — after save, the values are still right. "(and reopen)" comes from the trial's check definition O-16 (`pls-trial-store-promo/design/decisions/DES-004-lookup-and-store-check.md`: "value stored after save and reopen … P4 screen check as 店長"), not from these words; the account used was not stated.
- Not stated explicitly: that choosing 品目 filled 単価 (O-15); implied by 4 (金額 computed from the looked-up 単価) — asked to confirm.

Source (tag Pleasanter_1.5.2.0, read 2026-11-15; read-only clone):
- `Libraries/Settings/SiteSettings.cs` l.4790–4835: a column with a JSON-format link (`Links.JsonFormat == true`) builds its choices through `Link.SetChoiceHash`; other links through `LinkHash` (l.4725–4770, built from links with `JsonFormat != true`).
- `Libraries/Settings/Link.cs` l.280–315: for a site link, choices come from `ss.Destinations.Get(SiteId)`; when it is null nothing is added (Destinations are loaded there only when searching).
- `Libraries/Settings/SiteSettings.cs` l.502–520: `Destinations` from `SiteInfo.Links` (the Links table) and `SiteInfo.Sites`.
- `Models/Sites/SiteModel.cs` l.1440–1446: a site update on the screen deletes and re-inserts the Links-table rows from `SiteSettings.Links` (JSON links included).
- Not read: whether the API `updatesite` path runs the same Links-table rewrite and `SiteInfo.Refresh`.

Later answers (Nam, 2026-11-15, chat, verbatim "1. co, 3. chinh toi bat 自動ポストバック trên 数量, day la setting dung nhe, 2 chua ro"):
6. O-15: choosing 品目 filled 単価 — "co" (yes).
7. 自動ポストバック on 数量 (NumA) was set by Nam on the screen; he states it is the right setting (not yet in git — the trial must add it).
8. Whether a later `updatesite` deploy empties the JSON-link drop-down again: not known.
- The account for reports 1–5 and 6 was not stated in these messages (the earlier checks on the probe sites were made as administrator, Nam "use admin").
- Correction to "Not read" above (review 2026-11-15, M1, source read by the reviewer): the API path `SiteUtilities.UpdateByApi` (l.2078 → `siteModel.Update` l.2140) and the screen path (`SiteUtilities.Update` l.1132 → l.1181) both reach `SiteModel.Update` (l.1273) → `UpdateRelatedRecords` (l.1315; Links-table rewrite l.1440–1446) and `SiteInfo.Refresh` (l.1320). What `SiteSettings.Links` holds at that point on each path was not read. So the source read does not explain why the screen save helped.

Answers to review round 2 (Nam, 2026-11-15, chat, verbatim "1. co save, sau save thi danh sach xuat hien. 2.cot 品目, thu lai mot lan deploy updatesite nua"):
9. The `[[44970]]` test was saved on the screen; after that save the list appeared.
10. 自動ポストバック was unchecked/checked (with the saves of report 3) on the 品目 column (`ClassB`).
11. Nam will repeat one `updatesite` deploy to see what a re-deploy does and what screen action brings the list back. Not yet answered: whether restoring the JSON form after the `[[44970]]` test was a separate save that still listed nothing.
