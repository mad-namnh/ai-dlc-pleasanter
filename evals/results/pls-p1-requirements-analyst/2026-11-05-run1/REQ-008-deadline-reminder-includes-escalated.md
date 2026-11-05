# REQ-008 — 対応期限 reminder still covers escalated inquiries (derived)

- **Status:** awaiting G1
- **Source:** derived from REQ-001 impact analysis: reminder 「対応期限が3日以内の問い合わせ」 (to 対応担当) has a condition that appears to reference the 「未完了」 view
- **Type (EARS):** state-driven

## Requirement

While an inquiry's 状況 is エスカレーション済, the 問い合わせ管理 site shall include it in the 「対応期限が3日以内の問い合わせ」 reminder to the 対応担当.

## Acceptance criteria

1. `getsite`: the reminder's condition selects a set of records that includes エスカレーション済 inquiries (e.g. through REQ-007's 「未完了」 view).
2. Listing records with that condition returns an escalated inquiry whose 対応期限 is within 3 days.
3. *(Not automatically testable: reminder mail delivery.)*

## Notes

- That the reminder's `Condition: 2` means view Id 2 (「未完了」) is **not** in `pls-kb-pleasanter` (only notification Before/AfterCondition is documented). P2 must verify it on dev and record it.
- Escalated inquiries keep their 対応担当 (REQ-001 note), so the reminder still goes to the 対応担当 `[assumed]`.
