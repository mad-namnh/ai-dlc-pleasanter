# REQ-014 — Total response time per inquiry

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-improvement-request.md` — item 3 (問い合わせごとに合計時間が分かると、月次の報告に使えます)
- **Type (EARS):** ubiquitous

## Requirement

The 問い合わせ site shall show, for each inquiry, the total of 作業時間 of all 対応履歴 records linked to it.

## Acceptance criteria

1. An inquiry with response records of 30 and 45 分 shows a total of 75 (unit 分, Q19 `[assumed]`).
2. Adding, changing or deleting a linked response record updates the total of its inquiry (e.g. 45 → 60 gives 90; deleting the 30 gives 60).
3. A response record with empty 作業時間 counts as 0; an inquiry without response records shows 0 or empty.
4. After the release, inquiries whose response records were entered **before** the change also show their correct total (Q21 `[assumed]` yes). KB D16: a new summary does not recalculate existing parents — P2 must plan a migration; this criterion is checked on a sample of past inquiries through the API.
5. 対応回数 still shows the number of response records of each inquiry (existing behaviour unchanged).
6. The total is read-only on the edit screen (Q22 `[assumed]`). *(KB D17: read-only is a screen setting; API clients could still overwrite the value — recalculated on the next change of a linked response.)*

## Notes

- Monthly reporting itself (by which month: 受付日 of the inquiry or 対応日時 of the response; inquiries spanning months) is not specified — Q20 `[assumed]`: only the per-inquiry total is provided; the monthly figure is taken by the customer from the list / export.
- New column on 問い合わせ → impact on list, filter, edit screen and export (step 4): `[assumed]` shown in the list and on the edit screen, not added to the filter — Q22.
- The AI first response reads selected inquiry fields only; a new column does not change its input.
