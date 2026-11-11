# DES-002 — Priority choice 緊急

- **Status:** G2 approved (Nam, 2026-11-05)
- **Requirements:** REQ-005 (G1 approved 2026-11-05). REQ-006 withdrawn (Q5 = no).
- **Change classification (ADR-0004):** **config-only** — one choice is added to 優先度; nothing is removed or renamed; no record value changes; no permission change. On stg the choice already exists (accepted drift), so the release only brings git in line with live.

## Ladder (I5)

Rung 1 only (standard setting: choice list). No process, script or SQL change.

## Design

| # | Element | Setting (P3) | REQ | Rung |
|---|---|---|---|---|
| E1 | 優先度 choices | `Columns[ClassE].ChoicesText` = `緊急\n高\n中\n低` — identical to live stg (drift report), so dev, stg and git converge | REQ-005 | 1 |

## Rejected alternatives

- **Revert the drift** (option B) — rejected by the tech lead; removing a choice in use is data-impacting (D11).
- **Add 緊急 at the end of the list** — would differ from live stg and create a new drift; order also carries meaning (Q7: above 高).

## Impact analysis (`impact-checklist.md`, current `config/inquiries/`)

| Existing element | Impact | Action |
|---|---|---|
| Process `escalate`, `View.ColumnFilterHash.ClassE = ["高"]` | 緊急 inquiries do not get the button — **intended** (Q5 = no) | none; P4 adds a negative test for 緊急 (REQ-002 AC) |
| Column ClassG (AI: 推奨優先度) choices 高/中/低; `ai1` allowed list | unchanged — AI does not recommend 緊急 (Q6) | none |
| Notification #1 (`MonitorChangesColumns` incl. ClassE) | changing 優先度 to 緊急 triggers it like any priority change | none — mail deferred (framework TD-10) |
| Views 1–3, aggregation (Status), `FilterColumns`/`GridColumns` (ClassE) | new choice appears in the filter and grid automatically | none |
| Reminder 1 | independent of 優先度 | none |
| Permissions | unchanged | none |
| Slot ledger | no new column; ClassE already allocated | none |

## Migration

Not applicable. Rollback: redeploying R-20261105-01 would remove 緊急 → data-impacting once any record uses it; rollback of this change therefore needs its own decision (D11).

## Open points

- Customer confirmation of Q-adopt, Q6, Q7 still open (asked in Japanese in `requirements/index.md`).
