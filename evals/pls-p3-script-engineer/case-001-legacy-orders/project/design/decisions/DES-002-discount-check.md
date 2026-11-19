# DES-002 — Discount check on orders

- **Status:** G2 approved (Nam, 2026-10-02)
- **Element:** server script `check_discount` on site `orders` (BeforeUpdate): refuses a save when 値引 (NumC) is greater than 小計 (NumA), with a Japanese message.
- **Ladder:** rung 3 — no standard setting compares two columns on save (validation compares a column with a constant only).
