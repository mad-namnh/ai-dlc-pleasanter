# REQ-014 — Each inquiry shows the total 作業時間 of its 対応履歴

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-improvement-request.md` — item 3 (問い合わせごとに合計時間が分かると、月次の報告に使えます)
- **Type (EARS):** event-driven

## Requirement

When a 対応履歴 record linked to an inquiry is created, changed or deleted, the system shall show on that inquiry the total 作業時間 of all 対応履歴 records linked to it.

## Acceptance criteria

1. Inquiry with no 対応履歴 → total 0 (or empty, shown as 0 through the API — KB D23).
2. Create two 対応履歴 for one inquiry with 作業時間 30 and 45 → the inquiry's total is 75 (unit 分 `[assumed]`, Q18).
3. Change one of them to 60 → total 90; delete it → total 30.
4. A 対応履歴 without 作業時間 counts as 0; records in status 予定 are included `[assumed]` (Q19).
5. Inquiries whose 対応履歴 existed before the release show the correct total after the release (KB D16: a new summary does not recalculate existing parents — P2 must plan the recalculation; `[assumed]` past 作業時間 values are included, Q23).
6. The total cannot be edited on the inquiry's edit screen (read-only like 対応回数) `[assumed]` (Q22). *(API writes are not blocked — KB D17; the next child change recomputes it.)*
7. The total is shown on the edit screen and in the list of 問い合わせ `[assumed]` (Q22).
8. The existing 対応回数 keeps counting 対応履歴 as before (regression check).

## Notes for P2

- No existing column on 問い合わせ holds a time total: 対応回数 (NumA) is a Count summary from 対応履歴. A new column is needed → slot ledger; KB D22 (must be in `EditorColumnHash`).
- The summary is configured on the child site 対応履歴, which is not in `managed_sites` (PO2).
- Data-impacting (D16) — recalculation of existing inquiries on the live environment needs the operator.
- Monthly figures per month (by 対応日時) are not covered here; Q20 asks whether the per-inquiry total is enough.
