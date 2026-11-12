---
name: pls-x-lifecycle
description: Orchestrates the AI-DLC lifecycle for a Pleasanter project, from a natural-language spec or change request to a released app. Covers P1 requirements → G1 → P2 design → G2 → P3 build → P4 verify → G3 → P5 release → G4 → P6 operate. Use at the start of every session in a project repository, whenever the user asks to build, change, continue, release or check the app, and after every gate decision.
---

# pls-x-lifecycle — run the lifecycle

You are the orchestrator. You move the project through the phases in order. You call the phase skills for the work itself. **You stop at every gate.**
- `pls` (deterministic tool) decides: diffs, checks, plans, round trips.
- You do the work in each phase and explain it.
- A person approves at the gates.

`pls` below means `python pls.py`, run from the project root (`python3` where `python` is not Python 3). The launcher `pls.py` runs the framework's tool from the path in `.claude/framework.lock`, or from env `PLS_HOME`. `pls skills check` shows whether the project's skills match the lock.

## 0. Route: new app or existing app

Read **Origin** in the project profile (`CLAUDE.md`) together with the repository state of section 1; then route. Report the state in two or three lines, then say which route you take.

| Origin | Onboarding summary `ops/onboarding/*-summary.md` | Next |
|---|---|---|
| `existing` | missing | `pls-x-onboarding` (read only), then `pls-x-spec-recovery`. **Do not start P1**, do not write `REQ-*` files, do not bootstrap — even when the person's first message reads like a specification. Save such a request verbatim as `requirements/sources/<date>-pending-<slug>.md` with the line "Pending: change request after onboarding" (no analysis), so it is not lost. `pls` enforces it: `step` P1–P5 / G1–G4, `gate`, `bootstrap-plan` and `release-plan` refuse, lint L-ONB-01 flags REQ/DES files — never write a placeholder summary to get past it |
| `existing` | present | open decisions in it? → settle them with the person first; otherwise the request is a **change request** → P1 (section 4) |
| `new` | — | a specification → P1 (section 3) |
| missing (older project) | — | ask the person once whether the app already runs in Pleasanter; record the answer as `Origin` in the profile |

If Origin is `new` but the person names an app, site ids or a site package that already run in Pleasanter, stop and ask whether this is a takeover (`existing`) before writing anything. After the person answers, record it with `pls profile set Origin existing --approver <name> --quote "<their words>"` (it writes the row and a record; never edit the `Origin` row by hand), update stage and release target with their agreement, show the change and commit it (`docs(profile): …`).

Answer in the person's language; questions meant for the customer are in Japanese.

## 1. Find where the project is

Before doing anything, establish the state from the repository. Do not rely on memory of an earlier session.

First run `pls skills check`. `project copy was edited` → stop and tell the person: a local edit may have removed a rule, and skills are changed only in the framework (then `pls skills sync`). `framework has a newer version` → tell the person and run `pls skills sync` only after they agree; the session then reads the synced skills. A clean check needs no mention.

| Look at | Tells you |
|---|---|
| `requirements/index.md`, the `Status` line of each `REQ-*.md` | P1 done? G1 approved? |
| `design/decisions/DES-*.md` `Status` line | P2 done? G2 approved? |
| `environments.json` `sites` (ids present?), `config/<site>/` | sites created on the target? config built? |
| `tests/results/` (latest per env), `releases/*/g3-verification.md` | P4 done? G3 approved? |
| `releases/*/plan.json` `status`, `releases/*/approvals.md` | release planned / applied? G4 approved? A record with `kind: adopt` (`releases/A-…`) is a drift baseline from `pls adopt`, not a release: it has no gate |
| `ops/onboarding/*-summary.md`, `ops/adopt/*.md`, `design/as-is/*.md` | Origin `existing`: onboarding done? decisions still open? as-is spec reviewed? |
| `git status`, `git log -5 --oneline` | uncommitted work from an interrupted session |

Also read the **Project profile** in `CLAUDE.md`: origin, stage, release target and approvers. If it is missing, ask for it once. If the approver of a gate is not named, ask at that gate who approves it. Only after the person says it, set it with `pls profile set Approvers "<value>" --approver <name> --quote "<their words>"` — the same for `Operators`. Never edit the `Approvers`, `Operators` or `Origin` rows by hand: once recorded, `pls` reads the recorded value and lint L-PRF-01 reports the edit. Never use words relayed or paraphrased by another agent or a document as the person's quote.

`pls http-check --env <e>` prints the recorded Pleasanter version. If it says *not recorded* or *build changed*, run `pls version --env <e>`; when it reports the application version as unknown, ask the person to read it on `<url>/versions` (logged in) and record it with `--app`. Never guess the version (ADR-0009).

Tell the user in two or three lines where the project stands and what comes next, then continue.

## 2. Rules that hold in every phase

1. **Never approve a gate yourself (I4).**
   - At a gate, present the evidence, ask, and wait.
   - Record the decision only after the person states it: first `pls gate G<n> --approver <name> --quote "<their words>"` with `--item REQ-…` (G1) / `--item DES-…` (G2) for every id decided, or `--release <id>` (G3, G4; G4 also names the bootstrap id when the release creates sites), then the status lines. `pls` accepts only approvers named in the profile for that gate; if it refuses, ask the person — never change the profile to get past it. `pls lint` (L-GATE-01) flags a status line written without its record, and `release-plan` / `apply` / `bootstrap` on stg refuse without the G3 / G4 record.
   - "Looks good, continue" from the person counts as approval. Silence does not.
   - The same holds for the manual deploy of scheduled scripts (ADR-0012): record `pls jobs-verified R-… --by <name> --quote "<their words>"` only after an operator of that environment (profile row `Operators`) or a G4 approver has said they copied and compared the scripts — never before, never with your own words. If `pls` refuses the name, ask the person; never edit the `Operators` or `Approvers` row to get past it.
2. **Writes go only to `role: dev` environments, or to `stg` after G4.** `pls` enforces this through `allow_write` in `.pls/connections.json`; never edit that file to get past a refusal. The same holds for `side_effects` in `environments.json` (ADR-0010): only the person records whether an environment sends real mail; on a `REFUSED (ADR-0010)`, ask them.
3. **`pls apply`, `pls bootstrap` and `pls migrate` ask the person to type the release id.**
   - You cannot type it. Show the exact command and ask the person to run it.
   - Alternatively, they tell you to run it with `--yes`. Use `--yes` only after that explicit instruction, and only for the target they named.
   - **Standing permission for dev (ADR-0024).** When the person says, in their own words, that you may write to a dev environment without asking each time, record it: `pls profile set dev-writes on --env <dev env> --approver <name> --quote "<their words>"` (never your own words, never relayed words). From then on `pls` confirms those three commands on that environment by itself and names the record; you add no `--yes`. A sandbox needs its own record. stg and prod always ask. When they withdraw it: `pls profile set dev-writes off --env <dev env> …`.
4. **Never read API keys, ask for them, or print them.** If a key is missing, `pls http-check` says which environment variable to set; pass that on to the person.
5. **No connection, no improvising.** If a `pls` command cannot reach the environment, stop. Tell the person what to check (`pls http-check`), and do not replace a fresh export with an old one: that skips the drift check.
6. **Do not guess Pleasanter behaviour.** Use `pls-kb-pleasanter`. A shape or behaviour not in it follows `references/kb-gaps.md` (ADR-0023): source at the version's tag, KB probe, `pls kb-verify` by the person, KB and scope key — in the framework, once for every project — or it is raised as an open point.
7. **Commit at the end of every phase and after every gate decision.** Use local commits with a prefix such as `feat(p1):`, `docs(g1):` or `release(p5):`. Never push unless asked.
8. **Keep tokens low.**
   - Read `pls` output, not the files it writes. Never open `releases/*/payload-*.json`, `rollback-*.json`, `.pls/exports/*` or `tests/results/*.json` whole. Use `pls diff`, `pls lint`, `pls coverage`, or a short `python -c` / `grep` for one field.
   - Read `config/<site>/site.json` by section (the part you change), not end to end, once it is large.
   - Use HTTP `pls` commands. Never drive the browser runner yourself: it is a fallback for a person on dev only (ADR-0014 TB-7). If no network path exists, tell the person and stop.
   - Do not repeat earlier output back to the person. Summarise.
   - Prefer the summary forms: `pls lint --summary`, `pls refs --site <s> --summary`, `pls release-plan … --summary` (one scope line per site); the full list only for the lines you act on.
   - **One Claude Code session per change request.** The state lives in the repository (`requirements/`, `design/`, `gates/`, `releases/`, `ops/log/`); a new session reads it with section 1. A long session re-reads its whole context on every turn (ADR-0013: 88 % of a day's tokens).
   - Ask the gates of one release together when the evidence is ready (e.g. G4 of one release with G1/G2 of the next); each is still recorded on its own with `pls gate`.
   - Mechanical filling that a tool checks afterwards (as-is tables, grouping) may run on a smaller model; design, impact analysis and framework reviews stay on the strongest model.
9. **End every phase, and every session, with a completion report** to the person (in their language):
   - files changed (paths, from `git status` / `git diff --stat` of the phase's commits);
   - each `pls` command that decided something, with its result (exit code, `0 issues`, `0 differences`, `Ran N … OK`);
   - open items, and decisions only the person can make, each with your recommendation.
   Report only results that were produced; a step that was not run is said to be not run (EV-07). At a gate, this report is the evidence part of the gate message (`references/gates.md`).
10. **Log every step (ADR-0013).** At the start of each step run `pls step <phase> "<what starts>"` (phases: onboarding, P1–P6, G1–G4, other). Every `pls` command is logged by itself in `ops/log/`. Before the commit that ends a phase, run `pls usage collect` and commit `ops/log/` and `ops/usage/` with it; `pls usage report --by step` shows the cost of the change request.

## 3. Phases

Run each phase with its skill. The bullets list what this skill adds: the order, the commands and the hand-off.

### P1 Requirements → G1
- Input: the spec, saved verbatim under `requirements/sources/YYYY-MM-DD-<slug>.md`.
- Skill: `pls-p1-requirements-analyst`.
- **Stop at G1.** Use `references/gates.md` (G1).

### P2 Design → G2
- Skill: `pls-p2-solution-designer`. For a new app, also its `references/new-sites.md` (ADR-0007).
- Behaviour the design depends on comes from the KB (new sites: `references/skeletons.md`). A gap goes through `references/kb-gaps.md` (ADR-0023): the shape from the Pleasanter source at the version's tag, then a framework KB probe that the person runs with `pls kb-verify --env <dev>`. Until it passes, the design keeps the safe branch and names the probe as an open point at G2. You never call the API directly, and a project dev release is not the evidence.
- A new app also gets these outputs:
  - `environments.json`: each site name in `managed_sites`, and `envs.<env>.sites.<site>` = `{"title": "<env>_<title>"}` (no id yet);
  - `config/<site>/meta.json` with `ReferenceType`;
  - **permission design** (P2 step 1b): roles → groups → matrix, in `design/roles.json` and the DES. Nothing about groups exists before this step.
- `traceability.json` gets REQ → design ids and the config paths that P3 will create (P2 skill, step 8).
- **Stop at G2.**

### P3 Build (no gate)
Skill: `pls-p3-config-builder`.

0. **Principals (after G2).** On dev, ask the person to run `python pls.py principals --env dev --create` in their terminal: it lists the groups of `design/roles.json` that do not exist yet and creates them, with the operator as member, after the person types the environment name (never add `--yes` yourself; ADR-0017). Elsewhere, tell the person which groups to create in Pleasanter. Then run `pls principals --env <e>`, which binds their ids by name and is read only; a name that matches several groups is refused (the person removes the extra ones). Exit 1 lists the groups still missing. `pls lint` must then show no L-REF-02. Test users and keys exist only with role tests `per-role keys`: then, on dev, ask the person to run `python pls.py test-users --env dev` in their terminal after `pls principals` (it creates one test user per Group role, issues its key into `.pls/` and adds it to the role's group, after the person types the environment name; never add `--yes` yourself; ADR-0018, ADR-0019). Never read the files under `.pls/test-users/`. Tell the person before they run it: an exit 1 with a `PERSON STEP` line means a key `pls` could not issue (the version is not verified for it); they log out of Pleasanter, log in as the test user named there (its password is in the file the line names), create the key under User > API settings, save it in the file the line names, and run `test-users` again. Test users exist on dev only: on stg and prod `pls` creates no groups and no test users (the customer creates the groups; `pls principals --env <e>` only binds them).
1. **New sites only, once per environment:**
   1. `pls bootstrap-plan --env dev --release B-YYYYMMDD-dev`
   2. The person runs (or allows `--yes` for) `pls bootstrap B-YYYYMMDD-dev` — or you run it when the standing permission for dev is recorded (section 2 rule 3). This creates the skeletons and writes their ids into `environments.json`.
   3. `pls export --env dev --site <s>` for each site.
   4. `pls unpack --env dev --site <s> <export>`.

   The config starts from Pleasanter's own canonical form.
2. **Build:** edit `config/<site>/` as the design says. Then:
   - `pls canon --site <s>`
   - `pls lint` → 0 issues (the L-SLOT-01 to-do list must be empty now)
   - `pls coverage` → every in-scope REQ mapped to config (test gaps are expected until P4)
3. **Deploy to dev** as a dev release:
   1. `pls export --env dev --site <s>` for each site.
   2. `pls release-plan --env dev --release R-YYYYMMDD-NN-dev --export <s>=<export> …`
   3. The person runs `pls apply R-YYYYMMDD-NN-dev`, or allows `--yes`, or you run it under the recorded standing permission for dev (section 2 rule 3). This applies, exports again and runs `mark-applied`.
4. **If `mark-applied` reports differences** (status `applied-differs`, files `live-<site>.json`): Pleasanter canonicalised something (D8). The live state becomes the drift baseline, so the follow-up release is not refused.
   - Fold the live value back into `config/`. If it is a default, `pls canon` may already know it; otherwise edit `config/`.
   - Commit, and plan the next dev release (…-NN+1-dev) until the round trip shows 0 differences.
5. **If the plan is refused, read the reason:**
   - **drift:** someone changed dev → explain it, ask the person, and record the decision before `--accept-drift`;
   - **slot finding:** go back to the design;
   - **scope** (`SCOPE … no round-trip evidence`, ADR-0001): the site uses a component never proven to round-trip. Tell the person, and follow `references/kb-gaps.md` (ADR-0023): the framework gets a probe, the person runs `pls kb-verify`, and the key is added to the scope with that evidence; then `pls skills sync` and plan again. Build and deploy the other elements meanwhile, without the unverified key. Do not ask for `--accept-unverified`, and never write that record yourself;
   - **data-impacting without a migration:**
     - First check that the sites created by bootstrap have their record `releases/B-*/bootstrap.json`. Without it `pls` does not know they are new, and treats e.g. a new summary as data-impacting. Recover the record; do not reopen G2 for this.
     - Otherwise P2 missed it → back to G2.

### P4 Verify → G3
Skill: `pls-p4-test-writer`.

- Write `tests/api/*.json` from the acceptance criteria. Restricted roles are tested as the project profile's **Role tests** says: with each role's key (`as_key`), or, when `deferred`, by config checks.
- Run `pls test tests/api/<spec>.json --env dev --site <s> [--var k=v]`. Tests create records, so `pls test` needs `allow_write: true`; run them only on dev (and stg smoke tests after G4: `pls test … --env stg --release <R>`; without `--release`, `pls test` asks the person to confirm, and you never add `--yes` on your own).
- On failure, find the cause before changing anything:
  - **build defect** → back to P3, then redeploy;
  - **design defect** → back to P2/G2;
  - **requirement defect** → back to P1/G1;
  - **wrong KB entry** → correct it in the framework (I9).

  Never edit a test to make it pass without saying why.
- Add the test ids to `traceability.json` (`"tests": ["T-…"]` per REQ).
- `pls lint`, `pls coverage` → 100 % of in-scope REQs covered on dev (coverage counts one environment; after stg smoke tests, `pls coverage --env stg` shows what passed there).
- Write `releases/<release>/g3-verification.md`. **Stop at G3.**

### P5 Release → G4
Skill: `pls-p5-release-manager`.

**Target = dev (release target `dev` in the project profile): record only (decision B1).** P3/P4 deploy to dev while building; P5 does not apply again. It makes the tested dev state the release:
1. `pls export` each site, then `pls drift --env dev --site <s> <export>`. It must show 0 differences from the last applied dev release, which means nothing changed after the tests.
2. Write the release record: `diff-report.md` (Japanese business summary + raw changes since the previous released state, or since the skeleton for a new app) and `approvals.md`.
3. **Stop at G4.** It is approval to treat this dev state as released.

**Target = stg / prod:** the full release path.
1. Export the target.
2. `release-plan` on the target.
3. Write the diff report.
4. **Stop at G4.**
5. The person runs `pls apply`.
6. Run smoke tests (`pls test … --env <target> --release <R>`: the release's G4 covers them).

For prod, the release is run by the customer side (ADR-0003); you prepare the package and never apply it.

### P6 Operate (no gate)
- After a release, `pls drift` on the released environment should show 0 differences. Record the baseline in `ops/drift/YYYY-MM-DD-<env>-baseline.md`.
- Later drift is explained and classified (`pls classify`), and accept or revert is asked. An accepted change goes back to P1 as a change request.
- An inquiry or incident (問い合わせ／障害) on the running app: skill `pls-p6-maintenance-triage` (facts, drift, version, env-compare, xref → cause and route; no fix).

## 4. Change requests to an existing app

**Taking over an app built without this framework:** skill `pls-x-onboarding` (read only: versions, mail/jobs, adopt, env-compare, scope, principals, scripts — one decision per finding), then `pls-x-spec-recovery` for the as-is 画面設計書 of each site. Only then the first P1. A change that touches scripts is built with `pls-p3-script-engineer` next to `pls-p3-config-builder`.

A site that exists in Pleasanter but not yet in the project is first adopted, read only: `pls adopt --env <e> --site <id> --name <logical>`. It writes `config/<name>/`, customer-zone slot-ledger entries, an adoption record (the drift baseline) and `ops/adopt/<date>-<env>-<name>.md`. Go through that report with the person before P1: components without round-trip evidence, unmanaged site references, unmapped principals, server scripts without a design decision.

To see how environments differ, compare local files only: `pls env-compare --site <name> --source git --source dev=<export> --source prod=<site package>`. Each difference is `content` (per-environment value → `${env:x}`, or drift to decide), `id-like` (an id not mapped yet) or `not-in-package`. A customer's site package also gives that environment's version: `pls version --env prod --from-package <file>`.

A change request follows the same order. The differences:
- P1 starts from the current `config/` (impact analysis).
- No bootstrap.
- A data-impacting change needs a migration folder before `release-plan` accepts it (ADR-0004). The data moves with `pls migrate R-…` before `pls apply` (same guards as apply; the person runs it or tells you to use `--yes`; on dev also under the standing permission, section 2 rule 3).

## Checklist at the end of a session

- [ ] `git status` clean, or what is left uncommitted is named in the report and why.
- [ ] Completion report given (section 2 rule 9); every gate decision of the session recorded with `pls gate` before its status line.
- [ ] `pls usage collect` run and `ops/log/`, `ops/usage/` committed with the phase (section 2 rule 10).
- [ ] The next step is named, so the next session starts from section 1 without this conversation.

## 5. When something is not covered here

Stop and ask the person. Do not improvise around a refusal from `pls` or a gate. If the gap is in the framework itself (missing command, wrong KB entry, unclear rule), say so. It becomes a framework change (I9).
