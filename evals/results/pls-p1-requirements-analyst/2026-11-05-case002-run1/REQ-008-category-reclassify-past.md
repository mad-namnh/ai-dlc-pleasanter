# REQ-008 — Past 契約・請求 inquiries are reclassified as 契約 or 請求

- **Status:** awaiting G1
- **Source:** `sources/2026-11-05-category-billing-worktime.md`, item 1 (「過去の問い合わせも、できれば新しいカテゴリで集計できるようにしたい」)
- **Type (EARS):** event-driven

## Requirement

When the reclassification of past inquiries is carried out, the system shall hold, for every inquiry whose カテゴリ was 契約・請求, the カテゴリ 契約 or 請求 given for that inquiry in the customer's classification list.

## Acceptance criteria

1. Before the reclassification, a backup of every inquiry with カテゴリ = 契約・請求 exists (API updates create no history version — KB D14).
2. After the reclassification, for every 問い合わせ番号 in the customer's list, `get` returns the カテゴリ given in the list (契約 or 請求).
3. After the reclassification, filtering カテゴリ = 契約・請求 on the 問い合わせ管理 list returns only inquiries that were not in the customer's list (expected: none, if the list is complete — `[assumed]`, Q9/Q10).
4. Inquiries with any other カテゴリ, and every column other than カテゴリ of the reclassified inquiries, are unchanged (compare with the backup). *(更新日時 / 更新者 change — `[assumed]` acceptable, Q22.)*
5. The reclassification sends no mail (サポート責任者 notification #1 and the escalation mail are not triggered) and does not run the AI first response (AIで一次対応する stays off). *(Engineering prerequisite EP-8 — to be confirmed on dev.)*
6. *(Not automatically testable: whether each inquiry is placed in the right category depends on the customer's list; the customer checks a sample — Q9.)*

## Notes

- Whether this is needed, for which period and by when is open: 「できれば」 in the mail — Q10. Method (customer list vs. other) — Q9. If the customer does not provide a list, this requirement cannot be met and is withdrawn at G1.
- Migration keyed on 問い合わせ番号 requires it to be unique (KB D18) — EP-7.
