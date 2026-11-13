# Plan — P3-6 summary forms keep the decision data (design review G5-b)

- **Date / branch:** 2026-11-12 / `brownfield-adr`; parent `272bef3`
- **Tier:** Standard — output formatting of a refusal; the checks themselves do not change.
- **Change:** `pls release-plan --summary` prints one `SCOPE <site>:` line per site (count, first 5 names, "…", how to get all) instead of one line per component; every other line (refusal, drift, slots, gate, jobs) stays. Content tests for `lint --summary`, `refs --summary`, `release-plan --summary`. Lifecycle names the new flag (0.23).
- **Acceptance criteria:** 1. summary and full runs end with the same exit code and the same refusal / totals line; 2. the summary keeps the count and the names needed to decide; 3. tests: the `release-plan` one fails on the parent; the `lint` / `refs` content tests cover existing behaviour (they pass on the parent by nature); 4. suites green (3.10 too); TD-36, HANDOFF, README updated.
