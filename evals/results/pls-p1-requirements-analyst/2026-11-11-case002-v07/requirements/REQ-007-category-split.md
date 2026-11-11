# REQ-007 — カテゴリ offers 契約 and 請求 instead of 契約・請求

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-improvement-request.md` — item 1 (「契約・請求」…「契約」と「請求」に分けたい)
- **Type (EARS):** ubiquitous

## Requirement

The 問い合わせ site shall offer 操作方法, 不具合, 契約, 請求, 機能要望 and その他, in this order, as the choices of カテゴリ.

## Acceptance criteria

1. The edit screen and the list filter of カテゴリ show 操作方法, 不具合, 契約, 請求, 機能要望, その他 in this order; 契約・請求 is not offered for new selection.
2. An inquiry can be created and updated with カテゴリ = 契約 and with カテゴリ = 請求 (API create/update succeeds, `get` returns the value).
3. Inquiries that are not in 契約・請求 keep their カテゴリ value unchanged after the release.

## Notes

- Position (契約, 請求 in place of 契約・請求) is `[assumed]` — Q8.
- What counts as 契約 and what as 請求 is not defined by the customer — Q9 `[assumed]`. Users and the AI first response (REQ-009) both need it.
- Existing records holding 契約・請求: removing the choice keeps the stored value (KB D12, D11) — those records are handled by REQ-008 (Q10, Q11).
- For P2: the column is 問い合わせ ClassD; ClassF (AI: 推定カテゴリ) has the same list (REQ-009).
