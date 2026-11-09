# CLAUDE.md — Pleasanter project (AI-DLC)

This repository holds one Pleasanter app built with the AI-DLC framework `ai-dlc-pleasanter` (created by `pls init`). Run the tool as `python pls.py <command>` from this folder. The launcher finds the framework through `.claude/framework.lock`, or through env `PLS_HOME`.

## Start of every session

Load the skill **`pls-x-lifecycle`**. It finds where the project stands and runs the lifecycle:

P1 requirements → **G1** → P2 design → **G2** → P3 build → P4 verify → **G3** → P5 release → **G4** → P6 operate

How a project starts depends on its **Origin** (profile below):
- `new` — an app that does not exist yet: the user gives a specification in natural language (any language; Pleasanter end users read Japanese). Save it and begin P1.
- `existing` — an app that already runs in Pleasanter (運用保守): first `pls-x-onboarding` (read only) and `pls-x-spec-recovery`. **No P1 before the onboarding summary exists** (`ops/onboarding/*-summary.md`); then every change is a change request through P1–P6.

If Origin is `new` but the person names an app, site ids or a site package that already run in Pleasanter, ask whether this is a takeover before writing anything.

## Project profile

Filled in when the project is created; the lifecycle skill reads it.

| Item | Value |
|---|---|
| Origin | `new` (the app is built by this project) / `existing` (the app already runs in Pleasanter and is taken over) |
| Stage | `demo` (one person approves every gate; customer questions are answered with the `[assumed]` defaults unless the approver says otherwise) / `project` (customer owner approves G1 and G4) |
| Release target | `dev` (P5 records the dev state as released) / `stg` / `prod` (customer-side deploy, ADR-0003) |
| Approvers | G1, G4: <name>; G2, G3: <name> |
| Operators | dev: <name>; stg: <name>; prod: <customer operator> |
| Role tests | `deferred` (one key, the operator's: restrictions are verified in the configuration, not as each role; demo stage) / `per-role keys` (a test user and key per restricted role, TD-11) |

## Hard rules

1. **You never approve a gate.** At G1–G4 you present the evidence, ask and wait. You record the decision only after the person states it, with `pls gate` (approver from this profile, their words as `--quote`).
2. **Writes only to environments `pls` allows:** `role: dev`, or stg after G4, with `allow_write: true` in the operator's `.pls/connections.json`. Never change roles or `allow_write` to get past a refusal. Never write to prod.
3. **`pls apply` / `pls bootstrap` need the person:** they run the command, or they tell you to add `--yes` for that target. Never add `--yes` on your own.
4. **No keys, secrets or business data in git or chat.**
   - Keys live in environment variables or in key files under `.pls/`.
   - Test credentials live in `tests/seed/`, which is gitignored.
   - Never ask for a key in chat.
5. **Do not guess Pleasanter behaviour.** Use `pls-kb-pleasanter`; probe on dev when it is silent.
6. **Standard settings before code (I5).** A server script needs a written reason in the design.
7. Commit locally at the end of each phase and after each gate decision. Do not push unless asked.

## Token rules

- Read the output of `pls` commands, not the files they write. Never open payload, rollback, export or test-result JSON files whole.
- Use the HTTP commands of `pls`. The browser runner (base64 through the chat) is a last resort; tell the person first.
- Summarise; do not paste long output back to the person.

## Layout

| Path | Holds |
|---|---|
| `requirements/` | `sources/` (spec verbatim), `REQ-*.md`, `index.md` (status + questions) |
| `design/` | `decisions/DES-*.md`, `probes/`, `slot-ledger.json`, `roles.json` (permission design: roles → groups) |
| `config/<site>/` | desired configuration (unpacked): `site.json`, `meta.json`, scripts, `permissions.json` |
| `environments.json` | environments: role, `parent_id`, site ids, principals |
| `tests/api/` | test specs; `tests/results/` results |
| `releases/` | bootstrap and release plans, reports, approvals |
| `gates/` | one record per gate decision (`pls gate`): approver, their words, items or release |
| `ops/drift/` | drift baselines and decisions |
| `traceability.json` | REQ → design → config → tests |
| `.pls/` | gitignored: connection, exports, local files |

Language: project documents in English; questions for the customer, labels and messages for Pleasanter end users in Japanese.
