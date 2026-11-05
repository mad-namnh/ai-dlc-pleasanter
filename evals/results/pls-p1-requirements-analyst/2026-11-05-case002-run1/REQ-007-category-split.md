# REQ-007 — カテゴリ offers 契約 and 請求 instead of 契約・請求

- **Status:** awaiting G1
- **Source:** `sources/2026-11-05-category-billing-worktime.md`, item 1 (カテゴリの見直し)
- **Type (EARS):** ubiquitous

## Requirement

The 問い合わせ管理 site shall offer 操作方法, 不具合, 契約, 請求, 機能要望 and その他, in this order, as the choices of **カテゴリ**.

## Acceptance criteria

1. The edit screen and the list filter of カテゴリ show 操作方法, 不具合, 契約, 請求, 機能要望, その他 in this order (order `[assumed]`, Q8).
2. An inquiry can be created and updated with カテゴリ = 契約 and with カテゴリ = 請求 (API create/update succeeds; `get` returns the value).
3. 契約・請求 is not offered as a choice when a new inquiry is created (`[assumed]`, Q8).
4. Changing the choice list does not by itself change any stored カテゴリ value: an inquiry that held 契約・請求 before the release still returns 契約・請求 through `get` until it is reclassified (REQ-008). *(Pleasanter keeps removed choices on records as orphan values — KB D12.)*

## Notes (for P2)

- Current column: `ClassD` (カテゴリ), choices 操作方法 / 不具合 / 契約・請求 / 機能要望 / その他. No view, notification, reminder or aggregation of `inquiries` filters on カテゴリ; it appears in `GridColumns`, `FilterColumns`, `LinkColumns` and in the AI prompt input (impact analysis in `index.md`).
- Removing a choice that records use is data-impacting (D11, D12): sequence the choice change with REQ-008.
