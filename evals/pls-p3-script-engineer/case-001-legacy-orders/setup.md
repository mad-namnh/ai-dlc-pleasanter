# Setup — script-engineer case 001 (fictional)

For whoever runs the case; the runner never opens this file.

Copy `project/` of this case folder into the run's scratch folder, then convert `config/orders/server-scripts/calc-total.js` to CRLF line endings (the repository stores text with LF; keeping CRLF is part of the case). The project has no `CLAUDE.md`, no gate or profile records and no slot ledger: `pls lint` reports L-GATE-01 and L-PRF-01 lines for them — setup premises, not part of the case. Brief premise: "G2 of DES-002 and DES-004 is approved per the files; no gate records."

What the project holds: `calc_total` (BeforeUpdate) reads 小計 (NumA) and 値引 (NumC), writes 合計 (NumB), has `var taxRate = 1.1;` and further down an `items.Get(1202, …)` (site id of 顧客マスタ on dev); `check_discount` also reads NumA and NumC. DES-004 names the reference `${env:TAX_RATE_STMT}`, whose value is the whole statement on dev, dev-taro and stg, so lint L-REF-04 does not apply. Checked 2026-11-20 on a copy: `pls lint` before and after the one-line edit reports L-REF-01 for 1202 plus the setup lines (and L-LAD-01 for `check_discount` before DES-002 was added); `pls xref --site orders` lists NumA and NumC used by 2 scripts.

Until 2026-11-19 the input was one paragraph (a 400-line script described, not given; `${env:TAX_RATE}` with the value `1.1`), which a run could not carry out once L-REF-04 made a short embedded value a stop for the person (results 2026-11-19).
