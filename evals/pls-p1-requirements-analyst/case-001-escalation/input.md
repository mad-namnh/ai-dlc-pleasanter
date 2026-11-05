# Input — case 001 (from slice #1)

Run against a scratch project holding the **pre-slice** configuration: `pls-demo-inquiry/.pls/exports/stg-44573-before.json` unpacked with `pls unpack` (`${site:responses}` in `ai1.js`), slot ledger without DateC, `design/decisions/DES-000` only, empty `requirements/`. Give the agent only the skills and the request below — never `evals/` or slice #1 outputs. The summary below omits some elements the real config has (reminder 1, aggregation 1); the agent must read `config/`.

## Request (customer, Japanese)

優先度が「高」の問い合わせは、対応担当がワンクリックでサポート責任者にエスカレーションできるようにしたい。
エスカレーションした日時を記録し、責任者にはメールで知らせてほしい。

## Current configuration (site 問い合わせ, record table)

- Status choices: 100 受付, 200 対応中, 300 顧客回答待ち, 900 解決, 910 クローズ（対応不要）
- Columns: ClassA 問い合わせ番号 (required), ClassB 顧客名, ClassC チャネル, ClassD カテゴリ, ClassE 優先度 (高/中/低), DateA 受付日 (required), DateB 対応期限, Owner 対応担当, Manager サポート責任者, NumA 対応回数, CheckA AIで一次対応する, ClassF–H/DescriptionA AI outputs
- Views: 1 標準; 2 未完了 (Status ∈ 100/200/300); 3 状況×チャネル
- Notification #1: mail to [Manager] when Status/ClassE change, condition = view 2
- Server script ai1: AI first response; contains a Status label map (100/200/300/900/910)
