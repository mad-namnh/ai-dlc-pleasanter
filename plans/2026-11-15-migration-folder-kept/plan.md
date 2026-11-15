# Plan — a `--migration` folder given for a release that is not data-impacting is checked and kept

- **Tier:** Critical (release plan, migration order of ADR-0004).
- **Source:** trial `pls-trial-store-promo` commit 48a540b: the first master load (150 品目) was refused by `pls migrate` because `release-plan` dropped the folder (release config-only → `"migration": null`).
- **Change:** `pls release-plan` and `pls plan` check every given `--migration` folder with the same folder checks (migration.json site/keys/rollback, backup/, dry-run.md) and keep it in `plan.json`; incomplete → refused, nothing written. Data-impacting releases unchanged. Help text updated.
- **Split out (stop point 1, Nam):** the "nothing to convert" migration form (empty site, no keys/rollback) — departs from ADR-0004 Decision 2; asked separately. Its code is kept in the scratchpad, not in this commit.
- **Acceptance:** (1) given folder checked and kept for config-only releases, single-site and multi-site; (2) incomplete folder refused, no plan written; (3) data-impacting behaviour unchanged; (4) new tests fail on a6ecf67; (5) both suites green; (6) review: no open Critical/High.
