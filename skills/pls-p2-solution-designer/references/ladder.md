# The ladder (invariant I5): standard features before code

| Rung | Mechanism | Examples | Needs a written reason? |
|---|---|---|---|
| 1 | Standard settings | columns, choices/statuses, editor layout, views, grid, filters, notifications, reminders, permissions | No |
| 2 | Formulas, プロセス, ステータス制御, input validation | button that changes status and fields, display conditions, computed columns | No |
| 3 | Server script | external API calls, logic across sites that rung 2 cannot express | **Yes** — why rungs 1–2 cannot work |
| 4 | Extended SQL | heavy cross-site queries, batch logic | **Yes** + DBA review |
| 5 | External integration | separate service, ETL, gateway | **Yes** + architecture decision |

## Why

Each rung up costs maintenance, review effort and upgrade risk, and is harder for the customer to understand or change. Customers are allowed to edit configuration (rungs 1–2) themselves; code (rungs 3+) they usually cannot maintain.

## Typical traps

- Using a server script for something a プロセス can do (status change + data change + notification + display condition).
- Using a checkbox to model state that drives display conditions (D9) — use Status.
- Hard-coding SiteIds in scripts (D3) — use `${site:…}`.
