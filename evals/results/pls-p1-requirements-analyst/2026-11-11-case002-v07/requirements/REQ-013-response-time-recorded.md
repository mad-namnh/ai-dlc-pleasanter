# REQ-013 — Response time is recorded on each 対応履歴 record

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-improvement-request.md` — item 3 (対応履歴に対応時間を入れられるようにしてほしい)
- **Type (EARS):** ubiquitous

## Requirement

The 対応履歴 site shall let the person who records a response enter the time spent on it, in minutes, in the existing column 作業時間.

## Acceptance criteria

1. The edit screen of 対応履歴 shows 作業時間 with unit 分; a value (e.g. 45) can be entered and saved, and `get` returns 45.
2. 作業時間 is shown in the 対応履歴 list (already in the grid today).
3. 作業時間 can be left empty (no new required check — not requested).

## Notes

- **Overlap:** the 対応履歴 site already has 作業時間 (number, unit 分, on the edit screen and in the list). No new column is written as a requirement; whether 作業時間 is what the customer means by 対応時間 is Q18 `[assumed]` yes. If it is already in use, this requirement is met by the current configuration; if the customer answers no, a new column is decided at G1.
- How much of 作業時間 is filled in on existing records is unknown (no data export in this project) — relevant for REQ-014 and Q21.
