# REQ-007 — カテゴリ offers 契約 and 請求 instead of 契約・請求

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-improvement-request.md` — item 1 (「契約」と「請求」に分けたい)
- **Type (EARS):** ubiquitous

## Requirement

The 問い合わせ site shall offer 操作方法, 不具合, 契約, 請求, 機能要望 and その他 as the choices of カテゴリ.

## Acceptance criteria

1. The edit screen and the list filter of カテゴリ show 操作方法, 不具合, 契約, 請求, 機能要望, その他 in this order `[assumed]` (Q8).
2. An inquiry can be created and updated with カテゴリ = 契約 and with カテゴリ = 請求 (API create/update succeeds; `get` returns the value).
3. 契約・請求 is no longer offered as a choice for new entries `[assumed]` (Q9).
4. Inquiries that hold 契約・請求 before the change keep that value until they are reclassified (REQ-008); the release does not erase it (KB D12: removing a choice keeps stored values, so the old value stays on the record as an orphan option).

## Notes for P2

- Current column: カテゴリ (ClassD), choices `操作方法 / 不具合 / 契約・請求 / 機能要望 / その他`.
- Removing a choice that records use is data-impacting (KB D11, D12): classify the change accordingly and plan it together with REQ-008.
- Impact checked in `config/inquiries/`: views 1–3, the aggregation (by 状況), notification #1 (watches 状況 and 優先度) and reminder 1 do not filter on カテゴリ — no impact. カテゴリ is in the grid and filter columns, so the new choices appear there automatically. AI script `ai1` and AI: 推定カテゴリ use the same list → REQ-009.
