# Input

- G1-approved requirements `REQ-001…004` in `requirements/`
  (escalate → status エスカレーション中 + date-time; available only for 高 and open; mail to [Manager]; 未完了 view includes the new status).
- Current configuration (site 問い合わせ, record table), unpacked under `config/`:
  - Status choices: 100 受付, 200 対応中, 300 顧客回答待ち, 900 解決, 910 クローズ（対応不要）
  - Columns: ClassA 問い合わせ番号 (required), ClassB 顧客名, ClassC チャネル, ClassD カテゴリ, ClassE 優先度 (高/中/低), DateA 受付日 (required), DateB 対応期限, Owner 対応担当, Manager サポート責任者, NumA 対応回数, CheckA AIで一次対応する, ClassF–H/DescriptionA AI outputs
  - Views: 1 標準; 2 未完了 (Status ∈ 100/200/300); 3 状況×チャネル
  - Notification #1: mail to [Manager] when Status/ClassE change, condition = view 2
  - Server script ai1: AI first response; contains a Status label map (100/200/300/900/910)
- Slot ledger: ClassA–H, DateA–B, NumA, CheckA, DescriptionA, AttachmentsA allocated.
