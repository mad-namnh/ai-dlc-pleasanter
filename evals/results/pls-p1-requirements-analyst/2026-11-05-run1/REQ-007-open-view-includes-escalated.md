# REQ-007 — 「未完了」 view keeps escalated inquiries (derived)

- **Status:** awaiting G1
- **Source:** derived from REQ-001 impact analysis: view 「未完了」 filters 状況 on 受付/対応中/顧客回答待ち only, so a new status would disappear from it
- **Type (EARS):** state-driven

## Requirement

While an inquiry's 状況 is エスカレーション済, the 問い合わせ管理 site shall list it in the 「未完了」 view.

## Acceptance criteria

1. `getsite`: view 「未完了」 status filter contains 受付, 対応中, 顧客回答待ち and エスカレーション済, and not 解決 / クローズ（対応不要）.
2. Listing records with view 「未完了」 returns an escalated test inquiry and still excludes 解決 / クローズ inquiries.
3. Sort order (対応期限 ascending) is unchanged.
