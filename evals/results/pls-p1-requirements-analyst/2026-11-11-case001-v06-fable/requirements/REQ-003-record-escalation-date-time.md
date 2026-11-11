# REQ-003 — Record the date and time of the escalation

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-escalation-high-priority.md`
- **Type (EARS):** event-driven

## Requirement

When the 対応担当 executes エスカレーション on an inquiry, the system shall record the date and time of that execution on the inquiry.

## Acceptance criteria

1. Before escalation the inquiry has no escalation date-time.
2. After the action is executed (edit screen or API), the inquiry holds a date-time with hour and minute that lies within 2 minutes of the time of the execution.
3. The date-time is shown on the edit screen under the label 「エスカレーション日時」 and cannot be typed over on the screen. `[assumed]` Q6.
4. The execution changes nothing else on the inquiry: 状況, 優先度, 対応担当, サポート責任者, 対応期限 and 対応回数 keep their values. `[assumed]` Q7 (no status change).
5. A later ordinary save of the inquiry does not change the recorded date-time.

## Notes for P2

- Overlap check (procedure step 2): no existing column holds this value. 受付日 and 対応期限 are dates with another meaning; the built-in update time changes on every save. A new date-time column is therefore needed; `design/slot-ledger.json` has no date slot other than DateA/DateB allocated.
- KB D17: "cannot be typed over" is a screen setting only; the API can still write the column. The requirement is stated as screen behaviour.
- KB D22: the column must be in the editor layout to work at all.
- Whether the column also appears in the list and in the filters is Q6.
