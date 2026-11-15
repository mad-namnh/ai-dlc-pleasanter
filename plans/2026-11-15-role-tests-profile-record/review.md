# Review — Role tests profile record

## Round 1 (pls-x-reviewer, opus, high) — accept with fixes; no Critical/High

- **R1 Medium:** L-PRF-01 hint `pls profile set Role tests "…"` fails (argparse) → field quoted when it has a space; test runs the printed hint through `pls.main`.
- **R2 Medium:** no pls command reads Role tests (skills read the row); docstring / ADR-0014 TB-1 / ADR-0020 claim enforcement → docstring corrected; ADR wording back to Nam (stop point 1).
- **R3 Medium:** unrecorded annotated rows (`` `deferred` (…) ``, `deferred - no keys`, `` `Deferred` ``) silent → only the template text (both values joined by " / ") is a placeholder; any other unrecorded row is reported; test.
- **R4 Low:** pls.py usage line, test docstring → fixed. Lifecycle / P4 skill text does not name Role tests → TD (skill text needs an eval).
- **R5 Low:** record file name with a space → stem `role-tests`; test.
- **R6 Low (disposition):** init quote rebuilt from the command line incl. default `--stage` — existing pattern for `--origin`; ADR-0020 states "Role tests from `--stage`". No change.
- Suites 3.12 613 OK, Node 16/16; parent check confirmed by the reviewer; template patch applies, still open.
