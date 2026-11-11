# DES-001 — Escalation with a standard プロセス (process)

- **Status:** G2 approved (Nam, 2026-11-05)
- **Requirements:** REQ-001, REQ-002, REQ-003, REQ-004
- **Change classification (ADR-0004):** **config-only** (adds a column, a status choice and a process; changes one view filter; nothing removed)

## Ladder (I5)

Rung: **standard settings + プロセス**. No server script, no extended SQL.

## Design

| Element | Setting | REQ |
|---|---|---|
| Status choice | add `150,エスカレーション中,エ,status-inprogress` (between 100 and 200 in the list) | REQ-001 |
| Column `DateC` | label エスカレーション日時, format date-time (`Ymdhm`), **read-only** in editor; placed after サポート責任者 | REQ-001 |
| Process `escalate` | display name エスカレーション; screen: edit; current status: any; **changed status: 150** | REQ-001 |
| — data change | `DateC` ← current date-time (`InputDateTime`, base `CurrentTime`) | REQ-001 |
| — display condition (process view filter) | 優先度 (ClassE) = 高 **and** 状況 ∈ {100, 200, 300} | REQ-002 |
| — notification | mail to `[Manager]`, subject `【問い合わせ管理】エスカレーション: [ClassA] [Title]`, body with customer name and priority | REQ-003 |
| — messages | confirmation 「サポート責任者にエスカレーションします。よろしいですか？」, success 「エスカレーションしました。」 | REQ-001 |
| View 2 「未完了」 | filter 状況 ∈ {100, 150, 200, 300} | REQ-004 |
| Server script `ai1` | add `150: エスカレーション中` to the Status label map used in AI prompts (keeps AI input readable) | impact of REQ-001 |

## Rejected alternative

Checkbox 「エスカレーション済」 + display condition "checkbox is off": **not possible** — on 1.5.2 a checkbox filter can only select *checked* (`ViewFilters__CheckA` is a 2-state checkbox). Using the standard status also makes escalated inquiries visible in grids and aggregations without extra columns.

## Impact analysis

| Existing element | Impact | Action |
|---|---|---|
| View 2 「未完了」 (filters 100/200/300) | escalated inquiries would disappear from the open list | REQ-004 — add 150 |
| Notification #1 (watches Status, ClassE; condition = view 2) | follows view 2 → keeps escalated inquiries in scope | none |
| Aggregation by Status | shows a new group エスカレーション中 | none (expected) |
| AI script `ai1` status labels | 150 would appear as a bare number in AI prompts | add label |
| Data | no existing record changes; new status only set by the process | none |

## Open points

- Q1 (who may escalate): no process access control in this design; add `AccessControl` if the customer answers "assignee only".
- Q4 (mail delivery): notification is configured; delivery is verified in stg by the customer.
