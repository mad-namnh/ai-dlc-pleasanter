# REQ-015 — Existing inquiries show their correct 合計作業時間 from release (derived)

- **Status:** awaiting G1
- **Source:** derived from REQ-014 impact analysis: adding a Summary does not recalculate existing parents (KB D16), so every inquiry created before the release would show 合計作業時間 = 0 although it has 対応履歴 with 作業時間 — wrong figures in the monthly report.
- **Type (EARS):** state-driven

## Requirement

While an inquiry created before the release has 対応履歴 with 作業時間, the system shall show as its 合計作業時間 the sum of those 作業時間 from the first day of use.

## Acceptance criteria

1. After the release, for every inquiry, 合計作業時間 equals the sum of 作業時間 of its 対応履歴 computed independently from a 対応履歴 export (difference 0 for all inquiries).
2. 作業時間, 対応内容 and every other value of the 対応履歴 records are unchanged by the release (compare with the pre-release backup — KB D14). *(更新日時 / 更新者 of the touched 対応履歴 change — `[assumed]` acceptable, Q22.)*
3. 対応回数 of every inquiry is the same before and after the release (see REQ-016).

## Notes

- Scope depends on Q18 (`[assumed]` all existing inquiries). Data-impacting: one 対応履歴 per inquiry must be touched after the release (D16) — migration plan at P2, outside weekday daytime (Q21).
