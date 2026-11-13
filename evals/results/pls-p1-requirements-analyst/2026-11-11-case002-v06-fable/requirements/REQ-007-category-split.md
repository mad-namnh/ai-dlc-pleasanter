# REQ-007 — カテゴリ offers 契約 and 請求

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-category-accounting-worktime.md` (item 1)
- **Type (EARS):** ubiquitous

## Requirement

The 問い合わせ site shall offer 契約 and 請求 as two separate choices of カテゴリ.

## Acceptance criteria

1. The edit screen and the list filter of カテゴリ show 操作方法, 不具合, 契約, 請求, 機能要望, その他, in this order `[assumed]` (Q8: 契約 and 請求 take the place of 契約・請求).
2. An inquiry can be created and updated with カテゴリ = 契約, and with カテゴリ = 請求 (API create/update succeeds, `get` returns the value).
3. 契約・請求 is no longer offered for a new inquiry `[assumed]` (Q8).
4. The other choices (操作方法, 不具合, 機能要望, その他) and the inquiries that hold them are unchanged.

## Notes

- Existing inquiries that hold 契約・請求 are the subject of REQ-008; this requirement alone does not change any record.
- For P2: カテゴリ is `ClassD` on `inquiries`. Removing a choice keeps the stored value on the records, where it shows as an orphan option (KB D11, D12) — the change is data-impacting and must be ordered with REQ-008.
