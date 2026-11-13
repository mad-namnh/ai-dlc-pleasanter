# Review — P3-4 KB rows with version and evidence

- **Reviewer:** `pls-x-reviewer`, model `sonnet`, effort `medium`; round 1 of 2; working tree against `dfdd63c`.
- **Verdict:** accept — 0 Critical, 0 High, 0 Medium, 2 Low. Reviewer compared every "Probe contained / Not covered" text with its probe JSON (all agree) and checked D5 / D35 sources; Python 462 OK, node 15 pass.

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| F-1 | Low | D35 "not changeable per site as shipped" read from `ServerScriptTimeOutChangeable: false`, not checkable offline | No change: the Orchestrator read the file at the tag (log); the row is marked source-derived, not verified |
| F-2 | Low | The test checked only "probe contained", not "Not covered" | Fixed: the test requires both; D33 label normalised to "Not covered:" by the curator (wording only) |
