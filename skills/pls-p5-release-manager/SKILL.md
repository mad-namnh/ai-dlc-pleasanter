---
name: pls-p5-release-manager
description: Phase P5 of AI-DLC for Pleasanter. Prepares a G3-approved build as a release for its target environment and records it. Runs the drift check and release plan, writes the Japanese business diff report and the approvals record, stops at G4, then has the release applied (stg) or recorded (dev) and verified by a 0-difference round trip and smoke tests. Use after G3.
---

# pls-p5-release-manager

**Goal:** the target environment holds exactly the approved configuration, the customer understands what changed, and there is a way back.
**`pls` decides; you explain (I6).** The plan, diff, drift and round trip are computed by the tool. You turn them into a report a business owner can approve.

## Inputs

- G3-approved `releases/<release>/g3-verification.md`, `requirements/`, `design/`.
- **Project profile** in `CLAUDE.md`: the release target (`dev` / `stg` / `prod`).
- `references/diff-report-template.md` (this skill); gate records in `pls-x-lifecycle/references/gates.md`.

An adoption record (`releases/A-…`, `kind: adopt`, written by `pls adopt`) is the state found on an environment before the project managed it. For the first change request it is "the previous released state"; it is not a release and has no G4.

## Procedure — target `dev`

The app is already on dev from P3/P4. The release makes that state official.

1. **Nothing changed since the tests:**
   1. `pls export --env dev --site <s>` (each site).
   2. `pls drift --env dev --site <s> <export>` → 0 differences against the last applied dev release.

   Drift here means someone changed dev after P4. Explain it and ask the person. Do not release over it.
2. **Release id:** the last applied dev release (`R-YYYYMMDD-NN-dev`). The record goes into its folder.
3. **Write `diff-report.md`** (template) — only the Japanese summary; `release-plan` already wrote the operator part as `diff-report.operator.md`. The raw changes are the `raw-diff-<site>.md` files written by `release-plan` for each dev release since the previous released state. For a new app that means since the skeletons.
4. **Write `approvals.md`** with G1–G3 filled in from the existing records and G4 pending. **Stop at G4.**
5. After G4:
   - record the approval;
   - add a `Released: dev, <release> (<date>)` line to each REQ in scope and `released (<release>)` in `requirements/index.md`;
   - record the drift baseline (P6, `ops/drift/<date>-dev-baseline.md`: release, sites, 0 differences);
   - commit `release(p5): …`.

## Procedure — target `stg` (or prod package)

1. **Export the target** and run `pls release-plan --env <target> --release R-YYYYMMDD-NN --export <s>=<export> … [--migration <dir>]`. The plan checks drift against the last applied release on the target, column slots, complete payloads, dependency order and the migration gate.
   - **Refused for drift:** explain it and ask the person. Planning over drift needs a decision record (`ops/drift/…`) passed as `--accept-drift`.
   - **Refused for slots:** go back to P2.
   - **Data-impacting without a migration:** go back to P2/G2. Migrations run through the browser runner today; tell the person.
2. **Write `diff-report.md`** — the Japanese summary only — from `raw-diff-<site>.md`; the operator part (order, classification, checks, rollback) is `diff-report.operator.md`, written by `release-plan`. Write `approvals.md`. **Stop at G4.**
3. After G4 — recorded with `pls gate G4 --release R-… [--release B-…]`; `apply` and `bootstrap` on stg refuse without it — the person runs `pls apply R-…`, or tells you to use `--yes` for that target.
   - It runs a preflight on `UpdatedTime`, applies in order and restores every touched site on failure. Then it exports and runs `mark-applied`.
   - `mark-applied` must report 0 differences. Otherwise stop: the release is applied but not verified. Explain the differences and fold them back (P3 step 6) with the person's agreement.
   - **If `apply` does not end applied**, `plan.json` says why. Only `planned` can be applied, so never re-run `apply` for these:
     - `rolled-back`: every touched site was restored and read back. (A browser-runner result is not read back: the person always confirms it with export + `mark-applied`.) Report the cause; the next try is a new release plan.
     - `uncertain`: a write got no answer, so the site may or may not hold the payload. Nothing was restored. **Stop.** The person exports every site of the release, then runs `pls mark-applied R-… --export …`. That records what is there: `applied`, `rolled-back` or `recovery-required`.
     - `recovery-required`: a restore failed, or the release is only partly live. **Stop and tell the person** which sites, and show the `rollback-<site>.json` files. The person restores those sites, exports every site and runs `mark-applied` again. Never fold this state into `config/`.
   - **Scheduled scripts** (`JOB` / `MANUAL` lines of the plan, ADR-0012): `pls` does not deploy them. Hand the person `releases/<R>/scheduled-scripts/` and the manual step; an operator of the environment (profile row `Operators`) or a G4 approver copies them into tenant management and compares. Only after that person says they did it, record it with their words: `pls jobs-verified R-… --by <name> --quote "<their words>" [--approved-by <G4 approver>]`. **Never run it before the person has said it, and never with your own words** (I4). Until it is recorded, the next release lists the same changes again.
4. **Migrations**, if any, in the release window. Follow the dry-run notes; the backup must exist first (ADR-0004).
5. **Smoke tests:** `pls test` with the specs named in the plan, on the target, as the roles that matter. Then record the release lines in REQs/index, the drift baseline and the commit, as for dev.

**prod:** you prepare the same package (plan, payloads, rollback, report). The customer side applies it (ADR-0003). You never connect to prod.

## Checklist before G4

- [ ] Target and release id are stated; drift is 0 (dev), or the plan was accepted by `pls` (stg).
- [ ] The diff report states, in Japanese and business words:
  - what changes for users;
  - classification and impact on existing data and permissions;
  - order;
  - rollback;
  - open items.

  Every statement traces to the raw diff.
- [ ] `approvals.md` has G1–G3 with names and dates.
- [ ] After G4: round trip 0, smoke tests pass, REQs marked released, baseline recorded.
