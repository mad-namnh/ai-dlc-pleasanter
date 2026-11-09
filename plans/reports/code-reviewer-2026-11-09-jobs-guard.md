# Code review — scheduled-job (jobs) safety guard, `tools/pls` (uncommitted, 2026-11-09)

## Scope
- Files: `pls_side_effects.py` (+130), `pls.py` (+53: lint, `last_applied_jobs`, `release_plan`, `http_cmd` apply/test), `pls_report.py` (+3), `tests/test_side_effects.py` (+99), `tests/test_pls.py` (+25)
- Intent checked against ADR-0010 Decision §2 / "Jobs guard" note and ADR-0012 Decision 1, 3, 4; ADR-0011 sandbox section
- Tests: `python -m unittest discover -s tests` → `Ran 194 tests ... OK` (verified)
- Ad-hoc probes (scratchpad, no repo edits, no server contact): non-UTF-8 index, whitespace names, directory named `*.js`, malformed `plan.jobs.changed`, malformed baseline fingerprints

## Overall
Matches the intended behaviour for the main env flows. Read-only specs are not blocked; writing specs are refused on `unknown`, warned on `live`; a bad index refuses the plan and writes nothing (check runs before the `failed` gate, `pls.py:933-942`); a plan from before the check is refused unless `disabled`; mail and jobs refusals are combined, so both reasons show. Non-UTF-8 `_index.json` does not crash: `UnicodeDecodeError` is a `ValueError`, so all callers catch it (verified). The real gap is sandboxes. Second: the baseline assumes the manual deploy step was done.

## Critical
None.

## High

**H1. Sandbox env uses a stale copy of `side_effects`, but jobs are tenant-wide → writing tests can pass while dev's jobs state is `unknown`/`live`.**
`sandbox_create` copies `side_effects` from the base once (`pls.py:1432-1434`). `http_cmd test` and `apply` read the sandbox's own copy (`pls.py:2111-2113`, `2010-2011`). A sandbox shares dev's connection and tenant (ADR-0011), and a scheduled script runs tenant-wide (ADR-0010 note). Suppose dev was `disabled` when the sandbox was made, and a person later sets dev to `unknown` or `live`. The sandbox still says `disabled`, so writing tests in `dev-<name>` pass with no refusal and no warning. The same applies to mail, because SMTP is per server (that part was there before this change). It also works the other way: a sandbox created while dev was `unknown` stays blocked after dev is set. The person is then tempted to set the sandbox by hand, and the copies drift apart.
Fix: when `e.get("sandbox_of")`, compute the effective state from the base env, or take the more cautious of the base and the sandbox for each key (unknown > live > disabled for jobs). Do this in one helper used by test, apply, release-plan notes and `http-check describe`. Add a test: base `unknown` + sandbox `disabled` → writing test refused.

**H2. Sandbox release-plan tells a developer to deploy their branch's jobs to the shared dev tenant.**
`release_plan` computes `jobs_changed` against `last_applied_jobs(r, env)` for the sandbox env (`pls.py:989`). A new sandbox has no applied release, so the first `sandbox refresh` lists every job as "added". `manual_job_step` then says "On dev-<name>, tenant management → サーバスクリプト: … copy each body" (`pls_side_effects.py:289-296`). That tenant is dev's, and the change reaches dev and every other sandbox. That breaks the ADR-0011 rule that a sandbox deploys only its own copies. And with the copied `unknown`, every sandbox apply is refused until someone edits the sandbox's `side_effects`, which leads to H1.
Fix (pick one, possibly an ADR line): for `sandbox_of` envs, record `plan.jobs` with `changed: []` / `deploy: null` and a note that tenant settings are deployed only via the base env. Or compute against the base env's baseline and refuse with "deploy jobs through <base>". Add a test either way.

## Medium

**M1. Baseline assumes the manual step was done; nothing records that it was.**
`last_applied_jobs` (`pls.py:721-732`) takes the fingerprints of the last release with status `applied`/`applied-differs`. `mark-applied` sets that status after checking the sites only (`pls.py:2689`, `2683`). If the operator skips or botches the manual copy, the next plan reports `changed: []`, and the difference between git and the tenant is never shown again. ADR-0012 Decision (option B) requires "a person's verification step, recorded in the release", and the step text says "records the check in the release", but there is no field or command for it. Suggestion: add `plan.jobs.verified_by/at`, set by a person-run command or a `mark-applied --jobs-verified "<who>"` flag. Count only releases whose job changes are verified (or that had none) as the baseline. Until then, document the limitation in `docs/tech-debt.md`.

**M2. Apply does not check that git still matches the planned fingerprints.**
Apply computes `declared_jobs(r)` (`pls.py:2015-2016`) but uses it only as a bool. The manual step says "copy each body from git", so the operator copies the git state at apply time. That can differ from `plan.jobs.fingerprints`, and the baseline then records something that was not deployed. If git gained a job change after a `changed: []` plan, apply with `jobs: unknown` passes (although nothing is deployed). Fix: refuse when `SE.declared_jobs(r) != pj["fingerprints"]` and `pj` has fingerprints ("stale plan: scheduled scripts changed since planning — plan a new release"). The check is cheap, and the value is already computed.

**M3. Per-environment values are not in the fingerprint, and the manual step copies bodies without resolving references.**
ADR-0012 Decision 1 says the index holds per-environment values via `${env:x}`, and bodies use `${site:x}`/`${principal:x}`. `declared_jobs` hashes the raw git bytes (`pls_side_effects.py:235-247`). A change of `envs.<e>.values.x` or of a site id therefore never shows as a job change. The step tells the operator to copy `<name>.js` as is, so unresolved `${site:x}` placeholders would reach the tenant. No renderer exists (grep for `_tenant`/`scheduled` in `pls.py` finds only the guard). Suggestion: render each body and entry per env (reuse the payload resolution) and fingerprint the rendered text, or write the rendered bodies into `releases/<id>/jobs/` for the operator to copy. At minimum, say in the step that references must be resolved, and log it as tech debt.

**M4. Bad `plan.jobs.changed` types fail open or crash (probe-verified).**
`jobs_apply_refusal` (`pls_side_effects.py:268-283`) assumes a list:
- `"nightly added"` (a string) → warning text joined one character at a time;
- `5` → `TypeError` traceback from `"; ".join`;
- `""`, `0`, `{}`, `false` → treated as "no changes", so apply passes.
A malformed `fingerprints` list in an applied plan crashes `changed_jobs` (`before[n]` → `TypeError`, verified), so every later release-plan of that env fails. A non-string `manual_step` would crash the `"\n".join` at `pls.py:2022`. `plan.json` is tool-written, so this needs a hand edit, which makes the severity medium/low. Still, the guard should fail closed. In apply, if `"changed" in pj` and it is not a `list[str]`, treat it as `None` (unknown → refuse unless `disabled`). In `last_applied_jobs`, skip plans whose fingerprints are not a `dict[str,str]`.

## Low
- **L1.** The jobs check in `test` runs after the mail check (`pls.py:2128` vs `2114-2127`). The mail check calls `export_site` on the server for each written site. Moving the offline jobs refusal first avoids network calls that would be refused anyway.
- **L2.** Index names are not normalised: `" nightly"` and `nightly.js` count as two jobs (probe). Lint reports both, so it fails safe. Consider rejecting names that are not `SAFE_NAME`-like, so they also stay valid as file stems on Windows, which is case-insensitive.
- **L3.** A directory named `x.js` in the jobs dir → `PermissionError` (Windows) from `read_bytes`, uncaught in apply/test/release-plan (probe). Filter with `p.is_file()`.
- **L4.** `operator_report` puts job names into a markdown table cell without escaping (`pls_report.py:35-36`); a `|` in a name breaks the table. L2 fixes this as well.
- **L5.** `last_applied_jobs` reads every `releases/*/plan.json` on each plan, the same as `releases_for`. Fine at the current scale. A broken `plan.json` anywhere aborts release-plan (`rj` raises); this predates the change.
- **L6.** The manual step is printed before the confirmation and before the HTTP apply. If the site apply is rolled back (`pls_http.py:197`), the operator may already have deployed the jobs. The baseline is then not updated (the plan stays `planned`), so the next plan lists the jobs again. Fails safe, but consider printing "after the sites are applied" in the step.
- **L7.** L-JOB-01 covers layout only. ADR-0012 Decision 2 also requires L-REF-01, L-SEC-01, the top-level `const`/`let` rule and `node --check` on bodies. Not in this change's stated scope; follow-up.

## Baseline selection (verified)
Correct for: same env only; `applied` and `applied-differs`; ordering by `_applied_key` (offset-aware) then release id; adoption records and old plans skipped (no `fingerprints`). A plan without `applied_at` sorts as oldest. A newer applied release without a jobs record (from before the check) is passed over in favour of an older one with fingerprints, which is acceptable: older releases deployed no jobs through pls. If none is found, every job counts as "added" (safe side).

## Safe-side gaps summary
- The sandbox paths (H1, H2) are the only places where a writing test or a job-changing release gets through while the real tenant's jobs state is `unknown`.
- Hand-edited `plan.jobs.changed` set to a falsy non-list (M4).
- `changed: []` plan + git changed afterwards + `unknown` → apply passes (M2). No jobs are deployed, but the baseline is wrong.
- Writes outside `test` and `apply`: `bootstrap` (creates empty sites) and `kb-verify` (dev only, probe sites) have no jobs check. ADR-0010 §2 mentions bootstrap only for releases that change jobs, which bootstrap plans never do. Acceptable; flagged for awareness.

## Test gaps
- No sandbox test (H1/H2).
- No integration test for `last_applied_jobs` with several applied releases, another env's release, `applied-differs`, or a newer release without a jobs record next to an older one with fingerprints.
- No integration test that apply with `changed: []` + `unknown` passes, that apply with `live` prints the warning and the manual step, or that the manual step appears in the confirmation text.
- No test that `release-plan` prints the `jobs is 'unknown'` note.
- No `pls lint` integration test for L-JOB-01 (only `job_problems` unit tests).
- No test for a mixed run (a read-only spec plus a writing spec → refused) or for an exec-only spec.
- No test for a malformed `plan.jobs` (M4) or a non-UTF-8 index.
- `set_effects` in tests replaces the whole `side_effects` dict (mail becomes `unknown`). This works with the fake, but it hides how the mail and jobs guards interact.

## Positive
- Pure functions, with the IO wiring kept in `pls.py`. Refusal texts name the env, the field and the person's action, in the same style as the mail guard.
- Bodies are hashed byte for byte, which `.gitattributes` makes safe. An entry without a body, or a body without an entry, still counts.
- The bad-index check runs before anything is written. The old-plan case (`"changed" not in pj`) is handled conservatively. Declared jobs are re-read at apply, so a project that gained jobs after an old plan is caught.

## Recommended actions
1. H1: effective side effects for sandboxes come from the base env (or the more cautious of both); add a test.
2. H2: sandbox releases do not plan tenant job deploys; add an ADR-0011/0012 line and a test.
3. M2: apply refuses when the current fingerprints differ from the plan's.
4. M4: validate the `plan.jobs` shape and fail closed; validate the baseline fingerprints.
5. M1/M3: record the person's verification and render bodies per env, or log both in `docs/tech-debt.md` with a deadline.
6. Fill the test gaps listed above.

## Metrics
- Tests: 194 OK
- Type/lint: not run (no configured linter for `tools/pls`)

## Unresolved questions
- Sandboxes: should the jobs state come from the base, or should a sandbox be refused from any tenant-level deploy? This is a design decision, maybe for ADR-0011 or ADR-0012.
- Is there a renderer planned for `${env:x}` and `${site:x}` in scheduled-script bodies, or does the operator resolve them by hand?

**Status:** DONE_WITH_CONCERNS
**Summary:** The guard is correct for the normal env flows and all 194 tests pass. Sandboxes bypass or misdirect it (H1, H2), and the baseline trusts an unrecorded manual step and stale git (M1, M2).
**Concerns/Blockers:** H1 and H2 need a design decision on sandboxes and the tenant.

## Resolution (2026-11-09)

Status is "done" only where a test proves it. Paths are under `tools/pls/`; tests run with `python -m unittest discover -s tools/pls/tests` (214 OK) and `node --test tools/pls/tests/test_runner.mjs` (6 pass). "At start" = state found when this resolution began (after commit 661c578).

| Finding | At start | Now | Evidence (code → test) |
|---|---|---|---|
| H1 sandbox uses stale `side_effects` | partial (code, unit test only) | **done** | `pls.py:835` `env_effects`, `pls_side_effects.py:56` `cautious`; used by test/apply/release-plan/http-check → `tests/test_side_effects.py:418`, `tests/test_sandbox_merge.py:161` (base set to `unknown` after the sandbox copied `disabled` → writing test refused, nothing written) |
| H2 sandbox plan tells to deploy jobs on the shared tenant | partial (code, no test) | **done** | `pls.py:1099` sandbox records `changed: []`, no manual step, no files; ADR-0011 "Safety: resources shared with the base environment" → `tests/test_sandbox_merge.py:161` |
| M1 manual deploy never recorded | done | **done** (extended) | `pls.py:775` baseline skips unverified job changes; `pls.py:804` `jobs-verified`; `pls_gate.py:97,116` Operators / G4 → `tests/test_pls.py:349`, `:392`, `:128` |
| M2 apply does not check git vs plan | done | **done** | `pls.py:2148` → `tests/test_side_effects.py:398` |
| M3 per-env values / unresolved references | done | **done** | `pls.py:830` `rendered_jobs`, `pls_side_effects.py:244,265`; resolved files `pls.py:1109` → `tests/test_pls.py:349` (body resolved to stg id 202), `tests/test_side_effects.py:101` |
| M4 malformed `plan.jobs` fails open / crashes | partial (`manual_step` type unchecked, baseline skip untested) | **done** | `pls_side_effects.py:347` `bad_plan_jobs` (changed, fingerprints, manual_step); `pls.py:2141` apply refuses; `pls.py:775` baseline skips → `tests/test_side_effects.py:406`, `:82`, `tests/test_pls.py:128` |
| L1 jobs check after the network mail check | partial (reordered, untested) | **done** | `pls.py:2253` → `tests/test_side_effects.py:289` (no server call at all) |
| L2 names not normalised | open | **done** | `pls_side_effects.py:216` names must match `SAFE_NAME` (also body file stems, L-JOB-01) → `tests/test_side_effects.py:82`, `tests/test_pls.py:109` |
| L3 directory named `*.js` | done | **done** | `pls_side_effects.py:225` `is_file()` → `tests/test_side_effects.py:101` |
| L4 `|` breaks the report table | partial (escaped, untested) | **done** | `pls_report.py:36` → `tests/test_side_effects.py:94` |
| L5 every plan read; one broken plan stops release-plan | open (pre-existing) | **kept, TD-15 (a)** | `docs/tech-debt.md` TD-15 with deadline |
| L6 manual step printed before the apply | open | **done** | `pls.py:2155` confirmation only announces it; `pls.py:2177` printed after a successful apply → `tests/test_side_effects.py:330`, `:347` (rollback: not printed) |
| L7 body lint (ADR-0012 decision 2) | open | **done** | `pls.py:519` `lint_jobs`: L-REF-01, L-SEC-01, L-SCR-01 (shared), L-SCR-02 on bodies resolved per non-sandbox env, L-REF-02 for unresolved references → `tests/test_pls.py:109`, `:147` (+ no-node warning test) |
| Safe-side note: `bootstrap` / `kb-verify` have no jobs check | open (accepted in review) | **kept, TD-15 (c)** | rationale and deadline in TD-15 |

### Test gaps

| Gap | Now | Test |
|---|---|---|
| Sandbox cases | done | `tests/test_sandbox_merge.py:161`, `tests/test_side_effects.py:418` |
| Baseline across releases (other env, `applied-differs`, newer release without a jobs record, broken record, unverified) | done | `tests/test_pls.py:128` |
| Apply with `changed: []` + `unknown`; `live` warning; manual step in the confirmation | done | `tests/test_side_effects.py:323`, `:330` |
| `jobs is 'unknown'` note of release-plan | done | `tests/test_pls.py:349` |
| L-JOB-01 through `pls lint` | done | `tests/test_pls.py:124`, `:109` |
| Mixed read-only + writing specs; exec-only spec | done | `tests/test_side_effects.py:311` |
| Malformed `plan.jobs`; non-UTF-8 index | done | `tests/test_side_effects.py:406`, `:82` |
| `set_effects` replaced the whole dict | done | helper now merges; `tests/test_side_effects.py:297` checks each guard on its own |

### Decisions taken (were "Unresolved questions")
- Sandboxes never configure tenant-level resources; their effective mail/jobs state is the riskier of their copy and the base's current value (ADR-0011 Safety, 2026-11-09).
- References in scheduled-script bodies are resolved by `pls` per environment (`releases/<R>/scheduled-scripts/`), not by hand (ADR-0012 implementation notes).
- Who confirms the manual deploy: an operator of the release's environment (profile row `Operators`) or a G4 approver; older profiles: G4 only (ADR-0012 implementation notes).
