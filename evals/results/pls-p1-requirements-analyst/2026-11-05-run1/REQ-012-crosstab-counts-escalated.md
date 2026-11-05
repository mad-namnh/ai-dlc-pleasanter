# REQ-012 — Status aggregations count エスカレーション済 (derived)

- **Status:** awaiting G1
- **Source:** derived from REQ-001 impact analysis: the 状況 aggregation and the 「状況×チャネル」 cross-tab view group by 状況
- **Type (EARS):** ubiquitous

## Requirement

The 問い合わせ管理 site shall count エスカレーション済 inquiries as a separate 状況 in the 状況 aggregation and in the 「状況×チャネル」 view.

## Acceptance criteria

1. With one escalated test inquiry, the 「状況×チャネル」 cross-tab shows a row 「エスカレーション済」 with count 1 under its チャネル (UI or API check).
2. The 状況 aggregation on the list shows 「エスカレーション済」 with its count.
3. Counts of the other statuses are unchanged by the addition.
