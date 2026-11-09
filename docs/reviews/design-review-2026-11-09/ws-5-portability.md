# WS-5 — Portability, performance and operational readiness

| Item | Value |
|---|---|
| Standard | `docs/review-criteria.md` v2.1; plan `docs/reviews/design-review-2026-11-09/00-review-plan.md` (WS-5, T1/T2/T9/T10) |
| Commit | `10c328a` (detached worktree `wt-ws5`) |
| OS | Windows 11 Pro 10.0.26200, git `core.autocrlf=true` |
| Python | 3.12.10 (`python`), 3.10.21 (isolated, authorized H-3) |
| Node | v24.19.0 |
| Criteria | G1–G6 (primary) |
| Reviewer files (worktree only, not part of the suite) | `tools/pls/tests/review_ws5_windows.py`, `tools/pls/tests/review_ws5_offline_run.py`, `tools/pls/tests/review_ws5_runner_parity.mjs` |
| Logs | `scratchpad/review/ws5-logs/` (t1-312.log, t9-310.log, t9-310-patched.log, g3-offline.log, t2-node.log, bench/*) |

Summary of statuses: G1 FAIL · G2 PARTIAL · G3 PASS · G4 FAIL · G5 PARTIAL · G6 PARTIAL (rest NOT VERIFIABLE: clean machine).

## Findings (§5 format)

| ID | Criterion | Severity | Status | Stage | Finding | Evidence (file:line, test, command output) | Reproduction | Proposed fix | Verification |
|---|---|---|---|---|---|---|---|---|---|
| G1 | Documented minimum runtime is real | Medium | **FAIL** | demo | `docs/setup.md:15` says Python 3.10+; the whole CLI and 13 of 14 test modules fail to import on 3.10. Cause is a **single** construct: backslash inside an f-string expression (PEP 701, 3.12+) in `tools/pls/pls_adopt.py:94`. `pls.py:60` imports `pls_adopt` at top level, `pls_side_effects.py:26` too, so every `pls` command dies with `SyntaxError` on 3.10/3.11. No `sys.version_info` check, no CI matrix. With that one line rewritten (reviewer patch, reverted) the full suite passes on 3.10: **214 run, 0 fail** → true minimum today = 3.12; with a one-line fix = 3.10 (no other 3.11+ API found: static scan for tomllib/StrEnum/Self/ExceptionGroup/batched/Path.walk etc. = none; `datetime.fromisoformat` uses are pre-normalised `Z`). | `py310 -m py_compile` → `pls_adopt.py line 99 SyntaxError: f-string expression part cannot include a backslash` (only file failing; 3.12: all compile). T9: `Ran 14 tests … FAILED (errors=13)`, 13× `ImportError: Failed to import test module … SyntaxError`. Patched: `Ran 214 tests in 54.0s OK` (t9-310-patched.log). | `cd tools/pls && <py310> -m unittest discover -s tests -v` | Replace the f-string at `pls_adopt.py:94` with string concatenation (or precompute `extra_md` before the template); add a startup version guard in `pls.py` with a clear message; run the suite on 3.10 in CI or before each release. Alternatively change setup.md to 3.12+. | T9 = 214 OK on 3.10; `py_compile` clean on 3.10. |
| G2-a | Windows UTF-8 console | Low | PASS (this part) | demo | `pls.py:91-96` reconfigures stdout/stderr to UTF-8 at import. | Reviewer test `ConsoleTest.test_non_cp932_text_prints_on_a_cp932_console` (PYTHONIOENCODING=cp932, prints `—` and 下書き): ok; control without `import pls` fails: ok. | `python -m unittest tests.review_ws5_windows -v` | — | — |
| G2-b | BOM-tolerant JSON | Low | PARTIAL | demo | `utf-8-sig` is used for `rj()` (`pls.py:114`; environments.json, plan.json, exports, `_index.json` via `pls_side_effects.py:206`), connections (`pls_http.py:51,57`), key files (`pls_http.py:88`), `framework.lock` (launcher), `pls_scripts.py:49`. **Not** for gate records: `pls_gate.py:140` reads `gates/*.json` with `utf-8` → hand-edited gate record with BOM raises unhandled `JSONDecodeError` (every command that loads gates). Same plain `utf-8` JSON reads: `pls_kbverify.py:75`, `pls_usage.py:83,137`. No BOM test exists in the suite (grep `ufeff`/`utf-8-sig` in `tests/`: 0 hits) — the plan's "test_pls.py (BOM) [U]" is unconfirmed: there is none. | Reviewer tests: `test_bom_in_environments_json_is_accepted` ok; `test_bom_in_export_file_is_accepted` ok; `test_bom_in_hand_edited_gate_record_is_read` **FAIL**: `JSONDecodeError: Unexpected UTF-8 BOM (decode using utf-8-sig)`. | same | Read every JSON via `rj()`; add one BOM regression test per file kind. | Reviewer BOM test passes. |
| G2-c | CRLF: no false diffs | Low | PASS (with template attributes) | demo | Script bodies written/read with `newline=""` (`pls.py:327,343,1460,1496`); template `templates/project/.gitattributes` sets `config/** releases/** migrations/** -text`. Real git round trip with `core.autocrlf=true`: 0 differences for LF and CRLF bodies. Control without the attributes: LF body becomes CRLF on checkout → 1 difference. **Note:** `pls diff` always exits 0 (`pls.py:2903-2905`), so the existing S7 test `test_pls.py:760 test_script_bodies_keep_crlf` (asserts `diff` rc 0) cannot fail on a CRLF difference — it proves nothing; the CR is also invisible in the diff table (`var a;⏎var b;⏎` on both sides). | Reviewer `GitCrlfTest` 3/3 ok (counts `flat_diff` entries). Debug run: `1 difference(s)… diff rc 0`. | same | Make the S7 test count differences (or give `diff` a non-zero exit on differences); render `\r` visibly in md_diff. | — |
| G2-d | CRLF: no whole-file git changes | Medium | **FAIL** | demo | `wj()` (`pls.py:117-119`) and other `write_text` calls use text mode → OS-native newlines: CRLF on Windows, LF on macOS/Linux. Because `config/** releases/**` are `-text`, these bytes are committed as-is. Every `site.json`/`plan.json` in PLAY BOARD is CRLF (e.g. `config/ad-costs/site.json` 871/871 lines CR, `releases/R-20261108-05/plan.json` 103/103). A developer on another OS (or WSL) re-running `unpack`/`release-plan` rewrites every line → whole-file git changes and merge noise. The framework repo itself has **no** `.gitattributes`; behaviour depends on each clone's `core.autocrlf`. | Reviewer `test_unpack_writes_site_json_with_lf` **FAIL**: `b'{\r\n  "Columns": …'`. `tr -cd '\r'` counts on the PLAY BOARD copy. `ls .gitattributes` in framework: missing. | `pls unpack` on Windows vs Linux, `git diff --stat` | Write JSON/Markdown with `newline="\n"` in `wj()` and the other writers (script bodies stay byte-exact); add a framework `.gitattributes` (`* text=auto eol=lf` + `*.js` policy) ; test bytes of written files. | Reviewer LF test passes; cross-OS unpack gives `git diff` empty. |
| G3 | Stdlib only; tests need no network | Low | **PASS** | demo | AST import scan of `tools/pls/*.py` and `tests/*.py`: no non-stdlib module (only local `test_write_guards`). Node tests import only `node:*`. Fake server binds `127.0.0.1:0` (`tests/test_http.py:119`); unreachable-server tests use `127.0.0.1:9`. Runtime proof without disabling the network: suite run with `socket.connect` / `getaddrinfo` patched to refuse any non-loopback host. | `review_ws5_offline_run.py`: `Ran 214 tests … OK`, `non-loopback attempts: none` (g3-offline.log). | `cd tools/pls && python tests/review_ws5_offline_run.py` | — | — |
| G4 | HTTP transport and browser runner parity, or differences documented | High | **FAIL** | demo | Release/rollback/preflight/bootstrap logic is near-identical, but three behaviour differences are undocumented and silently change results: **(1)** runner `runTests` `exec` without `expectHttp` ignores the HTTP status (`pls-runner.js:65-66`) → HTTP 500 is reported `pass`; HTTP transport fails it (`pls_http.py:286-288`). **(2)** runner ignores `as_key` (spec and step) → a role test runs as the logged-in (usually admin) user and can pass; ADR-0008:25,32 says "same spec format… a release can be planned by one and applied by the other". **(3)** runner `rollbackRelease` (`pls-runner.js:132-140`) has no per-site try/catch: a thrown restore aborts the remaining restores and `applyRelease` throws with no status, leaving earlier sites in the new state; HTTP `rollback` continues (`pls_http.py:199-209`). Guards (role, `allow_write`, G4, side effects, typed confirmation, ops/log, apply-log, plan status) exist only on the HTTP path; runner has none — this part is TB-7 in ADR-0014 (ACCEPTED BOUNDARY only by citation, ADR-0014 Proposed — holds only once Nam accepts it; TB-7 scope "demo, dev only"). HANDOFF.md:86 says *agents* use the runner, while TB-7 assumes "driven by a person". | `node --test tools/pls/tests/review_ws5_runner_parity.mjs`: 3/3 **fail**: `{"status":"pass","log":["exec approve(Id 1) → HTTP 500"]}`; `role test ran as the logged-in user and passed`; `applyRelease threw (network down); calls: …updatesite 201 — site b not restored`. T2 baseline `test_runner.mjs`: 6/6 pass. | as left | Runner: fail `exec` on non-200 when no `expectHttp`; refuse specs/steps with `as_key` (or record `as: session-user`); try/catch per restore and return `rolled-back` with per-site results; add `transport: "browser"` to results. Document remaining differences in ADR-0008. | Parity probes pass; differences table in ADR-0008. |
| G5-a | release-plan on PLAY BOARD (23 sites) fast enough | Low | PASS | demo | Wall times on the copy (PLS_HOME = worktree): release-plan 22 sites, written, 3.4 s (3.0 MB, 68 files); 23 sites refused at slot check after full drift/scope 8.8 s; refused at scope 4.1 s. `lint` ≈ 5.6 s. All acceptable for an interactive CLI. | timings table below; bench/results.json | `python ws5-logs/bench.py <review> 3 [decision]` | — | — |
| G5-b | Token-heavy commands have a `--summary` keeping decision data | Low | PARTIAL | demo | `lint --summary` keeps rule, count, top-5 sites; drops the message (script name, line) — full list one command away (acceptable). `refs --summary` could not be exercised: the project has 0 POSSIBLE numbers left on all 23 sites, so summary output = full + one header line (2035 vs 2014 bytes on `campaigns`); its suppression of non-"other" groups (`pls.py:1435`) is untested on data. `release-plan` has no `--summary`: the refused 23-site run printed 13 KB / 167 lines of `SCOPE` lines. Tests only check exit codes of `lint --summary` (`test_observability.py:47`); no test compares summary vs full content. | bench/lint.txt vs lint_summary.txt (1037 → 154 bytes, same 9 issues, same rules/sites); per-site refs sizes. | as above | Group `SCOPE` lines per site in release-plan refusal (count + names), add content tests for both `--summary` flags. | — |
| G6 | Setup, env vars, local files, recovery documented accurately | Low | PARTIAL (clean-machine run NOT VERIFIABLE) | demo | Static comparison of `docs/setup.md` vs parser/code: commands and options exist (`setup`, `init --approver/--origin/--stage/--target`, `http-check`, `principals`, `version --app`, `kb-verify`, `jobs-verified --by --quote`, `merge-install`, `sandbox create --name --sites --parent`/`refresh`, `bootstrap`, `apply`, `--yes`, `skills check/sync`); `init` does the first git commit (`pls.py:2010-2013`), writes `.pls/connections.json` (`pls.py:1972`); `demo/README.md` exists. Inaccurate/missing: (1) Python 3.10+ (G1). (2) `setup`/`init` set `allow_write: true` automatically (`pls.py:1959,1973`) — setup.md never mentions `allow_write` although CLAUDE.md rule 1 treats it as the operator's opt-in. (3) Env vars `PLS_CONNECTIONS` (`pls_http.py:41`, redirects the connection file incl. `allow_write`), `PLS_PROFILE_DIR` (`pls.py:1905`), `PLS_ACTOR` (`pls_log.py:81`) are documented nowhere in `docs/`/README (only `PLS_HOME`). (4) No recovery section: what to do after `rolled-back`, a failed restore, or an interrupted apply. (5) No line-ending guidance (G2-d). (6) HANDOFF.md:86 still says "54 python tests" (actual 214). | grep results above; parser `pls.py:2501-2640`. | read setup.md vs `pls.py -h` | Add "Local files and environment variables" and "Recovery" sections; state that setup enables writes for dev; fix version. | Clean-machine walkthrough by a person (H). |

## Test runs

| Run | Interpreter | Command | Run | Pass | Fail | Error | Skip | Time |
|---|---|---|---|---|---|---|---|---|
| T1 | Python 3.12.10 | `python -m unittest discover -s tests -v` | 214 | 214 | 0 | 0 | 0 | 56.9 s |
| T9 | Python 3.10.21 | same | 14 (13 modules not importable) | 1 | 0 | 13 | 0 | 0.8 s |
| T9' | Python 3.10.21, `pls_adopt.py:94` rewritten (reverted after) | same | 214 | 214 | 0 | 0 | 0 | 54.0 s |
| G3 | Python 3.12, non-loopback network refused | `python tests/review_ws5_offline_run.py` | 214 | 214 | 0 | 0 | 0 | 54.8 s |
| T2 | node v24.19.0 | `node --test tools/pls/tests/test_runner.mjs` | 6 | 6 | 0 | 0 | 0 | 0.16 s |
| WS5 G2 | Python 3.12 | `python -m unittest tests.review_ws5_windows -v` | 10 | 8 | 2 (BOM gate record; CRLF site.json) | 0 | 0 | 1.1 s |
| WS5 G4 | node | `node --test tools/pls/tests/review_ws5_runner_parity.mjs` | 3 | 0 | 3 (parity differences) | 0 | 0 | <0.1 s |
| py_compile | 3.10 / 3.12 | each `tools/pls/*.py`, `tests/*.py` | — | 3.12 all; 3.10 all but `pls_adopt.py` | 3.10: 1 | — | — | — |

## Timings (PLAY BOARD copy, 23 sites, Windows, Python 3.12, wall clock incl. interpreter start)

| Command | Runs (s) | rc | Output |
|---|---|---|---|
| `lint` | 7.94, 5.56, 5.63 | 1 (9 issues) | 1037 B, 10 lines |
| `lint --summary` | 5.60, 5.71, 5.68 | 1 | 154 B, 4 lines |
| `refs --site campaigns` (largest site.json) | 1.21, 1.18, 1.19 | 0 | 2014 B, 16 lines |
| `refs --site campaigns --summary` | 1.19, 1.18, 1.20 | 0 | 2035 B, 17 lines |
| `release-plan --env dev --release REVIEW-PERF-1` 23 exports, no decision | 4.14 | 1 (scope refusal, ADR-0001) | 13 KB, 167 lines |
| same + `--accept-unverified ops/decisions/2026-11-08-accept-unverified-copies.md` | 8.79 | 1 (slot check A2: `campaigns` DateB label vs ledger) | 219 B |
| same, 22 sites (without `campaigns`) | 3.38 | 0 — plan written, 0 changes, config-only | 501 B; `releases/REVIEW-PERF-1/` 68 files, 3.0 MB |

Exports used: latest-modified `dev-<site>-*.json` per site from the copy's `.pls/exports` (167 files). `--summary` saves nothing for lint time (the work is the same; only output shrinks).

## HTTP transport vs browser runner

| Aspect | `pls_http.py` (+ `pls.py`) | `pls-runner.js` | Same? |
|---|---|---|---|
| Write guards (role dev/stg, `allow_write`, G4 for stg, side effects, jobs, typed confirmation) | `assert_writable` 90; `pls.py` apply/bootstrap path | none (header comment only) | No — TB-7 (ADR-0014 Proposed) |
| Payload completeness (Title/ReferenceType/SiteSettings) | `Client.apply` 141-146 | `apply` 31-35 | Yes |
| Missing payload/rollback files → refused before any call | 175-177 | 120-125 | Yes |
| Preflight `UpdatedTime` before any write | 178-183 | 126-131 | Yes (runner throws on getsite ≠ 200; HTTP raises `TransportError`) |
| Failing site included in restore, reverse order | 184-193 | 132-145 | Yes |
| One failing restore does not stop the others | try/except per site 203-207 | no catch: aborts, `applyRelease` throws, no status | **No** (probe 3) |
| Restore result inspected for status | no (status `rolled-back` even if restores fail) | no | Same gap (C8, other WS) |
| Final status | `applied-unverified`, then `pls` writes apply-log, plan status, ops/log, mark-applied | returns JSON only; person must save and run `mark-applied` | Records differ (documented only as "fallback") |
| Request timeout | `conn_timeout` 1-600 s | none | No |
| `runTests` `exec` without `expectHttp` | fails on ≠ 200 | ignores status → `pass` | **No** (probe 1) |
| `as_key` per spec/step | honoured | ignored, runs as session user | **No** (probe 2) |
| `editPage` | `pass-api-only` (documented ADR-0008:36) | real DOM check | Documented |
| Numeric compare 1.0 vs 1, key order | float compare, `sort_keys` | `JSON.stringify` (insertion order) | Minor difference |
| Unexpected exception in a test | only `TransportError` caught (others crash the run) | any error → `error` | Different |
| Result fields | `as`, `transport: "http"` | `executed_at`; no `transport`, no `as` | Different |
| Bootstrap id | `Id` | `Id` or `Response.Id` | Minor |
| Backup | no `taken_at` | `taken_at` | Minor |
| `bulkUpsert` (migrations) | `Client.bulk_upsert` exists; no CLI command found in parser | only executable path | Runner-only write (B3/C1) |

## Skipped / not done

- G6 clean-machine walkthrough: NOT VERIFIABLE (no clean machine). Static comparison only.
- Network was not disabled (not authorized); replaced by a socket-level loopback-only guard during the run.
- `refs --summary` on data with POSSIBLE numbers: none exist in the copy; not exercised.
- No real Pleasanter contact; no secrets or environment-variable values read.
- Benchmark repeated once for release-plan (writes a release folder); 3 runs for read-only commands.

## Notes for other workstreams

- **C1 / A6:** `PLS_CONNECTIONS` (`pls_http.py:41`) lets any process point `pls` at another connection file (its own `allow_write: true`) — undocumented; check it in the C1 bypass matrix. `setup`/`init` write `allow_write: true` by default (`pls.py:1959,1973`).
- **H3 / C-tests:** `test_pls.py:760 test_script_bodies_keep_crlf` asserts `pls diff` rc 0, but `diff` always returns 0 (`pls.py:2903-2905`); the test cannot detect a CRLF regression.
- **C3:** BOM in `gates/*.json` → unhandled `JSONDecodeError` traceback (`pls_gate.py:140`), not a refusal.
- **C8 / C11:** both transports return `rolled-back` without checking restore HTTP status.
- **B3 / C1:** runner is the only executable `bulkupsert` path; HANDOFF.md:86 says agents use the runner (contradicts TB-7 "driven by a person").
- **E/B (release ids):** `release-plan --release REVIEW-PERF-1` accepted (no `R-` format check) — harmless here, mention if ids are parsed elsewhere (`apply R-…`).
- **A3:** HANDOFF.md:86 "54 python tests" stale (214).
- Side effects of this WS: copy `copies-ws5/pls-onboard-playboard-r2` now has `releases/REVIEW-PERF-1/` and new `ops/log` lines; worktree has 3 untracked `review_ws5_*` files; `pls_adopt.py` patch was reverted (`git status`: only the 3 review files).

## Unresolved questions

- Should the minimum be raised to 3.12 in docs, or the one-line fix made (cheaper, keeps 3.10)? Decision for Nam.
- Is the browser runner still expected to be used by agents (HANDOFF) or only by a person (TB-7)?
