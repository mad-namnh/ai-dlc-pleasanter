# Plan — P1 0.7: impact analysis by condition

- **Task (Nam, 2026-11-11):** "sửa skill lên 0.7 rồi chạy lại case 001" — after case 001 failed twice on 0.6 on the 対応期限 reminder.
- **Tier:** Standard (skill text). Independent review; then eval case 001 (blind), and case 002 is not re-run unless Nam asks.
- **Change:** `SKILL.md` step 2 (record what decides when each notification / reminder / process acts), step 4 status trigger (also when a status is only possible through an open question; elements whose condition is a status view), checklist line. Wording stays generic (no escalation example).

## Acceptance criteria
1. The three edits say: read elements by condition, not only recipient; a view used as condition passes its filter on; an open question that could add a status lists every status-dependent element.
2. Field names stated as Pleasanter facts are the ones the KB documents (`BeforeCondition`/`AfterCondition` = view id; `View.ColumnFilterHash`); the reminder's `Condition` is not asserted beyond what the KB says.
3. No case-specific content (escalation, 対応期限, 未完了) enters the skill.
4. `skills/README.md` row 0.7; both suites green.
5. Case 001 on 0.7 run blind and graded.

## Open question
- Reminder `Condition`: the configurations seen hold a number equal to a view id; the KB has no entry for it. A probe on dev would settle it (for `pls-kb-curator`).
