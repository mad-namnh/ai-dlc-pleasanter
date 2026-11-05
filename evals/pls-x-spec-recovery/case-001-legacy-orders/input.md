# Input — spec-recovery case 001 (fictional)

`config/orders/` after adopt: 25 columns (ClassA 顧客 → `[[${site:customers}]]`, NumA 金額, Status 100 受付 / 200 出荷済 / 900 完了), one tab 詳細 with two sections, views 未出荷 and 今月, process 出荷 (100 → 200, DataChanges DateA = today, Groups `${principal:shipping}`), notification to `[Manager]` on status 200, summary into customers (Count), 2 server scripts: `calc_total` (BeforeUpdate, sets NumB from NumA × 1.1), `check_date` (context.Error 「出荷日は受付日以降にしてください」), 1 client script with a 3,000-line minified chart library, `ops/xref/orders.json`.
