# REQ-006 — AI first response shows the new status by its label (derived)

- **Status:** proposed — derived in P2 (DES-001 impact analysis), **awaiting G1**
- **Source:** impact of REQ-001 (new status 150) on server script `ai1` (DES-000): its status map lists 100, 200, 300, 900, 910 only
- **Type (EARS):** ubiquitous

## Finding

When 「AIで一次対応する」 is used on an escalated inquiry, the prompt sent to the AI shows 「状況: 150」 instead of 「状況: エスカレーション中」. The script says it is generated from `spec.json` and that hand edits are overwritten on re-registration; `spec.json` is not in this project.

## Proposed requirement

The AI first-response feature shall show status エスカレーション中 by its label in the information it sends to the AI.

## Acceptance criteria

1. `ai1` status map contains `"150": "エスカレーション中"`, made in its source (`spec.json`) so re-registration keeps it.

## Note

Touches a rung-3 script (reason unchanged: DES-000). Low impact; G1 may also decide to accept the raw value.
