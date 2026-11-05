# REQ-014 — Each inquiry shows the total 作業時間 of its 対応履歴

- **Status:** awaiting G1
- **Source:** `sources/2026-11-05-category-billing-worktime.md`, item 3 (「対応履歴に対応時間を入れられるようにしてほしい」「問い合わせごとに合計時間が分かると、月次の報告に使えます」)
- **Type (EARS):** ubiquitous

## Requirement

The 問い合わせ管理 site shall show, for each inquiry, the sum of the **作業時間** of all 対応履歴 records linked to it as **合計作業時間** (分).

## Acceptance criteria

1. Recording time per 対応 uses the existing 対応履歴 column **作業時間** (unit 分) — no new column on 対応履歴 (`[assumed]`, Q16).
2. Inquiry with no 対応履歴 → 合計作業時間 = 0.
3. Create two 対応履歴 for one inquiry with 作業時間 30 and 45 → `get` on the inquiry returns 合計作業時間 = 75.
4. Update one of them to 60 → 105; delete it → 30; move it to another inquiry (change 問い合わせ) → both inquiries' totals are recomputed (KB D16: every child create/update/delete recomputes the full total).
5. A 対応履歴 with 作業時間 empty counts as 0 (KB D16).
6. 合計作業時間 is read-only on the edit screen. *(The API can still write it — KB D17; the next change to a linked 対応履歴 restores the correct value.)*
7. 合計作業時間 is shown on the edit screen and in the 問い合わせ管理 list (label, unit and list display `[assumed]`, Q17).

## Notes (for P2)

- `responses` already has a Summary (Count → `inquiries.NumA` 対応回数); this adds a Total of `responses.NumA` into a new Num slot on `inquiries` (slot to be allocated in the ledger at P2). Two Summaries on the same child/link are not in the KB — EP-6.
- Monthly reporting basis (by 受付日 vs. by 対応日時) — Q20; this requirement gives the all-time total per inquiry.
