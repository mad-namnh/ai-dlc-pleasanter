# REQ-010 — AI一次対応 sees the escalated status by name (derived)

- **Status:** awaiting G1
- **Source:** derived from REQ-001 impact analysis: the AI first-response feature (「AI問い合わせ一次対応」) sends 状況 to the AI using its own list of status names; a new status would be sent as an internal code
- **Type (EARS):** event-driven

## Requirement

When 「AIで一次対応する」 is executed on an inquiry whose 状況 is エスカレーション済, the 問い合わせ管理 site shall give the AI the 状況 as 「エスカレーション済」.

## Acceptance criteria

1. Unit test of the AI script's status-to-text conversion: the escalated status value converts to 「エスカレーション済」; all existing statuses convert as before.
2. On dev, running 「AIで一次対応する」 on an escalated inquiry succeeds (success message, AI fields filled) and the prompt logged by the AI gateway contains 「状況: エスカレーション済」.

## Notes

- For P2: the script `ai1` is generated from a spec (header comment: hand edits are overwritten on regeneration) — change the source spec, not only `ai1.js`. Existing baseline: DES-000.
