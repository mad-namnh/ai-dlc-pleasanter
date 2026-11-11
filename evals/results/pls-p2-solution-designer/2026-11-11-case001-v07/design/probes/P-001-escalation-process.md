# P-001 — Escalation process: stamp into a read-only date-time column, and side effects on site notification / reminder

- **Design:** DES-001 (E3–E7, impact rows "Site notification 1", "Reminder 1")
- **Status:** written, **not run** (no environment reachable in this run). **G2 prerequisite.**
- **Where:** dev only — a probe site in a folder the person provides (not the dev `inquiries` site 44565; step 7 is read-only on 44565). Restore/delete afterwards.
- **Why:** the KB documents `InputDate` + `CurrentDate` (schema.md) but not `InputDateTime` + `CurrentTime`, not a data change into an `EditorReadOnly` column, not whether a process save triggers site notifications, and not the meaning of `Reminders[].Condition` / `Notifications[].Expression`.

## Probe site (Results, reproduces the combination DES-001 relies on)

- `Status` choices `100,受付` / `200,対応中` / `300,顧客回答待ち` / `150,エスカレーション中` / `900,解決`.
- `ClassE` choices `高 / 中 / 低`; `Manager` (the probing user); `DateC` with `EditorReadOnly: true`, `EditorFormat: "Ymdhm"`; all in `EditorColumnHash.General`.
- View 2: `Status` `["100","200","300","150"]`.
- Site notification as in `inquiries` #1: mail to `[Manager]`, `MonitorChangesColumns` Status + ClassE, `BeforeCondition 0`, `AfterCondition 2`, `Expression 1`.
- Process `escalate` exactly as DES-001 E3–E6.

## Steps and expected results

| # | Step | Expected | If not |
|---|---|---|---|
| 1 | `getsite` after `updatesite` (round trip) | process, data change, notification, view stored as sent (canonical differences only, D8) | adjust configuration shape in the DES |
| 2 | Record 高 / 200 → execute `escalate` (API, `ProcessId`) | HTTP 200; Status = 150 | design error — back to DES |
| 3 | `get` the record | `DateC` = execution date **and time** | if not stamped into a read-only column: **design changes** (AC3 vs rung 2) → back to G2 with options; if date only: try `BaseDateTime` variants |
| 4 | Same record (now 150) → execute again | HTTP 400 (D10) | design error |
| 5 | Record 中 / 200 → execute | HTTP 400 | design error |
| 6 | After step 2: was the site notification sent (mail log / SMTP sink of dev, if any; otherwise check the notification count in the Pleasanter log) | expected **yes** (safe branch in DES-001) | if no: REQ-005 may be unnecessary — tell G1 |
| 7 | Read-only: open reminder 1 of dev `inquiries` (44565) in the site settings dialog; read what 条件 (`Condition: 2`) shows; same for notification 1 `Expression: 1` | 条件 = view 未完了 | adjust impact row "Reminder 1" |
| 8 | Screen (person, browser): edit screen of a 高/対応中 record shows the button; DateC not editable | as stated | AC3 / AC1 fail → back to DES |

Mail delivery itself is not checked on dev (Q4).

## After the run

Record results here and add KB entries (with version and what the probe contained) through the KB curator.
