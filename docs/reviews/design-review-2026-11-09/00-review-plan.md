# Evidence-driven design review plan — ai-dlc-pleasanter

Plan only. No review has been executed. Prepared 2026-11-09 against branch `brownfield-adr` @ `782116b` (clean except untracked `docs/review-criteria.md`).

**Standard:** `docs/review-criteria.md` v2.1 (66 criteria, groups A–J). Notes on the request:
- The request names sections "A–K"; the standard has **A–J** (no K). Every A–J criterion is planned; nothing was invented for K.
- `docs/design-review-standard-v2.md` **does not exist**. The report format used is `docs/review-criteria.md` §5 (finding table) and §6 (final report). → Human decision H-1: confirm, or supply the missing file.
- `docs/review-criteria.md` is **untracked** in git. → H-2: commit it (or name the authoritative copy) before the review starts, so findings cite a stable version.

Legend used throughout: **[F]** confirmed fact (inspected during planning, with location) · **[H]** hypothesis to verify · **[U]** unknown · **[D]** human decision required.

---

## Deliverable 1 — Executive review plan

**Objectives.** Establish, per stage (`demo`, `cstg`, `prod`), whether the framework is consistent with its ADRs, refuses unauthorized and production writes, keeps human approvals human, recovers from partial failures, is deterministic and auditable, and is portable — using implementation and test evidence only (standard §1, §7).

**Scope.** `tools/pls/*.py` (16 modules, `pls.py` 2 989 lines), `tools/pls/browser/pls-runner.js`, `tools/pls/tests/` (15 Python files + `test_runner.mjs`; 214 + 6 tests at planning time), `skills/` (11 skills), `docs/adr/0001–0013`, `docs/architecture.md`, `docs/plan.md`, `docs/tech-debt.md`, `docs/review-findings.md`, `templates/project/`, `evals/`, `plans/reports/`, `docs/reviews/`, `docs/slices/`. Read-only copies of sibling project repositories for F-method checks (`demo-equipment`, `pls-onboard-playboard-r2`, `pls-adopt-797`). Out of scope: `patterns/ai-gateway` (parked, separate infra) except A5; `spike/` except its own write guard (`spike/round-trip/scripts/common.py:59`) as an extra write path for B3.

**Major risks identified during planning (all [H] until verified):**
1. **Approval authenticity rests on file-system trust.** `gates/*.json`, `plan.jobs.verified`, `CLAUDE.md` (Approvers/Operators), `environments.json` (`role`) and `.pls/connections.json` (`allow_write`) are plain files the agent can write. `GT.require` checks only that the recorded approver name is in the profile (`tools/pls/pls_gate.py:181-188`). No ADR names this trust boundary yet (A6/B4/D5).
2. **G4 is bound to a release id, not to content** (`pls_gate.py:181`; no payload digest in the gate record) → B10 likely FAIL (stage cstg).
3. **Rollback status does not reflect restore success.** `apply_release` returns `"rolled-back"` before/independent of restore results (`tools/pls/pls_http.py:196-197`, `rollback` 201-211 returns log lines only) → C8/C11.
4. **Timeout after a server-side write.** `Client.call` converts `URLError` to `TransportError`; a read timeout may surface as `TimeoutError`/`socket.timeout` not caught by `apply_release` (`pls_http.py:119-135`, 190-195) → C10, possibly C6.
5. **Browser runner writes without a code guard** (`tools/pls/browser/pls-runner.js:33,54,66,174,198`; header comment line 3 is the only control) and is the only `bulkupsert` (migration) path → B3/C1/G4.
6. **Run-log failures are swallowed** (`tools/pls/pls_log.py:122` "a log line is never worth a failed command") → D6 policy must be stated in ADR-0013 or it is a FAIL at cstg.
7. **Documented minimum runtime 3.10** (`docs/setup.md:15`) vs 3.12 syntax (known finding in the standard, G1). Only Python 3.12 is installed on the planning machine (`py -0`).
8. **No production runner exists** (ADR-0003 Proposed, option C) → J1–J3 largely NOT VERIFIABLE/FAIL for `prod`.

**Recommended execution order.** WS-2 (security, priority set) → WS-3 → WS-1 → WS-4 → WS-6 → WS-5 → WS-7. WS-1, WS-4, WS-5 (static parts) and WS-6 can run in parallel with WS-2/WS-3 because they are read-only; all F-method runs happen on **one** copy per reviewer (§9 isolation rules). The standard's batches map as: batch 1 = WS-1 + WS-2(B), batch 2 = WS-3 + WS-4(E) + D, batch 3 = WS-4(F) + WS-5 + H, batch 4 = WS-6 + J + WS-7.

**Estimated effort.** ≈ 34–44 reviewer-hours (table in Deliverable 3), plus ≈ 2 h of a person for method-L runs on dev and decisions.

**Required human participation.** H-1/H-2 above; H-3 authorize installing Python 3.10 (or 3.11) in an isolated venv/location for G1; H-4 run the method-L scenarios on MADLAB dev (B1, J1 and any live confirmation); H-5 confirm which sibling project copies may be used and that `ops/log` files created by running `pls` in a copy are acceptable; H-6 answer the trust-boundary question for A6 (which boundaries are accepted, owned by whom) — or accept that missing ADRs are reported as FAIL; H-7 approve this plan.

**Safety constraints for the review.** Follow standard §7. In addition: run every command that writes files only inside a disposable copy under the reviewer's scratch directory (`git worktree add <scratch>/fw <commit>` for the framework; `robocopy`/`cp -r` for projects, excluding `.pls/`); never copy `.pls/` (keys, connections) into a copy; tests already isolate `PLS_PROFILE_DIR` (`tests/test_pls.py:36`) — keep that; do not run `apply`, `bootstrap`, `test`, `kb-verify`, `backup`, `principals`, `http-check`, `export`, `adopt`, `harvest`, `version`, `sandbox` against any real URL (fake server only); never print environment variables (keys live there: `pls_http.py:74` `resolve_key`).

---

## Deliverable A — Repository inventory

| Area | Location | Components | Review relevance | Inspection status |
|---|---|---|---|---|
| CLI | `tools/pls/pls.py` | 44 subcommands (parser 2495–2650, dispatch `_main` 2498→, `http_cmd` 2049→) | Every criterion in B, C, E | Planned: targeted ranges listed in Deliverable B |
| HTTP transport | `tools/pls/pls_http.py` | `WRITABLE_ROLES` 31, `load_connection` 45, `resolve_key` 74, `assert_writable` 92, `Client` 110 (`call`, `export_site`, `apply`, `create_site`, `backup_records`, `bulk_upsert`), `apply_release` 177, `rollback` 201, `bootstrap` 214, `run_tests` 266 | B3, C1, C6, C8–C11 | Partly read during planning |
| Gates / profile | `tools/pls/pls_gate.py` | `approvers` 33, `_approver_for` 78, `operators` 97, `job_verifier` 116, `record`, `latest`, `require` 181, `require_onboarding` 209, `lint` (L-GATE-01, L-ONB-01) | B4, B10, D1, D2, D5 | Partly read |
| Side effects / jobs | `tools/pls/pls_side_effects.py` | `effects`, `cautious` 56, mail guards, jobs layout/fingerprints/refusals, `bad_plan_jobs` 347 | C2, C3, C7, E4 | Read (authored this session — reviewer must re-inspect independently) |
| Observability | `tools/pls/pls_log.py`, `pls_usage.py` | `append` 105 (swallows errors 122), `run` 126, `step` 168 | D4, D6, I4 | Partly read |
| Brownfield | `pls_adopt.py`, `pls_compare.py`, `pls_scope.py`, `pls_version.py`, `pls_kbverify.py`, `pls_merge.py`, `pls_scripts.py`, `pls_spec.py`, `pls_report.py` | adopt, env-compare, scope refusal, version, kb probes, merge driver, script refs/lint, spec skeleton, operator report | A2, B3 (kb-verify), E2, E4, F3, G1 | Not read |
| Browser runner | `tools/pls/browser/pls-runner.js` | `apply`, `runTests`, `applyRelease`, `rollbackRelease`, `bootstrapSites`, `backupRecords`, `bulkUpsert` (export 202) | B3, C1, G4 | Grep only |
| Canonical defaults | `tools/pls/canonical-defaults.json` | defaults table | E2, F1 | Not read |
| Tests | `tools/pls/tests/*.py`, `test_runner.mjs` | fake server `test_http.py:20` (`Fake`: `fail_update_on`, `drop_on_save`, `fail_restore_on`), write-path inventory `test_write_guards.py` (`WRITES`, `NETWORK_READS`, `LOCAL` 24–28; `test_prod_is_never_written` 147) | H1–H5, all F-method | Partly read |
| Skills | `skills/*/SKILL.md` (+ `references/`) | 11 skills; KB `skills/pls-kb-pleasanter/references/{api,behaviours,schema,skeletons}.md`, `probes/` | B5, B6, F1, F2, I1–I6 | Not read in full |
| ADRs | `docs/adr/0000–0013`, `README.md` | statuses: 0004, 0006, 0012 Accepted; others Proposed | A2, A3, A6 | Headers read |
| Architecture | `docs/architecture.md` (§2 invariants I1–I9 lines 18–32; §7 commands/lint 258–316), `docs/plan.md`, `docs/setup.md`, `README.md`, `HANDOFF.md` | source of truth for INV mapping | A1, A4, G6 | Partly read |
| Debt / findings | `docs/tech-debt.md` (TD-01…TD-15), `docs/review-findings.md` (34 table rows), `docs/reviews/*`, `docs/slices/*`, `plans/reports/code-reviewer-2026-11-09-jobs-guard.md` | prior findings | B9, H3, H4, J4 | Not read in full |
| Templates | `templates/project/` (`CLAUDE.md` profile, `.gitignore`, `.gitattributes`, `environments.json`, `connections.example.json`, `design/slot-ledger.json`, `requirements/index.md`, `traceability.json`) | profile rows Origin/Stage/Approvers/Operators/Role tests | A5, B7, G2, I2, J5 | Profile and `.gitignore` read |
| Evals | `evals/<skill>/case-*/{input,expected}.md`, `evals/results/<skill>/*` | 15 cases, manual grading (`evals/README.md`); `pls-p5-release-manager` has a case but **no result file** [F] | H6, appendix EV-01…EV-10 | Listed |
| Production runner | — | **none in repo** [F]; ADR-0003 Proposed (option C: package + manual import) | J1–J3 | Confirmed absent |
| Spike tools | `spike/round-trip/scripts/*.py` | own `assert_writable` (`common.py:59`, localhost exemption) | B3 (extra write path) | Grep only |
| Patterns | `patterns/ai-gateway/` | Terraform, Lambda, IAM | A5 only | Not read |
| Project repos (siblings, read-only copies) | `../demo-equipment`, `../pls-onboard-playboard-r2` (23 sites), `../pls-adopt-797` | real `releases/`, `gates/`, `ops/log/` | B1, B7, B8, D3, D4, G5, I3 | `lint --summary` / `skills check` run once (read-only) |

## Deliverable B — Execution entry-point map

Entry: `pls.py main` 2492 → `pls_log.run` (logs every command) → `_main` 2498 → argparse → branch. HTTP commands go through `http_cmd` (2049→). Locations below are at `782116b`; the reviewer re-anchors with `grep -n 'a.cmd == "<name>"' tools/pls/pls.py`.

| Command | Class (`test_write_guards.py:24-28`) | Internal path | HTTP / FS operations | Guards (order as coded) | Audit record | Tests |
|---|---|---|---|---|---|---|
| `apply` | WRITES | `http_cmd` 2113 → `H.apply_release` → `H.rollback` → `mark-applied` | getsite ×N (preflight), updatesite ×N, restore updatesite; writes `apply-log.json`, plan status | plan exists → `status == planned` → `_client`/`load_connection` (alias rule 55-66) → `assert_writable` 2120 → G4 if role ≠ dev 2121-2123 → site-id ownership loop → `env_effects` → mail refusal → jobs refusal (bad record, git≠plan fingerprints) → `_confirm` 2161 → preflight UpdatedTime (in `apply_release`) → writes → read-back via `mark-applied` | `apply-log.json`, plan `status`/`applied_at`, `ops/log` | `test_http.py`, `test_side_effects.py`, `test_write_guards.py`, `test_sandbox_merge.py`, `test_gate.py` |
| `bootstrap` | WRITES | `http_cmd` 2182 → `H.bootstrap` → `bind` | createsite ×N | `assert_writable` 2194 → G4 if role ≠ dev 2195 → `_confirm` 2200 → parent reachable | `bootstrap.json` status/created, `ops/log` | `test_http.py`, `test_write_guards.py` |
| `test` | WRITES | `http_cmd` 2210 → `H.run_tests` | create/update/delete/exec records; getsite for mail check | `assert_writable` 2220 → duplicate-key refusal → sandbox shared-site refusal → `env_effects` → jobs refusal (offline) → mail refusal (getsite) | `tests/results/*.json`, `ops/log` | `test_http.py`, `test_side_effects.py` |
| `kb-verify` | WRITES | `http_cmd` 2290 → `pls_kbverify` | createsite/updatesite probe sites, records | dev only + probe folder + `assert_writable` 2305 + `_confirm` 2314 | report under `ops/`? [U] | `test_kbverify.py`, `test_write_guards.py` |
| `backup` | NETWORK_READS | `http_cmd` 2476 → `Client.backup_records` | record export → `migrations/<dir>/backup/` (business data, gitignored) | [U] read guard; `.gitignore` covers backups | files | [U] |
| `export`, `http-check`, `version`, `principals`, `adopt`, `adopt-package`(local), `harvest`, `sandbox` | NETWORK_READS (adopt-package: local file) | `http_cmd` / `_main` | getsite / users / groups; write local files only | `test_network_read_commands_never_write` 157 | `ops/log` | `test_write_guards.py`, `test_adopt.py`, `test_sandbox_merge.py`, `test_version.py` |
| `release-plan`, `bootstrap-plan`, `plan` | LOCAL | `release_plan` ~1020, `bootstrap_plan` ~1680 | writes `releases/<R>/` (payload, rollback, plan, reports, scheduled-scripts) | onboarding → G3 if role ≠ dev → drift/slots/scope/migration → jobs layout | plan.json | `test_pls.py`, `test_scope.py`, `test_side_effects.py` |
| `mark-applied` | LOCAL | ~2700 | compares export vs payload; writes status `applied`/`applied-differs`, live baseline | 0 differences or `applied-differs` | plan.json | `test_pls.py`, `test_http.py` |
| `gate`, `jobs-verified` | LOCAL | `GT.record` / `jobs_verified` 804 → `GT.job_verifier` | writes `gates/*.json` (open "x") / plan.json | onboarding (gate) → approver/operator name in profile → non-empty quote | the record itself | `test_gate.py`, `test_pls.py` |
| `init`, `setup`, `skills sync` | LOCAL | `init_project` ~1816, `setup_profile`, `sync_skills` | writes project tree, `~/.pls/profiles/` (setup asks for key → hidden key file) | refuses over existing project | git first commit | `test_pls.py` |
| others (`unpack`, `pack`, `canon`, `diff`, `drift`, `classify`, `slots`, `lint`, `coverage`, `refs`, `xref`, `env-compare`, `merge-site`, `merge-install`, `spec-skeleton`, `usage`, `step`, `bind`) | LOCAL | various | local files only; `merge-install` edits `.git/config` + `.gitattributes` | — | `ops/log` | various |

**Indirect / shared paths to trace:** `Client.apply` is called only from `apply_release` and `rollback` (asserted by `test_write_helpers_are_called_only_from_known_functions` 88 — verify the AST walk covers aliases and `getattr`); `Client.bulk_upsert` has no Python caller (`CLIENT_WRITERS["bulk_upsert"] = set()`); `run_tests` sends `{op}` writes (`WRITE_ENDPOINT` regex includes `\{op\}`); browser runner (all write ops, no role check); spike `common.py` (`assert_writable` with localhost exemption); `sandbox refresh` = `release-plan` (+ person runs `apply`); env overrides: `PLS_HOME` (launcher picks framework code — code-substitution path), `PLS_PROFILE_DIR`, key env vars named in `connections.json`.

---

## Phase 2 maps

### P. Phase-to-artifact map (source: `docs/architecture.md` §5, skills)

| Phase | Inputs | Outputs / artifacts | Commands | Skill | Human point |
|---|---|---|---|---|---|
| (onboarding, Origin existing) | site packages / exports | `ops/onboarding/*-summary.md`, adoption records, `design/as-is/` | `version`, `adopt`, `adopt-package`, `env-compare`, `refs`, `xref`, `spec-skeleton` | `pls-x-onboarding`, `pls-x-spec-recovery` | decisions per finding |
| P1 | request (`requirements/sources/`) | `requirements/REQ-*.md`, `index.md` | `step`, `gate G1` | `pls-p1-requirements-analyst` | **G1** |
| P2 | approved REQs | `design/decisions/DES-*.md`, `roles.json`, slot ledger | `xref`, `gate G2` | `pls-p2-solution-designer` | **G2** |
| P3 | DES | `config/**`, `_tenant/scheduled-scripts/` | `unpack`, `pack`, `canon`, `lint`, `bootstrap-plan`, `bootstrap`, `bind`, `principals`, `sandbox`, `harvest`, `merge-site` | `pls-p3-config-builder`, `pls-p3-script-engineer` | — |
| P4 | config + specs | `tests/specs`, `tests/results`, `g3-verification.md` | `test`, `coverage` | `pls-p4-test-writer` | **G3** |
| P5 | G3 | `releases/<R>/` plan, payloads, rollback, reports, `approvals.md` | `release-plan`, `gate G4`, `apply`, `mark-applied`, `jobs-verified`, `backup` | `pls-p5-release-manager` | **G4**, manual job deploy |
| P6 | live exports | `ops/drift/`, incidents | `drift`, `export`, `harvest` | `pls-p6-maintenance-triage` | accept/revert drift |

### Q. Invariant enforcement map (INV-n = I-n, `docs/architecture.md:24-32`)

| INV | Definition | Enforcement (planned inspection) | Command | Tests | Known gap / hypothesis |
|---|---|---|---|---|---|
| 01 | git desired state | round trip unpack/pack; `mark-applied` compare; drift | unpack, pack, mark-applied, drift | `test_pls.py` round-trip tests | live baseline on `applied-differs` (B1) |
| 02 | complete payload + drift | `plan_site` (~880–1000) L-DEP-01, drift refusal, `apply_release` preflight | release-plan, apply | `test_pls.py`, `test_http.py` | preflight → write window (C9, API limit) |
| 03 | no AI path to prod | `WRITABLE_ROLES`, `assert_writable`; network isolation (doc) | all WRITES | `test_prod_is_never_written` | role comes from editable `environments.json`; browser runner unguarded [H] |
| 04 | AI never approves | `GT.record`, `GT.require`, `job_verifier`, skill text | gate, jobs-verified, release-plan, apply, bootstrap | `test_gate.py`, `test_pls.py` | names/quotes are CLI arguments; records are plain files [H]; no trust-boundary ADR [H] |
| 05 | ladder | L-LAD-01 (lint), P2 skill | lint | `test_pls.py::test_lint_rules` | brittle text match (audit F-08) |
| 06 | tools decide | diff/classify/coverage/drift in code | diff, classify, coverage | various | skills asking the model to judge [U] |
| 07 | no secrets/data | L-SEC-01 (unpack, lint, plan), `.gitignore`, adopt refusal | unpack, lint, release-plan, adopt | `test_pls.py`, `test_adopt.py` | `ops/log` content; `tests/results` record data [U] |
| 08 | traceability | `coverage`, `traceability.json` | coverage | `test_pls.py` | — |
| 09 | defects → rules | review-findings, KB, tests | — | — | trace table needed (B9) |

### R. ADR-to-code map (initial; reviewer completes in WS-1)

| ADR | Decision (short) | Status [F] | Implementation | Tests | Initial observation |
|---|---|---|---|---|---|
| 0001 | config scope in git | Proposed | unpack/pack, `pls_scope.py` | `test_scope.py` | Proposed while relied upon (A3) |
| 0002 | column-slot zones | Proposed (TD-01) | slot ledger, `slot_collisions` | `test_pls.py` | customer zone not enforced by lint (audit) |
| 0003 | prod deploy (option C) | Proposed (TD-02) | none (package format only) | — | J1–J3 |
| 0004 | data-impacting changes | Accepted | migration gate in `release_plan`; runner `bulkUpsert` | `test_pls.py` | migration write only in JS runner [H] |
| 0005 | config storage & secrets | runtime-secrets part accepted (§ line 40) | L-SEC-01 | `test_pls.py` | — |
| 0006 | permissions in git | Accepted | perms refs, L-PERM-01 | `test_pls.py` | — |
| 0007 | new sites via bootstrap | Proposed | `bootstrap_plan`, `H.bootstrap`, `bind` | `test_http.py` | — |
| 0008 | HTTP transport | Proposed | `pls_http.py` | `test_http.py`, `test_write_guards.py` | implemented + relied upon while Proposed |
| 0009 | version detection, kb-verify | Proposed | `pls_version.py`, `pls_kbverify.py` | `test_version.py`, `test_kbverify.py` | — |
| 0010 | mail & jobs safety | Proposed | `pls_side_effects.py` | `test_side_effects.py` | — |
| 0011 | sandboxes, harvest, merge | Proposed | sandbox/harvest/merge in `pls.py`, `pls_merge.py` | `test_sandbox_merge.py` | — |
| 0012 | scheduled scripts option B | Accepted (+ implementation notes 2026-11-09) | jobs code, `lint_jobs` | `test_pls.py`, `test_side_effects.py` | notes added to an Accepted ADR — check against ADR rule "Accepted ADRs are not edited" (`docs/adr/README.md:19`) |
| 0013 | observability, tool-first | Proposed | `pls_log.py`, `pls_usage.py` | `test_observability.py` | log-failure policy not stated [H] |
| — | **candidates without ADR** [H] | — | `pls gate` (gate records), `Operators` profile row, onboarding-first refusal (L-ONB-01), canonical defaults table, `PLS_HOME` launcher | — | decide architecture vs detail in A2 |

### S. Trust-boundary map

| Boundary | Enforced by code | Relies on documentation / agent instruction | Evidence to collect |
|---|---|---|---|
| AI agent → CLI arguments (`--approver`, `--by`, `--quote`, `--yes`) | name must be in profile; quote non-empty; `--yes` skips typed confirmation | that the agent only passes words the person said (CLAUDE.md rule 1, lifecycle skill §2) | `pls_gate.py` record/require; skills text; EV-03, EV-10 |
| AI agent → files (`gates/`, `releases/*/plan.json`, `CLAUDE.md`, `environments.json`) | none (plain files); `GT.require` re-checks approver name | git history, review, "never edit to get past a refusal" | write a gate file by hand on a copy → does `apply` accept it? |
| Local operator config (`.pls/connections.json`: url, keys refs, `allow_write`, timeout) | `assert_writable`, alias rule, key resolution never literal | gitignored; agent "never edits" | `pls_http.py:45-100`; `test_keys_resolve_from_env_and_file_never_literal` |
| Project profile (`CLAUDE.md`) | parsed for Approvers/Operators/Origin | person-maintained | `pls_gate.py` parsers |
| Dev/stg environments | role + allow_write + G4 (stg) | network reachability | `test_write_guards.py` |
| Production package | none (no runner) | ADR-0003 manual import | J2 |
| Customer-side runner | n/a | ADR-0003 | J1, J3 |
| Pleasanter API | preflight UpdatedTime, read-back | no conditional write (API limit) | C9 |
| Audit storage (`ops/log`, `gates/`, `releases/`) | append-only by convention (`gates` opened with `"x"`) | git as tamper evidence | D4–D6 |
| Framework code (`PLS_HOME`, `.claude/framework.lock`) | `skills check` hashes skills only | operator controls env | launcher `pls.py:11` in projects |

---

## Deliverable 2 — Criterion coverage matrix

Columns: ID · required behaviour (short) · files / functions · existing tests (planning-time pointers) · verification (method class) · risk if unverified · WS. Every criterion appears once as primary.

| ID | Required behaviour | Files / functions | Existing tests | Verification | Risk if unverified | WS |
|---|---|---|---|---|---|---|
| A1 | every command/skill/lint/template maps to P1–P6, artifact or INV | parser 2495–2650; `docs/architecture.md` §7.1–7.3; `skills/README.md` | — | Static: build table command→phase; list unmapped | Low | 1 |
| A2 | decisions only in ADRs | `tools/pls/*.py`, skills, templates vs ADR Decision sections | — | Code inspection; candidates in map R | Medium | 1 |
| A3 | ADR status matches reality | ADR headers, `docs/adr/README.md`, `docs/plan.md` | — | Static compare; "Proposed but relied upon" list | Medium | 1 |
| A4 | one authoritative source per rule | search rules (e.g. writes only dev/stg, `--yes`, I4) across CLAUDE.md, template, skills, ADRs | — | Static search (`grep -rn "allow_write\|--yes\|never approve"`) | Medium | 1 |
| A5 | no customer content in core | `tools/`, `skills/`, `templates/` | — | Static search for site ids (3+ digits), hostnames, customer/business terms (list from `HANDOFF.md` env table) | High (I7) | 1 |
| A6 | trust boundaries written | ADRs, `docs/architecture.md` | — | Static: does any ADR state map S rows? | Critical gate for B4/D5 statuses | 1 |
| B1 | round trip; `applied-differs` live baseline | `mark-applied`, `baseline` ~800, `drift_report` | `test_pls.py` (mark-applied/drift tests), `test_http.py` (applied-differs via `drop_on_save`) | Fake-server + **L** (person: apply→export→mark-applied on dev) | High | 4 |
| B2 | complete payload, drift refusal, UpdatedTime | `plan_site`, `release_plan`, `apply_release` 182-187 | `test_pls.py::test_release_plan_writes_nothing_if_one_site_fails`, drift tests; `test_http.py` preflight | Unit + fake-server; one refusal test per rule | High | 3 |
| B3 | every write path refuses prod | `assert_writable`; `pls-runner.js`; `spike/.../common.py:59` | `test_write_guards.py::test_prod_is_never_written` | Static enumeration (endpoint regex + JS + spike) + fake-server per WRITES command | Critical | 2 |
| B4 | no record without profile approver + words; skills stop | `GT.record`, `job_verifier`, `jobs_verified`; skills | `test_gate.py`, `test_pls.py::test_jobs_verified_*` | Unit (unknown name, empty/whitespace quote, case tricks, profile placeholder) + static skill stop points; authenticity → A6 | Critical | 2 |
| B5 | ladder reason, L-LAD-01 | lint 600-625; P2 skill | `test_pls.py::test_lint_rules` | Unit + static | Medium | 6 |
| B6 | tools compute; skills don't judge | skills vs commands | — | Static: each skill step that states a computable result → tool call present | Medium | 6 |
| B7 | secrets lint; gitignore; no data in logs/reports/fixtures | `SECRET_RES` 79; `.gitignore` (template); `ops/log`; `releases/`; fixtures | `test_pls.py` (L-SEC-01), `test_adopt.py` | Static + run lint on project copies; grep fixtures/logs for key-like strings (patterns only, never print matches in full) | Critical | 2 |
| B8 | REQ→DES→config→test traceability | `coverage` 683 | `test_pls.py` coverage tests | F: `pls coverage` on copy of `demo-equipment` | Medium | 4 |
| B9 | each finding → rule/test/KB/TD | `docs/review-findings.md`, slices, `plans/reports/`, `docs/reviews/` | — | Static trace table | Medium | 1 |
| B10 | G4 bound to payload digest (cstg) | `GT.require` 181; `release_plan` plan fields | none known | Fake: change payload after G4 on copy → expect refusal (hypothesis: accepted → FAIL) | Critical (cstg) | 2 |
| B11 | success by read-back | `apply_release` 198 `applied-unverified`; `mark-applied` | `test_http.py` | Code + fake-server; status sequence | High | 3 |
| C1 | dev/stg + allow_write (+G4 stg); re-validated per site | `assert_writable` 92; apply 2120; per-site loop | `test_write_guards.py::test_apply_bootstrap_test_kbverify_send_nothing_without_allow_write` | Fake-server matrix role×allow_write×G4; env overrides; check whether re-validation per site exists (hypothesis: once per command) | Critical | 2 |
| C2 | side effects: unknown refuses; sandbox riskier; person only | `pls_side_effects.py`, `env_effects` | `test_side_effects.py`, `test_sandbox_merge.py` | Re-run + independent negative cases | High | 3 |
| C3 | fail closed on malformed inputs | `rj`/`wj`, `envs()`, `load_connection`, `_job_index`, `bad_plan_jobs`, profile parsers | some in `test_side_effects.py` | Fake-server malformed-input matrix (missing, bad JSON, wrong type, null, bad enum, non-UTF-8, BOM) × 5 files | High | 3 |
| C4 | irreversible steps need person | `_confirm` 2026; `--yes` uses | `test_http.py` (`--yes`) | Static: every `--yes`/`_confirm`; no auto-yes path (env var, config) | Critical | 2 |
| C5 | refusals say what/why/next, no secrets | all `Fail(`, `TransportError(`, `REFUSED` | — | Static search + sample outputs from test runs | Low | 3 |
| C6 | partial failure: preflight first, reverse restore incl. failing site | `apply_release` 177-198, `rollback` 201 | `test_http.py` (`fail_update_on`) | Fake-server: fail at site 2 of 3; assert restore order and set | High | 3 |
| C7 | shared resources protected by code | sandbox/shared_from checks in release_plan, apply, test; `env_effects` | `test_sandbox_merge.py` | Re-run + bypass attempts (hand plan, alias) | High | 3 |
| C8 | failed rollback → "recovery required" (cstg) | `apply_release` 197, `rollback` | `fail_restore_on` exists in Fake [F] | Fake-server: fail restore → inspect status (hypothesis: `rolled-back` → FAIL) | High (cstg) | 3 |
| C9 | UpdatedTime preflight; window documented; post-apply round trip | `apply_release` 182-187; KB/ADR text | `test_http.py` | Code + test + doc search for the limit | Medium | 3 |
| C10 | timeout after write: no blind retry, read-back (cstg) | `Client.call` 119-135, `apply_release` 190-195 | none known | Fake-server that writes then delays beyond timeout | High (cstg) | 3 |
| C11 | no failure leaves success | all status writers (`apply-log.json`, plan status, bootstrap status, tests results) | various | Inspect statuses after each failure test of C6/C8/C10/E3 | High | 3 |
| D1 | complete gate/verification records; L-GATE-01 | `GT.record` fields; `plan.jobs.verified`; `GT.lint` | `test_gate.py` | Static + unit | High | 2 |
| D2 | agent vs human vs operator separation | record fields (`recorded_by`, `role`, `approved_by`); `ops/log` actor | `test_pls.py::test_jobs_verified_*` | Static | High | 2 |
| D3 | release folder self-sufficient | `releases/<R>/` in project copies | — | Static on one real release folder (`demo-equipment`) | Medium | 4 |
| D4 | run log complete, no secrets | `pls_log.append/run`; `ops/log/*.jsonl` | `test_observability.py` | Static + grep logs on copies | High | 4 |
| D5 | tamper evidence (prod) | git; ADR? | — | Static: ADR naming git as boundary | Medium | 1 |
| D6 | log-write failure policy (cstg) | `pls_log.py:105-124` | — | Fake: make `ops/log` unwritable on copy, run `apply` against fake server | Medium | 4 |
| E1 | same inputs → same outputs | unpack/pack/release-plan | — | F: run twice on copy, diff outputs excluding timestamps | Medium | 4 |
| E2 | canonicalisation modelled, hides nothing | `canonicalize` 218, `canonical-defaults.json` | `test_pls.py::test_canon_and_lint` | Unit with unknown field, null vs empty, order | High | 4 |
| E3 | repeat after interruption safe | bootstrap partial, bind, mark-applied, apply after rollback | `test_http.py` (partial bootstrap?) [U] | Fake-server repeats | High | 4 |
| E4 | references resolve and read back; refuse missing/ambiguous/cross-env | `to_refs`/`from_refs` 149-200; jobs rendering | `test_pls.py`, `test_scripts.py` | Unit round trip + refusals incl. scheduled scripts | High | 4 |
| F1 | KB entries: version, evidence, probe, limits | `skills/pls-kb-pleasanter/references/*.md`, `probes/` | — | Static sample of all D-entries | Medium | 4 |
| F2 | assumptions cite KB | tools + skills | — | Static: grep Pleasanter assumptions (e.g. `View`, `UpdatedTime`, `SiteSettings`) and look for KB ids in comments | Medium | 4 |
| F3 | version change detected | `pls_version.py`, `version_check` ~1050 | `test_version.py` | Unit + static report | Medium | 4 |
| F4 | uncertain behaviour conservative | unknown fields kept in canon; unknown states refuse | `test_side_effects.py` (unknown states) | Unit | Medium | 4 |
| G1 | minimum runtime real | `docs/setup.md:15`; `pls_adopt.py` | — | F on Python 3.10 (**needs H-3**) — else static syntax scan (`python -m py_compile` under 3.10 not possible → NOT VERIFIABLE) | Medium | 5 |
| G2 | Windows: UTF-8, BOM, CRLF | `pls.py:80-82` reconfigure; `utf-8-sig` reads; `.gitattributes` (framework + template) | `test_pls.py` (BOM) [U] | F on Windows (current machine) + static | Medium | 5 |
| G3 | stdlib only, offline tests | imports | full suite | Static import scan; run suite with network disabled (**H**: disabling network needs authorization; alternative: confirm fake server binds 127.0.0.1 only) | Low | 5 |
| G4 | HTTP vs browser runner parity | `pls_http.py` vs `pls-runner.js` | `test_runner.mjs` | Static side-by-side (statuses, preflight, rollback, guards) | High | 5 |
| G5 | scale on PLAY BOARD, `--summary` | `release-plan`, `lint --summary`, `refs --summary` | — | Runtime benchmark on copy of `pls-onboard-playboard-r2` (release-plan needs exports: use files in the copy's `.pls/exports`? those are excluded from copies → [D] H-5) | Low | 5 |
| G6 | setup doc accurate | `docs/setup.md` | — | Human/process (clean machine) or NOT VERIFIABLE | Low | 5 |
| H1 | guard positive + negative tests | B/C guards → tests | all | Static mapping table | High | 7 |
| H2 | tests assert state/records | sample per module | — | Static sample (≥2 tests/module) | Medium | 7 |
| H3 | escaped defects have regression tests | B9 trace | — | Static + one revert spot-check on a worktree copy | Medium | 7 |
| H4 | earlier review gaps closed or TD | `plans/reports/*`, `docs/reviews/*` | — | Static | Medium | 1 |
| H5 | skipped/failed/not-run visible; `pass-api-only` visible | unittest output; `run_tests` statuses; `coverage` | — | F: run suites with `-v`, count skips; static on coverage | Medium | 7 |
| H6 | skill evals after behaviour edits; EV cases in eval set | `evals/`, `skills/README.md` versions vs results dates | — | Static: versions changed after last eval date; EV-01…10 present? (hypothesis: absent) | Medium | 6 |
| I1 | skills state inputs/procedure/outputs/checklist/stops | `skills/*/SKILL.md` | — | Static per skill | Medium | 6 |
| I2 | no skill tells agent to touch keys/guards/profiles/`--yes` | skills, templates | — | Static search (`key`, `allow_write`, `side_effects`, `--yes`, `Approvers`, `Operators`) | Critical | 6 |
| I3 | project skills match lock | `pls skills check` | `test_pls.py` | F on each project copy | Low | 6 |
| I4 | token rules present and measured | lifecycle §2, `ops/usage` | — | Static | Low | 6 |
| I5 | language rule | spot-check | — | Static | Low | 6 |
| I6 | completion reports complete | skill text + one recent report | — | Static | Low | 6 |
| J1 | runner path without AI, same package | ADR-0003; none in repo | — | Static + **L**; expected NOT VERIFIABLE/FAIL | Critical (prod) | 7 |
| J2 | immutable, verifiable package | `releases/<R>/` fields | — | Fake: alter payload/target; expect refusal (hypothesis: no verifier exists) | Critical (prod) | 2 |
| J3 | runner has no AI credentials/path | — | — | Static: no runner → NOT VERIFIABLE | Critical (prod) | 7 |
| J4 | prod-blocking debt resolved/accepted in writing | `docs/tech-debt.md` | — | Static | High (prod) | 7 |
| J5 | customer responsibilities written | template, handover docs | — | Static | Medium (prod) | 6 |

Criteria verified together (same run, separate assertions): C6 + C8 + C11 (one failure-injection harness, three assertions); C2 + C7 (sandbox fixtures); B3 + C1 + C4 (write-guard matrix, separate test functions per property); E1 + E4 (round-trip harness). B4 and B10 are **not** merged (identity vs content binding).

---

## Deliverable 3 — Workstream execution plan

| WS | Priority | Criteria (primary) | Dependencies | Effort | Parallel-safe | Deliverables |
|---|---|---|---|---|---|---|
| WS-2 Security, approval, prod isolation | P0 | B3, B4, B7, B10, C1, C4, D1, D2, J2 | none | 8–10 h | yes (own worktree + fake server) | findings table; write-path inventory; approval-forgery results |
| WS-3 Write safety, recovery, tenant isolation | P0 | B2, B11, C2, C3, C5, C6, C7, C8, C9, C10, C11 | WS-2 inventory (read) | 7–9 h | yes (own worktree) | failure-injection results; malformed-input matrix |
| WS-1 Architecture, ADR, invariants | P1 | A1–A6, B9, D5, H4 | none | 5–6 h | yes (static) | maps P/Q/R/S completed; trust-boundary verdict (feeds WS-2 statuses) |
| WS-4 Determinism, round trip, KB | P1 | B1, B8, D3, D4, D6, E1–E4, F1–F4 | WS-1 (KB/ADR list) | 6–7 h | yes (own copy) | round-trip evidence; L scenario for B1 |
| WS-6 Skills, agent governance | P2 | B5, B6, H6, I1–I6, J5 | none | 3–4 h | yes (static) | skill checklist table; eval gap list |
| WS-5 Portability, performance, ops | P2 | G1–G6 | H-3, H-5 | 3–4 h | yes (separate copy) | runtime/OS evidence; benchmark |
| WS-7 Evidence verification, verdict | P0 (last) | H1, H2, H3, H5, J1, J3, J4 | all others | 3–4 h | no (single reviewer, fresh context) | final report per standard §6; verdict per stage |

Isolation rules: each WS that runs commands uses its own `git worktree add <scratch>/<ws> 782116b` and its own project copies; the fake server binds 127.0.0.1 on a random port per test (`test_http.py:serve`) so parallel runs do not collide. WS-2 and WS-1 (A6) use **separate reviewer contexts**; WS-7 is a fresh context that re-checks a sample of every PASS.

Per-WS inspection lists (files and functions are those in Deliverable 2 rows; additionally):
- WS-2: `pls_http.py:31-110`; `pls.py` `http_cmd` branches apply/bootstrap/test/kb-verify/backup; `pls_gate.py` whole; `pls_kbverify.py` guard path; `pls-runner.js` all write functions; `spike/round-trip/scripts/common.py:40-70`; `tests/test_write_guards.py`, `tests/test_gate.py`; skills grep for `pls gate`, `jobs-verified`, `--yes`.
- WS-3: `pls_http.py:119-230`; `pls.py` `mark-applied` branch, `release_plan`, `plan_site`, sandbox functions (`sandbox_create` ~1540, `sandbox_refresh`, `harvest`), `env_effects`, `last_applied_jobs`; `pls_side_effects.py`; `tests/test_http.py` Fake switches.
- WS-4: `pls.py` 131–440 (refs, canonical, logical, payload, diff), `canonical-defaults.json`, `pls_version.py`, `pls_compare.py`, KB references, `pls_log.py`.

---

## Deliverable 4 — Test execution matrix

Commands derived from `HANDOFF.md:12` and `tools/pls/tests/*.py` docstrings. Environment for all F runs: reviewer worktree of `782116b`, Windows 11, Python 3.12.10, node v24.19.0 (recorded at planning); record `python --version`, `node --version`, `git rev-parse HEAD` in the report.

| # | Test group | Command (cwd) | Environment | Criteria | Expected result | Side-effect risk / authorization |
|---|---|---|---|---|---|---|
| T1 | Full Python suite | `python -m unittest discover -s tests -v` (cwd `<wt>/tools/pls`) | worktree, temp dirs, 127.0.0.1 fake server | H1, H2, H5 + all F | 214 run, 0 fail; record skips (node-dependent tests skip when node missing) | temp files only; none |
| T2 | Node runner tests | `node --test tools/pls/tests/test_runner.mjs` (cwd `<wt>`) | worktree | G4 | 6 pass | none |
| T3 | Write-guard inventory | `python -m unittest tests.test_write_guards -v` | worktree | B3, C1 | pass; reviewer additionally checks the AST covers aliases/`getattr` | none |
| T4 | Security guard additions (proposed, in reviewer copy only) | new test file `<wt>/tools/pls/tests/review_test_security.py` run with `python -m unittest review_test_security -v` | worktree copy; **never committed** | B4, B10, C1, C4, J2 | see Deliverable 5 scenarios | writes only in copy; none |
| T5 | Failure injection (proposed) | `review_test_recovery.py` using `test_http.Fake` (`fail_update_on`, `fail_restore_on`, `drop_on_save`) + a delaying handler for timeouts | worktree copy | C6, C8, C10, C11, E3 | statuses recorded per scenario | none |
| T6 | Malformed input matrix (proposed) | `review_test_malformed.py` | worktree copy | C3 | refusal (exit 2 / `Fail`), never traceback or pass | none |
| T7 | Determinism | on a copy of `demo-equipment`: `python pls.py unpack …` / `pack` / `release-plan` twice; `git diff --no-index` between outputs | project copy (no `.pls/`) | E1, E4 | identical except declared timestamps | writes in copy; release-plan needs local exports → **[D] H-5** |
| T8 | Lint/skills on projects | `python pls.py lint --summary`, `python pls.py skills check`, `python pls.py coverage` in each project copy | project copies | B7, B8, I3 | record outputs | creates `ops/log/*.jsonl` in the copy (observed at planning) — copies only |
| T9 | Minimum runtime | T1 under Python 3.10 | isolated install | G1 | expected fail if 3.12 syntax present | **needs H-3** |
| T10 | Benchmark | `Measure-Command { python pls.py lint --summary }` and release-plan on PLAY BOARD copy | project copy | G5 | timings recorded | needs exports (H-5) |
| T11 | Log-failure policy | T5 variant with `ops/log` made read-only (`attrib +r` on the folder in the copy) | worktree copy | D6 | documented behaviour or FAIL | copy only |
| T12 | Fresh-agent evals | per `evals/README.md` manual procedure; EV-01…10 need new cases | scratch project | H6 (I-group evidence) | results files | runs an agent — **needs human authorization**; out of code-review scope (standard appendix) |
| T13 | Production package dry run | none possible (no runner) | — | J1, J2 | NOT VERIFIABLE (J1); J2 via T4 | — |
| T14 | Method L scenarios | written only; executed by a person on MADLAB dev | dev | B1, J1 | scenario + expected result | **person runs** (H-4) |

---

## Deliverable 5 — High-risk verification plan (scenarios)

Each scenario: setup → action → expected safe outcome → evidence. All in reviewer worktree with the fake server unless marked L.

**Approval forgery (B4, D1, D2, A6)**
1. Hand-write `gates/2026-11-09-G4-….json` with an approver listed in the profile and no `pls gate` call → run `apply` on a stg plan against Fake. Expected per standard: either refused, or reported as ACCEPTED BOUNDARY with an ADR. Hypothesis: accepted (only name re-check, `pls_gate.py:184`).
2. `pls gate G4 --approver "nam " --quote " "`; `--approver "<name>"` with template profile; profile with `Approvers | tbd |`. Expected: refused.
3. Edit `CLAUDE.md` Approvers to add "Agent", then `pls gate` → expected: works (file trust) → boundary question.
4. `jobs-verified` with operator of `dev` on a `stg` release; with `--approved-by` non-G4 → refused (existing test `test_jobs_verified_accepts_an_operator_of_the_env_or_a_g4_approver` — re-run independently).
5. Hand-edit `plan.json` `jobs.verified` → next release baseline uses it? (static: `last_applied_jobs` trusts it).

**Production access bypass (B3, C1, C4, J2)**
6. For every WRITES command: env `role: prod` with `allow_write: true` → no write call recorded in `Fake.calls` (extends `test_prod_is_never_written`).
7. Same URL configured twice: `prod` and a second env `stg` pointing at the prod URL → writes allowed (role not bound to URL) → expected: documented boundary (I3 relies on network isolation + no prod key). Evidence: `assert_writable` signature.
8. Sandbox alias: env `dev-x` with `connection: prod` / `sandbox_of: prod` → refused (`pls_http.py:63`).
9. `PLS_HOME` pointing at a modified framework → static: launcher has no integrity check (`skills check` hashes skills only) → boundary.
10. Browser runner: static proof that no role/allow_write check exists; parity finding (G4).
11. Alter `payload-<s>.json` after G4 → `apply` → expected refusal for B10/J2; hypothesis: applied.

**Guard bypass (C1, C2, C3, C7)**
12. Per-site re-validation: flip `allow_write` to false between preflight and site 2 (monkeypatch `load_connection`) → expected per C1: re-validated; hypothesis: validated once.
13. Malformed `environments.json` `side_effects: null`, `"jobs": "Unknown"`; BOM; non-UTF-8 `_index.json`; `plan.json` `jobs: []` → refusal.
14. Hand plan targeting a `shared_from` site in a sandbox → refused (existing test `test_shared_sites_and_stale_plans_are_never_written` — re-run).

**Partial rollback (C6, C8, C11)**
15. 3-site plan; `fail_update_on` = site 2 → restore order site 2, site 1 (reverse, including failing); site 3 untouched; status `rolled-back`; `apply-log.json` contents.
16. Same + `fail_restore_on` = site 1 → expected per C8: status signals recovery required; hypothesis: still `rolled-back` (`pls_http.py:197`) → FAIL (cstg).

**Concurrent modification (C9, E3)**
17. Fake changes `UpdatedTime` between plan and apply → `refused` before any write.
18. Fake changes a site after preflight, before write → write proceeds (API limit) → `mark-applied` must report differences (applied-differs) — verify the post-apply comparison catches it.
19. Re-run `apply` after `rolled-back` (status no longer `planned`?) and after `applied-unverified` → no duplicate write.

**Uncertain outcome (C10)**
20. Fake handler persists `updatesite` then sleeps > client timeout → observe: exception type, whether rollback runs, status written, whether a retry occurs. Expected: no blind retry; read-back step stated.

**Tenant isolation (C2, C7, E4)**
21. Sandbox created while dev `disabled`, dev later `unknown` → writing test refused (existing `test_sandbox_shares_the_tenant_…` — re-run independently).
22. `${site:x}` resolving to a `shared_from` id inside a sandbox payload → release-plan refuses (`sandbox_create` `--allow-shared-writes` path).
23. Cross-project: `environments.json` of project A listing a site id of project B → static: no ownership registry → boundary/finding.

**Audit failure (D4, D6)**
24. `ops/log` read-only → run `apply` against Fake → command result and log state (T11).
25. Grep copies' `ops/log/*.jsonl` and `releases/*/apply-log.json` for key-like patterns (`SECRET_RES` regexes) — report counts only.

**Agent instruction attacks (I2, EV-09; static part only)**
26. Search skills/templates for instructions that could be read as permission to edit guards/profiles; search repository content for embedded imperative text addressed to agents in data files (e.g. requirement sources). Agent-run cases EV-01…EV-10 are **eval** work (T12), not executed in this review.

---

## Deliverable 6 — Evidence collection plan

- One report per workstream: `<review-dir>/ws-<n>-<slug>.md`, review directory **outside the repository** unless H-2 decides otherwise (the review must not modify repository files).
- Finding rows use the standard §5 format exactly: `| ID | Criterion | Severity | Status | Stage | Finding | Evidence (file:line, test, command output) | Reproduction | Proposed fix | Verification |`.
- Every row cites file:line at the reviewed commit (`git rev-parse HEAD` in the header) and real test names; command outputs are summarized (counts, first failing line) with the full output saved next to the report.
- Separate columns or labels for **static** vs **runtime-verified** conclusions; hypotheses never become findings without evidence.
- Each WS report ends with: criteria covered with status, skipped steps and why, environment (OS, Python, node, commit).
- WS-7 merges into the §6 final report: executive summary, findings, not verifiable, accepted boundaries (each with ADR), top 5 risks, not reviewed, test evidence, verdict per stage, remediation roadmap.

## Deliverable 7 — Not-verifiable register (planning-time)

| Criterion | Missing prerequisite |
|---|---|
| B1 (live part) | person runs apply→export→mark-applied on MADLAB dev (H-4) |
| G1 | Python 3.10 runtime (H-3) |
| G5 | release-plan inputs (exports) for PLAY BOARD in a copy (H-5) |
| G6 | clean machine |
| J1 | customer-side runner does not exist (ADR-0003 Proposed) |
| J3 | same |
| H6 / EV-01…EV-10 | agent eval runs (outside code review; standard appendix) |
| D5 | depends on A6 outcome (ADR naming git as boundary) |
| C10 (live confirmation) | real server timeout behaviour — fake-server evidence only |

## Deliverable 8 — Review completion definition

The review is complete when all of the following hold:
1. Each of the 66 criteria (A1–J5) has exactly one status from standard §2, recorded once as primary.
2. Every FAIL / PARTIAL has file:line evidence and a reproduction; every PARTIAL names the missing part.
3. Every NOT VERIFIABLE names the exact missing method/evidence (Deliverable 7 updated).
4. Every ACCEPTED BOUNDARY cites an ADR; otherwise it is a FAIL "missing trust-boundary ADR".
5. Mandatory paths examined: every row of Deliverable B with class WRITES, the browser runner, the spike guard, every record-writing command (`gate`, `jobs-verified`, `mark-applied`, plan writers), and scenarios 1–26 executed or explicitly not run with reason.
6. Priority set (B3, B4, B10, B11, C1, C2, C3, C8, C11, D2, H5) fully evidenced.
7. Top five risks ranked by impact × likelihood.
8. Not-reviewed files/commands disclosed.
9. Test evidence recorded: commands, runtime, run/passed/failed/skipped/not executable.
10. Verdict per stage (`demo`, `cstg`, `prod`) given with the rule of standard §6.8.
11. No repository file changed (`git status` of the framework and project repos identical to start, except files the human allowed).

---

## Human decisions required before execution

| # | Decision |
|---|---|
| H-1 | Use `docs/review-criteria.md` §5/§6 as the report format (the named `docs/design-review-standard-v2.md` does not exist), and confirm "A–K" means A–J |
| H-2 | Commit or freeze `docs/review-criteria.md`; choose where review reports live (outside repo by default) |
| H-3 | Authorize an isolated Python 3.10 install for G1 (or accept NOT VERIFIABLE) |
| H-4 | A person runs method-L scenarios on MADLAB dev (B1; J1 not possible) |
| H-5 | Which project copies may be used; may exports under `.pls/exports` be copied for G5/T7 (they hold customer configuration — read-only copy outside git) |
| H-6 | Trust boundaries: write or decline an ADR before the review, so A6/B4/D5 statuses are decided on it |
| H-7 | Approve this plan |
