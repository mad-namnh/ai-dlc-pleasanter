# Plan — L-SEC-01 on the last live-content writers (TD-62) and principals in probes (TD-70)

- **Tier:** Critical (secrets I7; kb-verify guards). **Origin:** Nam 2026-11-17 "cu lam tiep khong can hoi".
- **Change:** `env-compare` refuses before writing its report when a source holds a secret-like value; `mark-applied` (applied-differs) refuses before printing the diff and before writing `live-<site>.json`; a test for harvest's raw-export check; `check_probe` refuses principal ids in `Users` / `Groups` / `Depts` lists of probe settings and steps.
- **Acceptance:** (1) no value printed or written; (2) release state unchanged on refusal; (3) existing probes still load; (4) new tests fail on the parent (harvest's test covers behaviour that already existed); (5) suites green; (6) review no open Critical / High.
