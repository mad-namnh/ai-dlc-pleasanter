# REQ-005 — 未完了 view still lists escalated open inquiries (derived)

- **Status:** awaiting G1
- **Source:** derived from REQ-001 / REQ-003 impact analysis: view 2 「未完了」 enumerates statuses (`Status ∈ 100, 200, 300` in `config/inquiries/site.json`). If escalation changes or adds a status (Q6), an escalated but unresolved inquiry would drop out of the list 対応担当 use for open work (KB behaviours, "Adding a new status").
- **Type (EARS):** state-driven

## Requirement

While an escalated inquiry is not in 解決 or クローズ（対応不要）, the 未完了 view shall list it.

## Acceptance criteria

1. An inquiry with 優先度 = 高 and 状況 = 対応中 is escalated; the 未完了 view (API `get` with view 2) still returns it, sorted by 対応期限 ascending as before.
2. The same inquiry, set to 解決 afterwards, is no longer returned by the 未完了 view.
3. Inquiries that were never escalated appear in the 未完了 view exactly as before the change (same filter: 受付, 対応中, 顧客回答待ち).

## Notes for P2

- If P2 adds a status, the same check applies to the 状況×チャネル crosstab (view 3), the 状況 aggregation (Aggregations #1), notification #1 (REQ-006) and the AI script status map (REQ-007).
