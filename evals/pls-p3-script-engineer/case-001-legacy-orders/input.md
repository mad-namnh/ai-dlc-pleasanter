# Input — script-engineer case 001 (fictional)

DES-004 (G2 approved): "`calc_total` must use the tax rate from `${env:TAX_RATE}` instead of 1.1." The script is 400 lines, CRLF, shared = false, BeforeUpdate. Line 120 also contains `items.Get(1202, …)` (site id of customers on dev). The project has sandboxes; the developer's sandbox is `dev-taro`.
