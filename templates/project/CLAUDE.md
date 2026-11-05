# CLAUDE.md — Pleasanter project (AI-DLC)

This repository holds one Pleasanter app built with the AI-DLC framework `ai-dlc-pleasanter` (created by `pls init`). Run the tool as `python pls.py <command>` from this folder. The launcher finds the framework through `.claude/framework.lock`, or through env `PLS_HOME`.

## Start of every session

Load the skill **`pls-x-lifecycle`**. It finds where the project stands and runs the lifecycle:

P1 requirements → **G1** → P2 design → **G2** → P3 build → P4 verify → **G3** → P5 release → **G4** → P6 operate

To start a new app, the user gives a specification in natural language (any language; Pleasanter end users read Japanese). Save it and begin P1.

## Project profile

Filled in when the project is created; the lifecycle skill reads it.

| Item | Value |
|---|---|
| Stage | `demo` (one person approves every gate; customer questions are answered with the `[assumed]` defaults unless the approver says otherwise) / `project` (customer owner approves G1 and G4) |
| Release target | `dev` (P5 records the dev state as released) / `stg` / `prod` (customer-side deploy, ADR-0003) |
| Approvers | G1, G4: <name>; G2, G3: <name> |
| Role tests | `deferred` (one key, the operator's: restrictions are verified in the configuration, not as each role; demo stage) / `per-role keys` (a test user and key per restricted role, TD-11) |

## Hard rules

1. **You never approve a gate.** At G1–G4 you present the evidence, ask and wait. You record the decision only after the person states it.
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
| `design/` | `decisions/DES-*.md`, `probes/`, `slot-ledger.json` |
| `config/<site>/` | desired configuration (unpacked): `site.json`, `meta.json`, scripts, `permissions.json` |
| `environments.json` | environments: role, `parent_id`, site ids, principals |
| `tests/api/` | test specs; `tests/results/` results |
| `releases/` | bootstrap and release plans, reports, approvals |
| `ops/drift/` | drift baselines and decisions |
| `traceability.json` | REQ → design → config → tests |
| `.pls/` | gitignored: connection, exports, local files |

Language: project documents in English; questions for the customer, labels and messages for Pleasanter end users in Japanese.
