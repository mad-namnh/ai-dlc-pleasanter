# Independent Quality Audit — AI-DLC Framework for Pleasanter

**Branch:** `brownfield-adr`
**Date:** 2026-11-08
**Auditor:** independent agent (tool-system-evaluator)
**Scope:** readiness for (a) onboarding an existing app read-only tonight, (b) first change request on dev

---

## A. Executive Summary

### Verdicts

**(a) Read-only onboarding tonight: READY WITH CONDITIONS.**
The `adopt`, `env-compare`, `version` and `refs`/`xref` commands are exercised by 145 + 6 passing tests and proven on a real site (797). The `pls-x-onboarding` skill routes correctly for `Origin: existing`. The mail/jobs guard (ADR-0010) refuses writes while side effects are `unknown`. Conditions: the operator must record `side_effects` in `environments.json`, record the Pleasanter version with `pls version`, and create a probe folder for `kb-verify` before any write. No action is needed tonight for a read-only onboarding.

**(b) First change request on dev: READY WITH CONDITIONS.**
The write path is well guarded (assert_writable, scope gate, drift check, slot check, mail guard, sandbox isolation). The `test_write_guards.py` mutation-test locks down every write endpoint. The lifecycle skill correctly routes change requests through P1-P6 after onboarding. Conditions: (1) ADR-0009/0010/0011 must be formally accepted by Nam (they are implemented but still "Proposed"), (2) the `jobs` guard is not yet implemented (ADR-0012 option B chosen but code deferred -- only matters if the candidate uses scheduled server scripts), (3) README and HANDOFF are severely stale and must be updated before another person works on the framework.

### Overall Score: 3.8 / 5 (confidence: high)

### Top 5 Strengths
1. **Write safety is defense in depth**: role check + allow_write + scope gate + drift check + mail guard + AST-scanned mutation test (test_write_guards.py).
2. **Invariants I1-I3 enforced by deterministic code**, not by agent instructions alone.
3. **Brownfield tooling is substantial**: adopt, env-compare, sandbox, harvest, merge driver, script refs, xref, kb-verify -- all tested and proven on a real site.
4. **Test suite is large and meaningful**: 145 Python + 6 Node tests, all passing, covering critical paths including failure/rollback scenarios.
5. **Architecture docs are thorough and honest**: open items, deferred decisions, and escaped defects are tracked systematically (tech-debt.md, review-findings.md, plan.md).

### Top 5 Risks
1. **pls.py at 2482 lines with 399-line http_cmd**: the monolith concentrates risk and is hard to review.
2. **Six ADRs (0001, 0002, 0003, 0007-0011) still say "Proposed"** despite having working code -- a governance/traceability gap.
3. **README and HANDOFF are severely stale** (say pls v0.2/v0.7, skills v0.1, 54 tests vs actual v0.8+, 12 skills, 145 tests) -- a newcomer onboarding risk.
4. **I4 (human gate approval) enforced only by skill text** -- no code prevents an agent from writing an approvals.md file itself.
5. **Jobs guard (ADR-0012) not implemented in code** -- if the candidate has scheduled server scripts that run on record changes, tests could trigger them without warning.

---

## B. Quality Scorecard

| # | Dimension | Score | Confidence | Evidence | Key Gap |
|---|---|---:|---|---|---|
| 1 | Architecture and design | 4 | High | architecture.md v0.3, 9 invariants, 6 phases, 4 gates, 12 ADRs, clear scope | 6 ADRs still "Proposed" |
| 2 | Functional correctness | 4 | High | 145+6 tests pass, 3 slices proven end-to-end, real-site adoption (797) | L-LAD-01 checks script name in design text (brittle) |
| 3 | Security and safety | 4 | High | write guard 3-layer (role+allow_write+scope), secrets lint, key resolution refuses literals, AST mutation test | I4 not code-enforced; jobs guard missing |
| 4 | Reliability and resilience | 4 | High | rollback on apply failure, drift check, preflight on UpdatedTime, adopt cleanup on failure, harvest refuses dirty worktree | No retry/timeout tuning for slow networks |
| 5 | Testing and verification | 4 | High | 151 tests, all pass, covers rollback/failure/refusal paths, write-guard mutation test | No property-based tests; unclosed-socket warnings in test output |
| 6 | Performance and scalability | 3 | Medium | stdlib-only Python, no async; works for single-site; order-by-dependency for multi-site | 399-line http_cmd; no connection pooling; many sites untested |
| 7 | Maintainability | 3 | Medium | 9 modules extracted; clear naming; no bare excepts; Windows UTF-8 handled | pls.py 2482 lines; http_cmd 399 lines; main 380 lines |
| 8 | Observability and operations | 3 | Medium | apply-log.json, drift reports, adoption reports, version tracking | No structured logging; no timing/token metrics in the tool itself |
| 9 | Brownfield/flow routing | 4 | High | lifecycle 0.9 routes by Origin; adopt skips bootstrap; lifecycle cases 002/003 pass | No code-level guard against running P1 without onboarding for Origin=existing |
| 10 | Documentation and DX | 2 | High | README, HANDOFF severely stale; setup.md is current; architecture.md is thorough | README says pls v0.2, skills v0.1, "directories not created yet" |

**Weighted overall: 3.8 / 5** (weights: arch 15%, correctness 15%, security 15%, reliability 12%, testing 10%, perf 8%, maintain 8%, observability 7%, routing 5%, docs 5%)

---

## C. Findings Register

### F-01 [High] README.md is severely stale
- **Component:** `README.md`
- **Evidence:** Lines 18, 24-25 say architecture v0.1, pls v0.2, skills v0.1 (3 skills). Line 66 says "cli/, skills/, agents/, hooks/ and test-harness/ directories are intentionally not created yet." Actual: architecture v0.3, pls ~0.8 (10 modules), 12 skills, 145+6 tests, and skills/ exists with content.
- **Failure scenario:** A new team member reads README, gets a completely wrong picture of the project state.
- **Recommendation:** Update README as part of D6 cleanup, before anyone else works on the framework.
- **Effort:** S

### F-02 [High] HANDOFF.md is stale
- **Component:** `HANDOFF.md`
- **Evidence:** Line 61 says "54 python tests + 6 node tests"; actual is 145+6. Line 19 says "pls 0.7" and "KB 0.9, P1 0.3, P2 0.5, P3 0.1, P4 0.2, P5 0.1, lifecycle 0.1" but the brownfield-adr branch has KB 0.13, P3 0.3, P4 0.3, P5 0.2, lifecycle 0.9, plus 4 new brownfield skills. The status section (lines 28-46) describes state as of slice #2, not the brownfield work.
- **Failure scenario:** A session starting from HANDOFF runs the wrong version of commands or skills.
- **Recommendation:** Update HANDOFF to reflect brownfield-adr state before using it as a handoff document.
- **Effort:** S

### F-03 [High] Six ADRs say "Proposed" but have working, tested code
- **Component:** `docs/adr/0007-0011` and `0001`
- **Evidence:** ADR-0007 says "Proposed -- to be confirmed by the probe on dev and the equipment-loan demo" but the demo (D5) is done and the code is proven. ADR-0008 says "Proposed -- implemented in pls 0.5" with a first real run. ADR-0009-0011 say "Proposed" with notes that code is done on brownfield-adr. ADR-0001 is still Proposed despite 3 slices + adoption of site 797.
- **Failure scenario:** Governance gap: the framework claims these are proposals, but code enforces them. A review that trusts the status would undercount what is committed.
- **Recommendation:** Nam reviews and accepts ADR-0007, 0008, 0009, 0010, 0011 (and 0001 with its known limits). This is a gate decision, not a code change.
- **Effort:** S (review meeting)

### F-04 [High] I4 (humans approve at gates) enforced only by skill text
- **Component:** `skills/pls-x-lifecycle/SKILL.md` section 2 rule 1; `templates/project/CLAUDE.md` hard rule 1
- **Evidence:** The gate enforcement is the sentence "Never approve a gate yourself" in skill text. No code prevents an agent from writing `releases/R-*/approvals.md` or changing a REQ status to "G1-approved" without human input. `pls` commands do not check gate records before proceeding.
- **Failure scenario:** An agent with the lifecycle skill loaded could, through a misunderstanding, write an approvals.md and continue past a gate without human approval.
- **Recommendation:** Accept as a known design trade-off for demo/dev stage. For the production stage, add a `pls gate <id> --approved-by <name>` command that writes the record and is the only approved way to mark a gate, with `release-plan` checking for it.
- **Effort:** M (before production use)

### F-05 [High] Jobs guard not implemented in pls code
- **Component:** `pls_side_effects.py`, `pls.py`
- **Evidence:** `pls_side_effects.py` defines `JOB_STATES` (line 21) and `effects()` (line 31) reads and validates the `jobs` value, but no code refuses a test or apply when `jobs` is `unknown` or `live`. The comment in plan.md BR1 says "jobs guard (ADR-0012)" is open. ADR-0012 chose option B (files in git, manual deploy) but the tool-level guard is not built.
- **Failure scenario:** On the candidate project, if dev has scheduled server scripts that fire on record changes, `pls test` or `pls apply` could trigger them without warning.
- **Recommendation:** Before the first test run on the candidate: (1) ask the server operator whether dev runs scheduled scripts, (2) record `jobs` in environments.json. Building the tool guard is M-effort and can wait if the answer is "disabled."
- **Effort:** S (ask the question) / M (build the guard)

### F-06 [Medium] pls.py is 2482 lines with 399-line http_cmd
- **Component:** `tools/pls/pls.py`
- **Evidence:** `http_cmd()` at line 1692 is 399 lines handling 11 subcommands in a single if/elif chain. `main()` at line 2095 is 380 lines of argparse setup. The top 5 functions account for ~1400 lines of the file.
- **Failure scenario:** Hard to review, hard to test in isolation, high merge-conflict risk when multiple developers touch it.
- **Recommendation:** Extract `http_cmd` subcommands into separate functions (apply_cmd, bootstrap_cmd, test_cmd, etc.). This is a refactoring that does not change behavior.
- **Effort:** M

### F-07 [Medium] Unclosed socket warnings in test output
- **Component:** `tools/pls/tests/test_http.py`, `test_adopt.py`, `test_kbverify.py`
- **Evidence:** Running `python -m unittest discover -s tests` produces ~30 `ResourceWarning: unclosed <socket.socket ...>` messages. The fake HTTP server's sockets are not fully drained/closed in tearDown.
- **Failure scenario:** On a CI server with stricter resource limits, these could accumulate. No functional impact currently.
- **Recommendation:** Close the fake server and its sockets in tearDown. Low priority.
- **Effort:** S

### F-08 [Medium] L-LAD-01 checks script name presence in design decision text (brittle)
- **Component:** `pls.py` line 517: `if kind == "ServerScripts" and not it.get("Shared") and nm and nm not in decisions`
- **Evidence:** The lint rule joins all .md files under `design/` and checks if the script's `Name` appears as a substring. A script named "a" would match any document containing the letter "a". A script named with Japanese characters would need exactly those characters in a design decision.
- **Failure scenario:** False negatives (common short names match incidentally) and false positives (legitimate scripts whose name format does not match).
- **Recommendation:** Use a structured check: DES files should list script names explicitly (e.g., in a "Scripts" section), and lint should parse that list.
- **Effort:** M

### F-09 [Low] No code-level guard against P1 without onboarding for Origin=existing
- **Component:** `skills/pls-x-lifecycle/SKILL.md` section 0
- **Evidence:** The routing is in skill text only. The lifecycle skill (section 0) says "Do not start P1" when Origin is `existing` and no onboarding summary exists, and saves pending requests verbatim. But `pls` has no command that checks the profile Origin before allowing requirements analysis.
- **Failure scenario:** An agent that does not load the lifecycle skill, or that ignores section 0, could write REQ files for an existing app without onboarding.
- **Recommendation:** Accept for the current stage. The lifecycle skill is the standard entry point. For production, consider a `pls check-ready p1` command.
- **Effort:** S (later)

### F-10 [Low] architecture.md section 7.1 command table is incomplete for brownfield
- **Component:** `docs/architecture.md` lines 260-280
- **Evidence:** The command table lists commands through pls 0.3-0.6 but does not include brownfield commands: `adopt`, `env-compare`, `sandbox create/refresh/drop`, `harvest`, `merge-site`, `merge-install`, `refs`, `xref`, `kb-verify`. These exist and are tested.
- **Failure scenario:** A person reading architecture.md does not know these commands exist.
- **Recommendation:** Add the brownfield commands to the table as part of D6.
- **Effort:** S

### F-11 [Low] No connection timeout configuration
- **Component:** `pls_http.py` line 105: `timeout: float = 30`
- **Evidence:** The HTTP client uses a hard-coded 30-second timeout. For a slow on-prem Pleasanter with many sites, large exports could time out.
- **Failure scenario:** Export of a site with hundreds of scripts or records times out, and the error message is unclear.
- **Recommendation:** Allow `timeout` in connections.json. Low priority for onboarding.
- **Effort:** S

---

## D. Invariant Enforcement Summary

| Invariant | Enforcement Level | Evidence | Gap |
|---|---|---|---|
| I1 Git is desired state | **Code** | `pls unpack/pack/drift/mark-applied` maintain the git-Pleasanter correspondence; `mark-applied` requires 0 differences | None for managed components; unverified components are gated by scope check |
| I2 Complete payloads + drift check | **Code** | `plan_site()` (pls.py:779) checks L-DEP-01 (payload completeness), drift vs last release, slot collisions; `release_plan()` refuses on any failure | None |
| I3 AI has no prod path | **Code** | `assert_writable()` (pls_http.py:92) refuses role=prod; `test_write_guards.py` AST-scans every write endpoint and caller; `test_prod_is_never_written` confirms dynamically | Solid |
| I4 Humans approve at gates | **Skill text only** | lifecycle SKILL.md rule 1, project CLAUDE.md hard rule 1; `_confirm()` for apply/bootstrap requires user confirmation | No code prevents agent from writing approvals.md (F-04) |
| I5 Standard before code | **Code (lint)** | L-LAD-01 (pls.py:517) flags server scripts without a design decision | Substring match is brittle (F-08) |
| I6 Deterministic checks | **Code** | `pls diff`, `pls classify`, `pls coverage`, `pls lint` are all pure functions; release-plan calls them | AI writes the diff-report.md text, but raw diff is always attached |
| I7 No secrets in git | **Code (lint)** | L-SEC-01 (pls.py:505) regex-scans configuration for secret patterns; `pls_adopt.py` refuses before writing if secrets found; key resolution refuses literal keys (pls_http.py:89) | Not a pre-commit hook; relies on lint being run |
| I8 Traceability | **Code + skill** | `pls coverage` checks REQ-config-test chain; coverage-reviewer is planned but not built | Coverage check exists; reviewer agent is missing |
| I9 Escaped defects become rules | **Process** | tech-debt.md, review-findings.md track defects; KB probes (kb-verify) re-verify facts; lint rules seeded from findings | No automation: a person must create the rule |

---

## E. Two Flows: Greenfield vs Brownfield

### Routing
- `pls init --origin existing` sets Origin in project CLAUDE.md (pls.py:1521,1536,2197).
- Lifecycle skill section 0 (SKILL.md:15-28) routes by Origin: `existing` without onboarding summary → `pls-x-onboarding` then `pls-x-spec-recovery`; existing with summary → change request via P1.
- Lifecycle routing cases 002 and 003 pass (skills/README.md line 17).

### Separation
- `bootstrap_plan()` (pls.py:1339) skips adopted sites (line 1356: `if _adopted(r, site)`).
- `release_plan()` (pls.py:827) recognizes new sites from bootstrap records and relaxes the data-impacting gate for first releases (line 854-862).
- Sandbox `release_plan` refuses shared sites (pls.py:843).
- `adopt()` (pls.py:940) never overwrites existing config (line 961).
- Adoption records are `kind: adopt` and the lifecycle skill explicitly says they are not releases (lifecycle SKILL.md line 41).

### Potential Gaps
- **No code-level guard** prevents P1 without onboarding for `existing` projects (F-09). The guard is in skill text only.
- **Slot ledger zones** (`customer` vs framework/project) are set by adopt but not enforced by lint -- a developer could allocate a slot in zone `customer` without the customer's agreement. This is a known deferred item (TD-01).

---

## F. Safety of Writes

### Write Guard (3-layer)
1. **Role + allow_write:** `assert_writable()` (pls_http.py:92) requires role dev/stg AND allow_write=true. Called at pls.py:1768 (apply), 1816 (bootstrap), 1837 (test), 1911 (kb-verify).
2. **Scope gate:** `site_findings()` in pls_scope.py:61 blocks deploy of sites with unverified components.
3. **Mutation test:** `test_write_guards.py` uses AST analysis to lock down:
   - Every subcommand classified (WRITES/NETWORK_READS/LOCAL, line 24-28)
   - Write endpoints appear only in ALLOWED_WRITE_SITES (line 30-31, test at line 79)
   - CLIENT_WRITERS and WRITE_RUNNERS called only from known functions (line 89)
   - Dynamic test: all writing commands with allow_write=false send nothing (line 121)
   - Prod is never written (line 147)

### Side Effects (ADR-0010)
- `pls_side_effects.py` guards mail at test time (`test_refusal`, line 137) and apply time (`apply_refusal`, line 147).
- When mail is `unknown`, tests on sites with notifications/reminders are refused.
- Literal mail addresses flagged by L-MAIL-01 (lint).
- **Gap:** Jobs guard is tracked but not built (F-05).

### KB Verify Safety
- `check_probe()` (pls_kbverify.py:47) refuses probes with Notifications, Reminders, or ServerScripts.
- Only ops `create/get/list/exec` allowed; no `site`, `run_on`, `as_key`, `vars`.
- Probe sites are created in a dedicated folder (not the app folder -- enforced at pls.py:1902).
- Probe sites are reused only when title, type, and parent match (`is_own_probe_site`).

### Sandbox Safety
- `sandbox_create()` refuses sites that write to shared sites unless `--allow-shared-writes` is passed (pls.py:1217).
- `release_plan()` refuses shared_from sites (pls.py:843).
- `apply` in http_cmd checks that plan site ids match the environment's own sites (pls.py:1771-1776).

### test_write_guards.py Assessment
- **Strengths:** AST-based static analysis catches structural changes; dynamic tests confirm no writes without permission.
- **Limitation:** AST scan looks for `call()` with a write-endpoint string. A dynamic dispatch via `getattr` or `eval` would escape detection. However, the codebase does not use either pattern, and `modules()` scans all `.py` files in the tools directory.
- **Limitation:** A new `.py` file in a subdirectory would not be scanned (glob is `TOOLS.glob("*.py")`). Not a current risk since all modules are in the root.

---

## G. Test Quality

- **151 tests, all pass** (145 Python in 35s, 6 Node in 39ms).
- **Meaningful tests:** test_apply_release_ok_and_rollback_on_failure, test_apply_refused_when_live_changed, test_secrets_refuse_before_anything_is_written, test_probe_folder_must_be_a_folder_of_its_own, test_sandbox_cannot_write_shared_sites (in test_sandbox_merge.py).
- **Write-guard mutation test:** ensures new write paths fail the test.
- **No trivially-true tests found.**
- **Resource warnings:** unclosed sockets in ~30 test cases (F-07). Not functionally harmful.
- **Coverage gaps:** no tests for the `merge_site_files` git merge driver with a real git merge; no tests for `_stamp()` collision (timestamp-based names); no property-based tests.

---

## H. Prioritised Remediation Roadmap

### Before Onboarding Tonight (P0/P1)
Nothing is blocking for read-only onboarding. The following are preparatory:

1. **Ask the server operator** whether SMTP is configured on dev and whether scheduled server scripts run. Record `side_effects.mail` and `side_effects.jobs` in the candidate project's `environments.json`. (P0, effort: minutes)
2. **Record the Pleasanter version** of the candidate's dev with `pls version --env dev`. (P0, effort: minutes)
3. **Create a probe folder** in Pleasanter for `kb-verify`. (P1, effort: minutes)

### Before First Change Request on Dev (P1)
4. **Nam accepts ADR-0009, 0010, 0011** (and ideally 0007, 0008, 0001). The code is written; the governance record is missing. (P1, effort: S -- a review meeting)
5. **Verify the jobs state** from item 1. If jobs are live on dev, build the jobs guard or disable them for the sandbox. (P1 if jobs are live, else P2)

### Before Another Person Works on the Framework (P1)
6. **Update README.md** (F-01): reflect the actual state (pls ~0.8, 12 skills, 145+6 tests, brownfield commands, layout). (P1, effort: S)
7. **Update HANDOFF.md** (F-02): reflect brownfield-adr state. (P1, effort: S)
8. **Update architecture.md section 7.1** to list brownfield commands (F-10). (P1, effort: S)

### Before Production Use (P2)
9. **Add a `pls gate` command** for I4 enforcement (F-04). (P2, effort: M)
10. **Refactor pls.py** -- extract http_cmd subcommands (F-06). (P2, effort: M)
11. **Fix L-LAD-01** substring match (F-08). (P2, effort: M)
12. **Build jobs guard** in pls_side_effects.py (F-05). (P2, effort: M)
13. **Fix unclosed sockets** in tests (F-07). (P2, effort: S)

### Later (P3)
14. **Connection timeout configuration** (F-11). (P3, effort: S)
15. **Property-based tests** for merge driver and diff. (P3, effort: M)
16. **Structured logging** with timing metrics. (P3, effort: M)

---

## I. Items Already in plan.md / tech-debt.md -- Audit Agreement or Disagreement

| Plan Item | Plan Severity | Audit View |
|---|---|---|
| TD-01 slot zones need customer | Medium (before prod) | **Agree.** Not needed for dev onboarding. |
| TD-02 prod deploy method | Medium (before prod) | **Agree.** |
| TD-10 mail deferred | Low (before real users) | **Agree.** Side-effect guards are sufficient for dev. |
| TD-11 per-role tests | Medium (before permissions) | **Agree.** Config-level checks are sufficient for the demo stage. |
| TD-12 Windows cp932 | Fixed | **Confirmed fixed:** stdout/stderr reconfigured to UTF-8 (pls.py:80-82). |
| TD-14 pls gaps | (a)-(d) fixed; (e)-(h) before customer | **Agree.** (h) is a minor inconvenience, not a blocker. |
| BR1 mail guard | Done (code) | **Agree it works.** Note: jobs guard portion is open (F-05). |
| BR6 sandbox/harvest/merge | Done (code) | **Agree.** First real run on dev (2026-11-08) passed. |
| BR8 kb-verify | Done (code) | **Agree.** 7/7 entries, 8/8 probes on 1.5.2; safety checks are solid. |

---

## J. Final Decision

**PASS WITH CONDITIONS**

The framework is ready for read-only onboarding tonight and for a first change request on dev, subject to:
1. Record side_effects (mail, jobs) and the Pleasanter version before any write.
2. Nam accepts the Proposed ADRs that have working code (0009-0011 at minimum).
3. README and HANDOFF updated before another person works on the framework.

The write-safety architecture is the strongest part of the system: three layers of code enforcement plus an AST-based mutation test. The brownfield tooling (adopt, env-compare, sandbox, harvest, merge, script refs, xref, kb-verify) is substantial and well-tested for a v0.x. The main risks are documentation staleness and the absence of code-level gate enforcement (I4), neither of which blocks tonight's onboarding or the first dev change.
