# REQ-013 — Record the time of each response in the existing 作業時間

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-improvement-request.md` — item 3 (対応履歴に対応時間を入れられるようにしてほしい)
- **Type (EARS):** ubiquitous

## Requirement

The 対応履歴 site shall record the time spent on each response, in minutes, in the existing column 作業時間.

## Acceptance criteria

1. The 対応履歴 edit screen offers 作業時間 with unit 分; a value entered there is saved and shown in the list (it is already in the grid).
2. An API create / update of a 対応履歴 record with 作業時間 = 45 succeeds and `get` returns 45.
3. No new time column is added to 対応履歴 `[assumed]` (Q17: 対応時間 = existing 作業時間; label unchanged).
4. 作業時間 stays optional on save `[assumed]` (Q21).

## Notes

- Overlap: the customer asks to "add" 対応時間, but 対応履歴 already has 作業時間 (NumA, unit 分) in the editor and grid. This requirement is written against the existing column; Q17 asks the customer to confirm.
- If the customer wants it required (Q21 answered "yes"), that is screen-only (KB D27) unless a script is designed.
