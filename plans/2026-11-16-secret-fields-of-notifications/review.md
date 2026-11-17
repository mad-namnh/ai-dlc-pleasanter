# Review — credential fields of notifications and reminders

## Round 1 (pls-x-reviewer, opus, high) — accept with fixes; no Critical/High

- **M1:** the task asked that `pack` refuse; it did not → `pack` runs `refuse_secrets` on the resolved payload; test.
- **M2:** a credential kept as an `environments.json` value (e.g. `Headers: ${env:hdrs}`) passed lint and unpack → lint checks the payload of each environment; unpack and harvest check the raw export before values are mapped back; test.
- **M3:** missed forms (`Ocp-Apim-Subscription-Key`, `client_secret=`, Slack / Discord webhook through HttpClient) → header names read as JSON keys and matched on credential words; query parameter names likewise; known webhook hosts / paths for HttpClient; remaining limits stated in the module docstring.
- **L1:** HANDOFF line (in the commit); ADR-0005 open question annotated.
- **L2:** `"Type": Infinity` → OverflowError caught; test.
- **L3:** refusal names the ADR-0005 alternative (internal gateway, extended server scripts).
- Not run by the reviewer: parent check (done by the Orchestrator, log).

## Round 2 (pls-x-reviewer, opus, high) — accept with fixes; F1 High open

- **F1 High:** single-site `pls plan` wrote payload.json / rollback.json / raw-diff.md with no L-SEC-01 → refused before writing (payload and live rollback), with the ADR-0005 hint; test (live webhook → exit 1, no releases/R1; clean live → 0). Fixed after the last round: not re-reviewed.
- **F2 Medium:** raw-export checks untested → unpack test with a credential equal to an environment value; harvest's raw check untested → TD-62.
- **F3 Medium:** refusal list shortened through a lint path that swallows errors → test `test_pack_refuses_an_unmapped_principal_in_an_access_list` asserts the refusal text.
- **F4 Medium:** `env-compare`, `mark-applied` applied-differs write live content without L-SEC-01 → TD-62 (deadline: before the first customer environment is compared or released).
- **F5 Low:** lint caught every exception → catches `Fail` only and reports "L-SEC-01 not checked for env X: <reason>".
- **F6 Low:** numbers, enum names, `user:pass@` URLs → handled; false positives (X-Author) stated as failing closed.
- **F7 Low:** architecture I7 and L-SEC-01, adr/README, review-findings D5 updated; HANDOFF line at commit.
- **Open question (product):** following ADR-0005 layer 3, unpack / adopt / release-plan refuse any site with a Slack, Teams, RocketChat or LINE WORKS notification or a token, even as `${env:x}` — brownfield adoption needs them removed from live first. For Nam.

## Round 3 (pls-x-reviewer, opus, high; Nam "1a") — accept with fixes; no Critical/High

- **F1 closed:** every write of single-site `plan` comes after the check of payload and live rollback; test asserts exit 1, no value printed, no releases/R1.
- **R3-1 Medium:** lint crashed (exit 3) when a site is missing from an environment's `sites` (KeyError) or a principal is still a placeholder (ValueError in `acl_from_refs`) → lint skips an environment that does not hold the site, catches Fail / KeyError / ValueError as "not checked for env"; `acl_from_refs` refuses a principal without a numeric id with Fail; test `test_lint_runs_when_an_environment_lacks_a_site_or_a_principal_has_no_id` (fails on the pre-fix code).
- **R3-2 Low:** payload half of the plan check untested → `test_single_site_plan_refuses_a_token_in_config`.
- **R3-3 Low:** raw-diff.md is built from the whole live export and config/ (SiteName, SiteGroupName) → plan also checks `export` and `git`.
- **R3-4 Low:** test docstring updated; release-plan refusal carries the ADR-0005 hint; f-string without placeholders fixed.
- Not verified by the reviewer: parent check (done by the Orchestrator: log); whether a real getsite answer has a non-empty `ApiKey` (would make unpack refuse, failing closed) — open, TD-62.
