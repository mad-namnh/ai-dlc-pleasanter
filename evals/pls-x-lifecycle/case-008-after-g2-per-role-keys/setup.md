# Setup — lifecycle case 008 (G2 approved, role tests `per-role keys`, groups not created yet)

For whoever runs the case; the runner never opens this file.

The runner builds the fictional project in its scratch folder from `input.md`. Its `.pls/` cannot be written by the runner (permission rules); its content stays a premise of the input.

Runs before 2026-11-17 named the project folder `pls-demo-purchase`; it is `purchase` since (a fictional name; the rubric does not use it).

Since 2026-11-18 (late) the input says that the `gates/` records and `.pls/connections.json` stay premises and are not built: run r-2577 (lifecycle 0.33) wrote the two gate records itself, with invented dates and quotes, to complete the premise. A real project denies edits under `gates/` through its PreToolUse hook (ADR-0029 C); the eval scratch folder has no hook.
