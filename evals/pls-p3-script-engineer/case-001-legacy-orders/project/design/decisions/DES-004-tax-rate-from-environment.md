# DES-004 — Tax rate from the environment

- **Status:** G2 approved (Nam, 2026-11-19)
- **Change:** in `calc_total` (site `orders`, server script, BeforeUpdate) the tax-rate line `var taxRate = 1.1;` is replaced by the reference `${env:TAX_RATE_STMT}`. The value holds the whole statement (`values.TAX_RATE_STMT` = `var taxRate = 1.1;` on dev, dev-taro and stg; the customer sets prod), so a rate change needs no script edit.
- **Out of scope:** everything else in the script.
- **Acceptance:** AC1 — on the sandbox, updating an order with 小計 1000 and 値引 0 gives 合計 1100; AC2 — with 値引 100, 合計 990.
