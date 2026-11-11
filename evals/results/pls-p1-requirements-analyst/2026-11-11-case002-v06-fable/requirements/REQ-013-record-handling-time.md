# REQ-013 — Handling time is recorded on 対応履歴 (existing 作業時間)

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-category-accounting-worktime.md` (item 3)
- **Type (EARS):** ubiquitous

## Requirement

The 対応履歴 site shall accept the time spent on one response in the existing field 作業時間 (minutes).

## Acceptance criteria

1. The edit screen of a 対応履歴 record shows 作業時間 with the unit 分, and a value entered there is saved (API create/update with 作業時間 = 30, `get` returns 30).
2. The list of 対応履歴 shows 作業時間.
3. A 対応履歴 record can still be saved without 作業時間 `[assumed]` (Q18: not required).
4. No second field for handling time exists on the 対応履歴 site `[assumed]` (Q17).

## Notes

- **Overlap with an existing field (Q17).** 対応履歴 already has 作業時間 (number, unit 分), shown on the edit screen and in the list. The request 「対応履歴に対応時間を入れられるようにしてほしい」 is therefore written against this field, not as a new one, with the assumption `[assumed]` that 作業時間 is the 対応時間 the customer means. Criteria 1 and 2 describe today's configuration; if Q17 is confirmed, this requirement needs no change to the 対応履歴 site.
- Whether the field should be renamed to 対応時間 or use another unit is part of Q17.
- For P2: `NumA` on `responses`. `ValidateRequired` is a screen setting only (D27), relevant if Q18 is answered "required".
