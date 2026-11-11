# REQ-015 — The total covers 対応履歴 recorded before the release (derived)

- **Status:** awaiting G1
- **Source:** derived from REQ-014 impact analysis: inquiries and 対応履歴 already exist, the total is wanted for the monthly report closing on 12/10 (`sources/2026-11-11-category-accounting-worktime.md`, item 3), and a newly added total is not calculated for existing inquiries by itself (KB D16)
- **Type (EARS):** ubiquitous

## Requirement

The 問い合わせ site shall show the total handling time of REQ-014 also for inquiries whose 対応履歴 records were all entered before the release.

## Acceptance criteria

1. After the release and its migration, for every inquiry that has 対応履歴 records, the total equals the sum of 作業時間 of those records (checked through the API for all such inquiries, not a sample).
2. An inquiry that was not touched by anyone after the release shows the correct total, not empty and not 0, when its 対応履歴 hold 作業時間.
3. The migration changes no value of any 対応履歴 record and no other field of any inquiry (compared with a backup taken before).
4. 対応履歴 records whose 作業時間 is empty stay empty and count as 0 `[assumed]` (Q20: missing past values are not filled in afterwards).

## Notes

- Whether past 対応履歴 records actually carry 作業時間 is not known from the repository (no data here); Q20.
- For P2: KB D16 — adding a Summary does not recalculate existing parents and there is no sync API; touching one child per parent recalculates it. Data-impacting; runs outside weekday business hours (constraint C-2 in `index.md`). API updates create no record version (D14) → backup first.
