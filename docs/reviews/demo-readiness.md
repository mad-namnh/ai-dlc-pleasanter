# Review — demo readiness (2026-11-05)

- **Reviewer:** Claude, for Nam. Read-only review; nothing was implemented.
- **Scope:** framework `ai-dlc-pleasanter` (architecture v0.3, `pls` 0.5, skills KB 0.7 / P1 0.3 / P2 0.5) and the demo projects `pls-demo-inquiry` and `pls-demo-equipment`.
- **Plan derived from this review:** `docs/plan.md`, Step 4b.

## Demo requirements (Nam)

1. **R1** — the input is a specification in natural language.
2. **R2** — the framework carries out every designed lifecycle step (P1–P6, gates G1–G4) and builds the Pleasanter app described by the spec.
3. **R3** — simple setup:
   - another person receives the repositories and can run the demo;
   - at most they set a connection config for their Pleasanter environment;
   - token use is low.

## Verdict: not ready

The technical core is solid and has been proven on stg three times (R-20261105-01, -05, -E03). What is missing is the packaging: a person or agent who did not build it cannot run the process unaided.

### R1 — natural-language spec: partly met

**Met:**
- `pls-p1-requirements-analyst` 0.3 turns a Japanese request into EARS requirements, `[assumed]` defaults and Japanese questions.
- It passed eval cases 001 and 002.
- A good demo spec exists: `pls-demo-equipment/requirements/sources/2026-11-05-equipment-loan-request.md`.

**Gap:** there is no demo package. Nothing says where a spec goes or which command or prompt starts the run.

### R2 — framework runs the whole lifecycle: not met (largest gap)

| # | Finding | Severity |
|---|---|---|
| R2-1 | Only P1 and P2 are skills. P3 (build `config/`), P4 (write test specs, G3 evidence), P5 (release plan, diff report, apply, mark-applied) and P6 (drift baseline) were done by the session agent from its own context. A fresh agent has no instructions after G2. | High |
| R2-2 | Project repositories have no `CLAUDE.md` or runbook. Nothing defines the phase order, where to stop for a gate, how gate decisions are recorded, or which `pls` command belongs to each step. | High |
| R2-3 | The test-spec format is undocumented. Fields such as `ops`, `as_key`, `expectHttp`, `spec.vars` and `$var` appear only in ADR-0008 and the slice reports. | High |
| R2-4 | `pls bootstrap` and `pls apply` over HTTP are covered only by unit tests against a fake server. The only real HTTP run on dev used `http-check`, `export` and `test`. | Medium (demo risk) |
| R2-5 | Release artefacts (`diff-report.md`, `g3-verification.md`, `approvals.md`) have no template and are written free-form each time. | Medium |
| R2-6 | Data migration over HTTP is missing: `bulkUpsert` exists only in the browser runner. Reviewer agents and CI are also missing. | Low for a new-app demo |

### R3 — simple setup, low tokens: partly met

**Good:**
- `pls` uses only the Python standard library.
- The connection lives in the operator's `.pls/connections.json` and keys come from environment variables. Nothing secret is in git.
- `bootstrap` creates new sites, so an empty Pleasanter folder is enough.
- The HTTP transport removes the base64 transfers.

| # | Finding | Severity |
|---|---|---|
| R3-1 | No project template or `pls init`. `environments.json` (`parent_id`, `principals`), `design/slot-ledger.json`, `traceability.json`, `.gitignore`, the skills copy and `framework.lock` are all written by hand. | High |
| R3-2 | The framework is found only through the relative path `../ai-dlc-pleasanter`, which fixes the folder layout. Skills are copied by hand, and nothing checks that the copy matches the lock. | Medium |
| R3-3 | Pleasanter preparation is undocumented. The receiver must create a parent folder, one group and one user per role, and an API key per user, then map the IDs into `principals`. | High |
| R3-4 | Where the agent runs is not stated. A cloud agent (Cowork) has no network path to Pleasanter and falls back to the browser runner and base64, which is token-heavy. The demo must use Claude Code on a machine that can reach Pleasanter. | High |
| R3-5 | No token rules. An agent may read whole `releases/*/payload-*.json`, rollback or export files instead of the `pls` summaries. | Medium |
| R3-6 | The framework repository is not clean for a newcomer:<br>• `README.md` status says v0.1/v0.2.<br>• `CLAUDE.md` still points at spike-era `scripts/common.py` and `config.json`.<br>• `spike/`, `patterns/ai-gateway`, `evals/results/*` and the session-log style `HANDOFF.md` sit next to the core. | Medium |

## Proposals (minimum to demo)

| # | Proposal | Requirement | Plan item |
|---|---|---|---|
| 1 | Lifecycle runbook: project `CLAUDE.md` template + orchestration skill `pls-x-lifecycle` (phases, gate stops, exact `pls` commands, token rules) | R2, R3 | D1 |
| 2 | Skills `pls-p3-config-builder`, `pls-p4-test-writer` (+ test-spec reference), `pls-p5-release-manager` (+ templates for release artefacts); P6 as a short runbook step | R2 | D2 |
| 3 | `pls init` + `templates/project/`, a configurable framework path, and a skills sync and check against the lock | R3 | D3 |
| 4 | Pleasanter setup guide + `demo/` package (spec, scenario, expected stops) | R1, R3 | D4 |
| 5 | Real HTTP rehearsal on dev: init → bootstrap → apply → test | R2 | D5 |
| 6 | Clean-up: README, framework `CLAUDE.md`, move non-core folders, slim `HANDOFF.md` | R3 | D6 |
