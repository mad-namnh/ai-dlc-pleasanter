# REQ-014 — Total handling time per inquiry

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-category-accounting-worktime.md` (item 3: 「問い合わせごとに合計時間が分かると、月次の報告に使えます」)
- **Type (EARS):** ubiquitous

## Requirement

The 問い合わせ site shall show, for each inquiry, the total of 作業時間 of the 対応履歴 records linked to that inquiry.

## Acceptance criteria

1. An inquiry with 対応履歴 records of 30 分 and 45 分 shows a total of 75 分 (API `get` on the inquiry returns 75).
2. Adding a 対応履歴 record of 15 分 to that inquiry changes the total to 90; changing it to 20 changes the total to 95; deleting it changes the total back to 75.
3. A 対応履歴 record without 作業時間 adds 0 to the total.
4. The total counts 対応履歴 records in every 状況 (予定 and 完了) `[assumed]` (Q18).
5. The total is shown on the edit screen and in the list of the 問い合わせ site under the label 「合計対応時間」 with the unit 分, and cannot be edited by hand on the edit screen `[assumed]` (Q19).
6. 対応回数 keeps counting the 対応履歴 records of the inquiry as before.

## Notes

- No existing field holds this total: 問い合わせ has 対応回数 (number of 対応履歴 records), not their time. A new displayed value is needed; label, unit and place are Q19.
- Inquiries that already have 対応履歴 at the time of release: REQ-015.
- A monthly total or report screen is not requested as such; see Q21.
- For P2: KB D16 (Summary type Total on the child site; each child create/update/delete recomputes the parent's full total), D22 (the destination column must be in the editor layout), D17 (read-only on the screen does not stop API writes). New column on `inquiries` → slot ledger, grid, filter, export.
