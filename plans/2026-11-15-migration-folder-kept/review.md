# Review — migration folder kept

## Round 1 (pls-x-reviewer, opus, high) — accept with fixes; no Critical/High

- **M1:** new use of a migration (data load with any release) not recorded → ADR-0004 Consequences as-built note (not Decision), architecture P5 + P-MIG-01, `pls.py` usage line, `pls_migrate.py` docstring. P5 skill step: tech-debt line added after the D40 commit (tech-debt.md holds that task's uncommitted edits).
- **M2:** a load before the configuration that defines the site's columns/keys — order risk; `bulkupsert` on undefined columns not verified. → ADR note + architecture: the load goes in a release of its own after the release that defines the columns (the trial did so: R-20261115-01-dev columns, R-20261115-04-dev load).
- **L1:** refusal tests now assert the reason. **L3:** `--migration ""` message fixed. **L4:** log wording English.
- **L2 (disposition, not fixed):** no test of `migrate`/`apply` on a config-only plan; the paths do not read the classification (`pls_migrate.dirs`, apply `MI.pending`), and the trial ran it live on dev (R-20261115-04-dev: 150 records migrated, applied, round trip 0 differences).
- Reviewer verified parent-commit failure itself; suites green; tree unchanged after review.
