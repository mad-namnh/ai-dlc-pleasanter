# AI-DLC for Pleasanter — Architecture

Version 0.3 (2026-11-05) — updated after vertical slices #1–#3 (`docs/slices/slice-0{1,2,3}-report.md`). Stage: **test / demo** — the framework is being shaped on MADLAB dev with role-played customers; prod-stage items (customer questions, prod environment, real groups, mail) are deferred. This document is the frame of the framework. Every skill, agent, hook, check and tool must map to a phase, an artifact or an invariant described here. If something does not fit, change this document first (via an ADR) — do not build around it.

## 1. Purpose and scope

**The framework is:** a standard way for MADLAB teams to use AI across the whole lifecycle of a Pleasanter project — **requirements → design → build → verify → release → operate** — with humans approving at fixed gates.

**The framework is not:**
- a set of AI features inside customer applications (see `patterns/` for reusable app-level solutions such as `patterns/ai-gateway/`);
- a replacement for Pleasanter's UI for the customer — the customer may keep editing configuration; the framework detects and reconciles it.

**Users:**
- MADLAB engineers (Japan + Vietnam), working with AI agents (Claude Code).
- The MADLAB PM / tech lead, who approves at gates.
- The customer, who approves requirements (G1) and releases (G4), and may edit configuration directly.

## 2. Invariants

These rules hold in every phase. Each one is enforced by a deterministic check or a gate, not by trust.

| ID | Invariant | Enforced by |
|---|---|---|
| I1 | **Git is the desired state; Pleasanter is the runtime.** Every managed site exists in the project repository as unpacked configuration | Round-trip (spike B4), `pls drift` |
| I2 | **A deploy always sends the complete configuration and is preceded by a drift check.** `updatesite` replaces SiteSettings entirely (D4) | `pls plan` refuses partial payloads; refuses to plan while unresolved drift exists |
| I3 | **AI has no path to production and holds no production credentials** | Network isolation; production deploy runs inside the customer network (ADR-0003); write guard in tooling |
| I4 | **Humans approve at gates G1–G4; AI never approves its own work** | Gate records in `gates/`, written by `pls gate` with the approver's words and required by `release-plan` (G3) and `apply` / `bootstrap` / `migrate` (G4) outside dev, and `package` (G4) always (ADR-0020); P4 reviewer agents, when built, are read-only |
| I5 | **Standard features before code.** Standard settings → formulas/プロセス (process)/ステータス制御 (status control) → server script → extended SQL → external integration. Climbing a rung requires a written reason | Design review (P2), over-coding reviewer (P4) |
| I6 | **Deterministic checks decide; AI explains.** Diffs, classifications and coverage are computed by code; AI only rewrites them into business language (B3) | `pls diff`, `pls classify`, `pls coverage` |
| I7 | **No secrets and no customer business data in git.** Configuration holds references only (`${secret:…}`, `${env:…}`) | Lint L-SEC-01, and a refusal before writing in `unpack`, `harvest`, `adopt` and `release-plan` (D5, ADR-0005); no CI yet |
| I8 | **Every requirement is traceable to configuration and tests, and back** | Traceability ledger; coverage check at G3 |
| I9 | **Every escaped defect becomes a rule, check, skill change or eval** | Operate phase feedback loop (P6 → framework) |

## 3. Repositories and environments

### 3.1 Two kinds of repository

| Repository | Owner | Contains | Never contains |
|---|---|---|---|
| **Framework** (`ai-dlc-pleasanter`, this repo) | MADLAB | Architecture, ADRs, `pls` toolchain, check rules, skill/agent/hook templates, project template, evals, patterns | Customer configuration or data |
| **Project** (one per customer system) | MADLAB + customer | Requirements, design, unpacked configuration, tests, environment maps, release records, ops records | Secret values, business data |

### 3.2 Project repository layout

Machine-read files are JSON (stdlib only). Reference implementations: `pls-demo-inquiry` (changes to existing sites: slices #1, 1.5, #2) and `pls-demo-equipment` (a new app: slice #3).

The tree is checked by a test (`tools/pls/tests/test_architecture_project_layout_matches_what_pls_creates_and_names.py`): it holds everything `pls init` creates and every name `pls` joins into a project path, and it names nothing that neither `pls`, a skill nor the project template names. One name per line; `<…>` marks a part that varies. The comments are not checked.

```
<customer>-<system>/
├─ CLAUDE.md                      # project profile and rules, from the framework template (pls init)
├─ pls.py                         # launcher: runs the framework's pls for this project
├─ .gitignore                     # .pls/, tests/seed/, migration backups, dist/
├─ .gitattributes                 # config/, releases/, migrations/ are stored byte for byte
├─ .claude/
│  ├─ skills/                     # skills installed from the framework (pls skills sync)
│  └─ framework.lock              # framework path and commit, version and hash of every installed skill (ADR-0022)
├─ requirements/
│  ├─ sources/                    # what the customer gave, verbatim
│  ├─ REQ-<nnn>-<slug>.md         # EARS statements, acceptance criteria, source
│  └─ index.md                    # status per requirement, open questions
├─ design/
│  ├─ decisions/
│  │  └─ DES-<nnn>-<slug>.md      # design decisions incl. ladder rung + reason (I5)
│  ├─ probes/                     # probes run for design decisions
│  ├─ as-is/
│  │  └─ <site>.md                # what an existing site does today (pls spec-skeleton; reviewed with pls review)
│  ├─ slot-ledger.json            # column-slot allocation: site → slot → logical name → zone (ADR-0002)
│  ├─ roles.json                  # permission design: roles → groups (bound with pls principals)
│  └─ refs-literal.json           # site ids in scripts that a person decided to keep as literal numbers (pls refs)
├─ config/                        # UNPACKED desired state (I1)
│  ├─ <site>/
│  │  ├─ site.json                # SiteSettings without scripts, IDs replaced by logical references
│  │  ├─ meta.json                # logical name, reference type, parent, zone
│  │  ├─ permissions.json         # optional (ADR-0006): inherit + entries with ${principal:x}
│  │  ├─ server-scripts/
│  │  │  ├─ <name>.js
│  │  │  └─ _index.json           # the settings of each script of the folder, without its body
│  │  ├─ scripts/                 # same form as server-scripts/
│  │  ├─ styles/                  # same form, .css
│  │  └─ htmls/                   # same form, .html
│  └─ _tenant/
│     └─ scheduled-scripts/       # tenant-level scheduled scripts (ADR-0010, ADR-0012)
├─ environments.json              # dev/stg/prod: base URL, role, logical name → SiteId map, ${env:} values, principals
├─ connections.example.json       # template for the operator's .pls/connections.json (ADR-0008, no keys)
├─ .pls/                          # gitignored: operator-local files
│  ├─ connections.json            # URL, allow_write and key references of this operator (ADR-0008)
│  ├─ exports/
│  │  ├─ <env>-<site>-<stamp>.json            # site exports (pls export, harvest, adopt, apply read-back)
│  │  ├─ <env>-<site>-harvest-<stamp>.json
│  │  ├─ <env>-<site>-adopt-<stamp>.json
│  │  └─ <env>-<site>-after-<release>.json
│  ├─ kb-probes-<env>.json        # state of a pls kb-verify run
│  └─ test-users/                 # pls test-users (ADR-0018): dev test users' secrets, never printed
│     ├─ <env>-<role>.password    # random password of the role's test user
│     └─ <env>-<role>.key         # its API key (connections.json keys.<role> = file:test-users/<env>-<role>.key)
├─ migrations/
│  └─ <migration>/
│     ├─ migration.json           # site, keys, data, rollback (ADR-0004)
│     ├─ dry-run.md               # log of the dry run on a copy
│     └─ backup/                  # gitignored (I7): records exported before the conversion
├─ tests/
│  ├─ api/                        # behaviour tests through the Pleasanter API
│  ├─ results/
│  │  └─ <env>-<date>-<name>-http.json        # results per environment and run (pls test)
│  └─ seed/                       # gitignored: test-user credentials for dev
├─ traceability.json              # REQ ↔ design element ↔ config path ↔ test (I8)
├─ gates/                         # the person's decisions, one file each, never overwritten (I4)
│  ├─ <date>-<gate>-<time>-<id>.json          # gate decision G1–G4 (pls gate)
│  ├─ profile/                    # profile values as the person stated them (pls profile set)
│  └─ review/                     # reviews of as-is documents (pls review as-is)
├─ releases/
│  └─ <release>/
│     ├─ plan.json                # release plan: ordered steps, snapshot refs, rollback, status
│     ├─ bootstrap.json           # plan for sites that do not exist yet (ADR-0007)
│     ├─ payload-<site>.json      # complete SiteSettings per site (I2)
│     ├─ rollback-<site>.json     # the site as it was when the release was planned
│     ├─ raw-diff-<site>.md       # live (before) against git (after), per site
│     ├─ payload.json             # single-site form of the three files above (pls plan)
│     ├─ rollback.json
│     ├─ raw-diff.md
│     ├─ scheduled-scripts/       # scheduled scripts resolved for the target, deployed by hand
│     ├─ diff-report.operator.md  # operator's report, written by pls
│     ├─ diff-report.md           # business-language summary (AI)
│     ├─ g3-verification.md       # G3 evidence
│     ├─ approvals.md             # approvals note for people; the records pls checks are in gates/
│     ├─ apply-log.json           # outcome of the apply: transport, who ran it, how it was confirmed, status
│     ├─ live-<site>.json         # what the site held after an apply that differs from the payload
│     └─ package-manifest.json    # files and digests of the customer package (pls package)
├─ dist/                          # gitignored: packages for the customer
│  └─ <release>-<env>.zip
├─ handover/
│  └─ customer-responsibilities.md            # who approves, runs, backs up and recovers on customer environments
└─ ops/
   ├─ drift/                      # drift baselines and decisions (accept / revert)
   ├─ log/
   │  └─ <day>-<actor>.jsonl      # run log of every pls command (ADR-0013)
   ├─ usage/
   │  └─ <session>.json           # LLM token usage per session (pls usage)
   ├─ adopt/
   │  └─ <date>-<env>-<site>.md   # report of an existing site brought into the project (pls adopt)
   ├─ env-compare/                # one site compared across environments (pls env-compare)
   ├─ kb-verify/
   │  └─ <date>-<env>.md          # knowledge-base probes run against an environment
   ├─ xref/
   │  └─ <site>.json              # which script uses which column and site (pls xref)
   ├─ onboarding/                 # onboarding summaries of a project taken over (Origin existing)
   └─ triage/                     # maintenance triage notes (P6)
```

**Planned, not built** (in no project today, not in the tree, not checked): `secrets.catalog.json` (secret names per environment, I7), `design/sites.md` and `design/permissions.md`, generated customer design documents (`design/設計書/`), `tests/permissions/` and `tests/smoke/`, `releases/<release>/checks.json`, `ops/incidents/` (I9).

### 3.3 Environments

| Environment | Who writes | How | Role in config |
|---|---|---|---|
| local / dev (MADLAB) | Engineers and AI agents | `pls release-plan` (plan and checks), then `pls apply`, confirmed by the person who types the release id again; write guard | `role: dev`, `allow_write: true` |
| stg (customer or MADLAB) | Release tooling only, **after G4** for that release | `pls apply` over HTTP (operator opt-in `allow_write` in `.pls/connections.json`, ADR-0008) (data migrations: `pls migrate`, before apply); the browser runner writes dev only (ADR-0014 TB-7) | `role: stg` — no ad-hoc writes; every write is a planned release |
| prod (customer on-prem) | Customer-side runner or operator, after G4 | Same deploy package (ADR-0003) | `role: prod` — never written by `pls` HTTP; unreachable from MADLAB |

**Transport (ADR-0008).** People and workstation agents call the Pleasanter API directly with `pls` (keys from environment variables or key files under `.pls/`, never in git or chat). Agents never drive the browser runner (`tools/pls/browser/pls-runner.js`): it is a fallback for a person on dev only (ADR-0014 TB-7). An agent without a network path to Pleasanter tells the person and stops.

## 4. Lifecycle overview

```
 P1 Requirements ──G1──► P2 Design ──G2──► P3 Build ──► P4 Verify ──G3──► P5 Release ──G4──► P6 Operate
       ▲                                                                                         │
       └──────────────── change requests, drift accepted as requirements, incidents ─────────────┘
                                          └── framework feedback: new rules / checks / evals (I9)
```

| Gate | Decision | Approver | Evidence required |
|---|---|---|---|
| G1 | Requirements are right and complete enough to design | Customer business owner + MADLAB PM | `requirements/REQ-*.md` in approved state; open questions closed or accepted |
| G2 | Design is the simplest that meets the requirements; data/permission impact understood | MADLAB tech lead | Design docs, slot ledger, ladder reasons, impact classification |
| G3 | Build is correct and safe | MADLAB tech lead | All checks green, coverage 100% of in-scope REQs, reviewer-agent findings resolved |
| G4 | Release may go to the target (stg, then prod) | Customer business owner + operator | Diff report, deploy plan with rollback, drift check clean, data-migration plan if any |

The Approver column is the target. What `pls` enforces today is ADR-0020 (Proposed): one approver per record, named for that gate in the profile row Approvers; who approves G4 for `cstg` / `prod` is an open question of that ADR. In the demo stage, Nam approves every gate (acting as both MADLAB lead and customer owner). Gate decisions are recorded by `pls gate` under `gates/` (the records `pls` checks); the status lines of REQ / DES files and `releases/R-*/approvals.md` are notes for people, and lint L-GATE-01 checks that each approval they mention has its record.

## 5. Phases

Each phase lists: goal, inputs, what AI does, outputs, automated checks, gate, and current status.

### P1 — Requirements (要件定義)

- **Goal:** turn customer intent into testable requirements.
- **Inputs:** meeting notes, emails, tickets, screenshots, existing site configuration (for change requests), drift accepted in P6.
- **AI does:**
  - `pls-p1-requirements-analyst`: extracts requirements as **EARS** statements, assigns REQ IDs, writes acceptance criteria.
  - When the input is only a rough idea, the same skill interviews the person first (at most 3 rounds, grounded in the KB) and keeps questions and answers verbatim in `requirements/sources/<date>-interview-<slug>.md`. A requirement then names the answers it comes from; what has no source answer — including a proposal of the AI that the person did not accept — is an open question, not a requirement (I4, I8). What the person asked for and the KB does not cover is a requirement marked `[unverified]`, which P2 verifies before designing.
  - Flags ambiguity, conflicts with existing requirements, and missing non-functional aspects (permissions, notifications, volume, audit).
  - Produces the customer-facing question list (Japanese) for open points.
- **Outputs:** `requirements/REQ-*.md`, `requirements/index.md`, question list; in interview mode also the interview record under `requirements/sources/`.
- **Checks:** every REQ has EARS form + acceptance criteria; no duplicate IDs; open questions listed.
- **Gate:** G1.
- **Status:** **used in slices #1–#3.** Skill 0.3 passed eval cases 001 and 002. Lessons:
  - one `shall` per REQ;
  - derived requirements only protect existing behaviour;
  - check whether an existing column already covers the request (slice #2: 作業時間).

### P2 — Design (設計)

- **Goal:** decide *how* Pleasanter will meet each requirement, as simply as possible.
- **Inputs:** approved REQs, current `config/` and `design/`, slot ledger.
- **AI does:**
  - `pls-p2-solution-designer`: maps each REQ to sites/columns/views/プロセス/notifications/permissions, climbing the I5 ladder only with a written reason.
  - Allocates column slots in the ledger (ADR-0002) and detects collisions.
  - Classifies the change: config-only / data-impacting / permission-impacting (ADR-0004).
  - Generates 設計書 for the customer from the design + configuration.
- **Outputs:** `design/*`, updated `traceability.json` (REQ → design element).
- **Probes:** behaviour the design depends on and the KB does not cover is probed on dev **before G2**. A probe counts only for the configuration it reproduces. If a probe cannot run, the design takes the safe branch.
  - Example of the safe branch: process access control instead of assuming that read-only users cannot see buttons.
  - Origin: slice #2 T-015, eval case 002.
- **New sites (ADR-0007):** choose the site type and relations, run a skeleton probe, and allocate slots in zone A.
- **Checks:** every in-scope REQ has a design element; slot ledger consistent; ladder reasons present for rungs ≥ server script.
- **Gate:** G2.
- **Status:** **used in slices #1–#3.** Skill 0.5 (0.4 passed eval case 002; 0.5 adds new sites, not yet evaluated). KB `pls-kb-pleasanter` 0.7, entries D7–D27.

### P3 — Build (実装)

- **Goal:** produce the desired configuration in git.
- **Inputs:** approved design, `config/`, `environments.json`.
- **AI does:**
  - `pls-p3-config-builder`: edits `config/<site>/site.json` (columns, editor, grid, views, プロセス, notifications, permissions).
  - `pls-p3-script-builder`: writes server/client scripts following script rules (no hard-coded SiteIds — D3; no top-level `const`/`let` in shared scripts — D7; no secrets — D5).
  - Deploys to **dev** to try things, then folds any UI experiment back into git (`pls export` + `pls unpack`).
- **Outputs:** commits on a branch; `traceability.json` (design element → config path).
- **Canonicalise (slice #1, S1):** Pleasanter adds default fields and drops default-valued fields on save. After the first deploy to dev, export → unpack again so that git holds the canonical form; otherwise drift checks report false positives.
- **Checks (hooks, on every edit):** pre-tool: block writes to non-dev environments, block secret values; post-tool: schema validation, `pls lint`, reference check.
- **Gate:** none (continuous); feeds P4.
- **New sites (ADR-0007):** `pls bootstrap-plan` → create skeletons (`pls bootstrap` or runner `bootstrapSites`) → `pls bind` writes the new IDs into `environments.json` → export → unpack → build. After that, the first release is a normal `release-plan`.
- **Status:** **proven in slices #1–#3.**
  - The round trip of configuration is reliable on 1.5.2.
  - The fold-back step for canonicalisation is needed on every first deploy.
  - Principals are mapped through `${principal:x}`; `pack` refuses raw principal IDs.
  - No P3 skill yet: the agent edits `config/` by following the design.

### P4 — Verify (検証)

- **Goal:** prove the build is correct, safe and covers the requirements.
- **Inputs:** branch, dev environment, requirements, design.
- **AI does:**
  - `pls-p4-test-writer`: writes API tests from acceptance criteria and permission tests from `design/permissions.md`.
  - Read-only reviewer agents, each with a narrow view (I4):
    - `pls-p4-permission-reviewer` — permissions vs matrix;
    - `pls-p4-script-reviewer` — script rules, performance, error handling;
    - `pls-p4-over-coding-reviewer` — anything that could be standard settings instead (I5);
    - `pls-p4-coverage-reviewer` — REQ ↔ config ↔ test gaps (I8).
- **Outputs:** `tests/*`, check results, review findings.
- **Checks (CI, staged — stop on first failing stage):**
  1. Static: schema, `pls lint` (rule catalogue §7.2), secrets, slot collisions
  2. Deploy to an ephemeral or dev environment
  3. API tests + permission matrix
  4. Smoke (Playwright, few flows)
  5. Coverage: every in-scope REQ has config and a passing test
- **Gate:** G3.
- **Role tests (TD-11, TD-13):** each restricted role is tested with a user of that role, through the API and, for buttons, the edit screen. Slice #2 T-015 caught a wrong KB entry this way.
  - Over HTTP, `pls test` picks the key per step (`as_key`).
  - The browser runner sends every request as the logged-in user and refuses a spec or step with `as_key`: role tests run with `pls test`.
- **Status:** **in use.**
  - `pls lint` and `pls coverage` run.
  - Test specs (`tests/api/*.json`) cover create, process exec, get/list with expectations, negative creates (`expectHttp`), fixtures (`spec.vars`) and UI checks for button presence. They run through `pls test` (HTTP) or the runner `runTests` (differences: ADR-0008). `pls test` writes only to the sites `environments.json` lists as the environment's own (never another application's site id, never a sandbox's shared site; ADR-0011). Outside dev, tests that change records need the G4 of the release under test (`--release`) or the person's confirmation (ADR-0008).
  - Not built: reviewer agents, Playwright smoke, CI.

### P5 — Release (リリース)

- **Goal:** change the target environment exactly as approved, with a way back.
- **Inputs:** G3-approved commit, target environment.
- **AI does:**
  - `pls-p5-release-manager`: turns the deterministic diff into a business-language report (Japanese for the customer), explains data/permission impact, drafts release notes.
- **Tooling does (deterministic):** `pls drift` against the **last released payload** (S2; must be clean or resolved) → `pls plan` (ordered steps by site dependency, complete payloads, snapshot, rollback) → deploy package.
- **Outputs:** `releases/R-*/` (plan, diff report, checks, approvals). After an apply the folder also says who ran it and how it was confirmed (`apply-log.json`: `executed_by`, `confirmed`; the name is the run-log actor, self-asserted), what the read-back found (`plan.json` `readback_evidence`: per site the state and the sha256 of the live content and of the payload; `apply-log.json` `final_status` = the plan's status). Undoing an applied release is a new release until ADR-0015 (Proposed) is decided.
- **Checks:** drift clean; plan contains complete SiteSettings only (I2); data-impacting changes have migration + dry-run; post-deploy smoke + round-trip export equals git.
- **Gate:** G4.
- **Data-impacting changes (ADR-0004):** a migration folder has a backup, a dry run on dev and a rollback. It runs before the configuration change, in the same release window (ADR-0004 order: backup → conversion → configuration), with `pls migrate` over HTTP (one `bulkupsert` with keys per folder; `apply` refuses until it has run).
- **Status:** **proven on stg in slices #1–#3.** The release sequence:
  1. `release-plan` checks drift, slots and the migration gate, and orders multi-site releases by dependency.
  2. `applyRelease` / `pls apply` runs a preflight on `UpdatedTime`, applies in order and restores automatically on failure.
  3. Migrations run.
  4. Export → `mark-applied`, which requires a round trip with 0 differences.
  5. Smoke tests.

  The business-language diff report is written by the agent from the raw diff. Not built: `pls-p5-release-manager` as a separate agent, and the customer-side deploy package (ADR-0003).

### P6 — Operate (運用)

- **Goal:** keep production and git in agreement, and learn from what goes wrong.
- **Inputs:** scheduled exports, customer change requests, incidents.
- **AI does:**
  - `pls-p6-ops-watcher`: explains drift in business terms and proposes *accept* (becomes a requirement/PR) or *revert*.
  - Intake of customer change requests into P1.
  - Incident analysis → proposes a new lint rule, check, skill change or eval (I9).
- **Outputs:** `ops/drift/*`, `ops/incidents/*`, framework issues.
- **Checks:** periodic drift report; incident records reference the rule they produced. Drift resolution always goes through `pls classify` — reverting customer edits can itself be data-impacting (S3).
- **Gate:** accept/revert decisions by tech lead; customer informed via drift report (B2).
- **Status:** **partly proven.**
  - `pls drift` compares the live site with the last applied release.
  - Slice 1.5 carried an accepted drift on stg (優先度 「緊急」) through P6 → P1 → P5.
  - Slice #3 recorded a drift baseline of 0 on stg.
  - Not yet exercised: drift on permissions or on a process ACL, scheduled exports, and incident records.

## 6. Traceability model

One file, `traceability.json`, links the chain in both directions:

```json
{
  "REQ-001": {
    "design": ["DES-001"],
    "config": ["config/inquiries/site.json#Processes[escalate]", "config/inquiries/site.json#Columns[DateC]"],
    "tests": ["T-001"]
  }
}
```

`pls coverage` computes gaps; the `pls-p4-coverage-reviewer` agent explains them.

## 7. Components

### 7.1 `pls` toolchain (framework, deterministic)

**Project files are read through one loader per kind** (design review C3). `environments.json`, release records (`plan.json`, `bootstrap.json`), `.pls/connections.json`, gate / profile / review records, `_index.json`, migration files and the profile are read as UTF-8 with a BOM tolerated; a missing, unreadable, non-UTF-8 or non-JSON file, or a field of the wrong type that a guard reads (`envs`, `sites`, `per_site`, `steps`, `rollback`, `keys`, …), is a refusal that names the file and the field before anything is written, never a traceback. Which fields a command needs stays that command's own refusal.

**Portability (design review G1, G2).** Minimum Python 3.10, checked at start-up; the suite is run on 3.10 and on the current Python before a release. Every file `pls` writes has LF line endings on every OS (script bodies are byte for byte), so running a command on another OS never rewrites whole files; the framework repository's `.gitattributes` stores and checks out text with LF.

| Command | Phase | Purpose | Status |
|---|---|---|---|
| `pls export` | P3, P6 | Read site configuration from an environment | **0.5** over HTTP (ADR-0008); browser runner `exportSite` as fallback |
| `pls http-check` | all | Check connection, key and role of an environment | **0.5** |
| `pls package` | P5 (ADR-0003) | Zip a G4-approved release for the customer's operator: release files, migration folders without `backup/`, the G4 record, a manifest of sha256, `CHECKLIST.md` and a standard-library `verify.py` that refuses an altered file, an added file, a wrong target or release, or content the G4 record did not approve; deterministic zip | branch |
| `pls migrate` | P5 (ADR-0004) | Send the explicit data of each migration folder of a release with one `bulkupsert`: write guard, G4 on non-dev (digest covers the folder), mail / job checks, typed confirmation, run recorded in `plan.json` before the call; `--rollback` sends `rollback.data` prepared by a person | branch |
| `pls apply` / `test` / `backup` | P4, P5 | Apply a planned release (preflight, ordered, automatic restore); run test specs (per-step key); back up all records of a site | **0.5** over HTTP; runner `applyRelease` / `runTests` / `backupRecords` as fallback for a person on dev (ADR-0014 TB-7) |
| `pls setup` | before P1 (once per machine and environment) | Save a machine profile — URL, folder, ids by name, key file outside the repositories — that `pls init` applies to every new project; writes on that environment only when the person answers yes to setup's question (default no; ADR-0021, ADR-0014 TB-10; `docs/setup.md`) | built (2026-11-05) |
| `pls init` / `skills check|sync` | P1 (new project) | Create a project from `templates/project` (CLAUDE.md with profile, layout, launcher `pls.py`, skills + lock with hashes); check or upgrade the project's skills against the lock and the framework (the message names the direction by version: newer, older, or changed at the same version); `step` / `gate` print a WARNING when a project copy was edited (never refuse) | **0.6** |
| `pls bootstrap-plan` / `bootstrap` / `bind` | P3, P5 | Create skeleton sites for a new app and bind their IDs per environment (ADR-0007) | **0.4–0.5** |
| `pls principals` | P3 (after G2) | Bind the roles of `design/roles.json` to group / user ids of an environment by exact name; a name that matches several groups is refused; exit 1 while a role has no id. `--create` (dev only, not a sandbox, typed confirmation): creates the missing groups with the operator as member first (ADR-0017) | built (2026-11-05); `--create` 2026-11-11 |
| `pls test-users` | P3 (after `pls principals`), before P4 role tests | Dev only (not a sandbox, writes allowed, typed confirmation): for each Group role of `design/roles.json`, a test user `zz_test_<project>_<role>` (random password in `.pls/test-users/`), its API key issued through the screens only on a version where KB D32 is verified (else a person issues it, exit 1), `keys.<role>` added to `.pls/connections.json` when absent (never replaced), and the user added to the role's group by read, add, write, check (ADR-0018 option C, ADR-0019 option B). Removal and rotation: TD-24 | built (2026-11-11) |
| `pls unpack` / `pack` | P3 | Site JSON ↔ readable tree; scripts as files; IDs ↔ logical references; secrets → references | **v0.1** (`tools/pls/pls.py`); secret → reference not yet |
| `pls lint` | P3, P4 | Rule catalogue §7.2 | built — the rules it reports are listed in §7.2 only |
| `pls diff` | P4, P5 | Structured diff, deterministic (B3) | **v0.1** — keyed by ColumnName/Name/Id; scripts not line-level yet (S6) |
| `pls classify` | P2, P5 | config-only / data-impacting / permission-impacting (ADR-0004); summaries → data-impacting (D16); permissions and process access control → permission-impacting | **0.4** |
| `pls coverage [--env E]` | P4 | REQ ↔ design ↔ config ↔ test gaps for one environment (default dev): covered only when the design documents and config elements exist and every linked test passed **in that environment** (latest run per test); `api-only`, `failed`, `error`, `not-run` counted apart; an empty `traceability.json` is a gap | **v0.1**; per environment since 2026-11-10 |
| `pls drift` | P5, P6 | Live vs **last applied release** (D11); reports whether reverting is data-impacting | **v0.2** |
| `pls slots` | P5, P6 | Column-slot check: live target vs git vs slot ledger (A2, ADR-0002) — collision, slot used outside the ledger (incl. editor-only slots), repurposed label, git slot not allocated | **v0.3** |
| `pls plan` / `release-plan` | P5 | Ordered, complete-payload deploy with snapshot and rollback (A3, D4); **refuses on unresolved drift and on column-slot findings** (missing ledger = refused) | **v0.3** — `pls plan` (one site) and `pls release-plan` (several sites: order by `${site:x}` dependencies, per-site snapshot + rollback, reverse-order restore, nothing written if any site fails). Runner `applyRelease`: preflight on `UpdatedTime`, ordered apply, automatic restore on failure; smoke tests still run by hand (`runTests`) |
| `pls canon` | P3 | Apply Pleasanter's save-time normalisation (`tools/pls/canonical-defaults.json`, D8) | **v0.2** |
| `pls mark-applied` | P5 | Record a release as applied only after verifying live == payload | **v0.2** |
| `pls version` | all | Version label per environment: build token and schema detected, application version recorded by a person or from a site package; names the KB entries not verified on that version, as `release-plan` does in its `VERSION` lines (ADR-0009) | branch `brownfield-adr` |
| `pls kb-verify` | KB (I9) | Run the KB probes on a dev environment in a probe folder; result per entry and version (ADR-0009). Also the step that turns a source-derived shape into verified knowledge before any project deploys it (ADR-0023, `skills/pls-x-lifecycle/references/kb-gaps.md`) | branch |
| `pls adopt` | before P1 (existing app) | Read-only take-over of an existing site: config, customer-zone ledger, adoption record (drift baseline), report | branch |
| `pls env-compare` | onboarding, P6 | One site across environments (exports, UI site packages, git), ids mapped, differences classified | branch |
| `pls refs` / `xref` | P2, P3 | Site ids inside scripts (literal decisions by a person); scripts ↔ columns ↔ sites index for impact analysis | branch |
| `pls sandbox` / `harvest` / `merge-site` / `merge-install` | P3 (several developers) | Per-developer sandbox environments (every plan refuses a copy that writes to a shared site unless a person accepted that place), UI edits back into git, semantic merge of `site.json` (ADR-0011) | branch |
| `pls adopt-package` | onboarding | Every site of a UI site package in one read-only run (names from the project or a person's file) | branch |
| `pls spec-skeleton` | onboarding, P1 | As-is 画面設計書 tables from the configuration; the LLM writes only marked places | branch |
| `pls step` / `pls usage` | all (ADR-0013) | Step markers in the run log; LLM tokens per step from Claude Code transcripts; `usage report` warns about a session that did P1–P4 work after a G4 (one session per change request) | branch |
| `pls jobs-verified` | P5 (ADR-0012, ADR-0020) | Record that an operator of the release's env (profile row `Operators`) or a G4 approver deployed and checked its scheduled scripts by hand; until then the next release lists them again | branch |
| `pls profile set` | I4 (ADR-0020) | Set profile rows Approvers / Operators / Origin or an environment `role` as the person stated it; recorded under `gates/profile/`; once recorded, the recorded value is what `pls` reads (a hand edit changes nothing, L-PRF-01) | branch |
| `pls review as-is` | onboarding (I4, I5) | Record that a G2 approver reviewed `design/as-is/<site>.md`, bound to its sha256; only then does `DES-000-as-is-<site>.md` clear L-LAD-01 | branch |
| `pls gate` | G1–G4 (I4) | Record a gate decision by a named approver; `apply` to stg/prod refuses without G4. A G4 approval stores the digest of each planned release (`pls_release_digest`); a release changed after G4 is refused | branch |

Planned, not built (not a command of `pls`): `validate` — JSON schema derived from real exports (P3, P4).

The first column of this table is checked against the parser of `tools/pls/pls.py` by `tools/pls/tests/test_architecture_tables_match_the_parser_and_lint_rules.py`: a command the parser does not have, or a parser command without a row, fails the suite. Sub-actions (`skills check|sync`, `profile set`) and the other columns are not checked.

### 7.2 Lint rule catalogue (seeded from findings)

**Rules `pls lint` reports.** The same test checks this table against the rule codes of the issues the lint code builds: a rule lint cannot report, or a reported rule without a row, fails the suite.

| Rule | Source | Checks |
|---|---|---|
| L-SEC-01 | D5 | No secret-like values in configuration or scripts. Also a refusal before writing: `unpack`, `harvest`, `adopt` (config/) and `release-plan` (payload from config/, rollback from the live site) write nothing when one is found |
| L-REF-01 | D3 | No raw site id written as a site id (`…SiteId = 797`, `items.Get(797`, `/items/797/`); other numbers equal to a site id are not ids |
| L-REF-02 | S5, B2 | Every `${site:x}`, `${env:x}` and `${principal:x}` in the configuration is defined for every environment; scheduled scripts resolve for every environment that can receive them |
| L-REF-03 | D3 | No `${site:x}` outside a site-id context unless recorded (`pls refs --ref`): the next unpack would turn it back into a number |
| L-REF-04 | E4 | No `${env:x}` inside longer text when its value is a number or shorter than 6 characters: unpack maps such a value back only as a whole value (ADR-0005) |
| L-SCR-01 | D7 | No top-level `const`/`let` in shared server scripts |
| L-SLOT-01 | A2 | Column slots in git match the slot ledger |
| L-LAD-01 | I5 | Server scripts / extended SQL have a design decision with a ladder reason: a `design/decisions/DES-*.md` that names the script **and** its site as whole names (a name inside a longer word, a decision about another site, or any other file under `design/` does not count). Shared server scripts are not checked (open: decide in an ADR). `design/as-is/` documents decide nothing; `DES-000-as-is-<site>.md` counts only for scripts named in a reviewed, unchanged as-is document (`pls review as-is`) |
| L-CAN-01 | D8 | Configuration is in Pleasanter's canonical form |
| L-PERM-01 | D15, ADR-0006, ADR-0023 | `permissions.json`, process access control and mail addresses of notifications / reminders (`[${principal:x}]`) use only `${site:x}` / `${principal:x}` — no environment-specific IDs (also refused by `pack`) |
| L-SCR-02 | BR7 | Server and client scripts compile (node, nothing is run) |
| L-MAIL-01 | ADR-0010 | No literal mail address in notifications or reminders |
| L-ENV-01 | `docs/setup.md` | Environment setup is finished: no principal id left as a `<…>` placeholder, no `parent_id` of 0 |
| L-ENV-02 | ADR-0010 | `side_effects` values are known states |
| L-JOB-01 | ADR-0012 | Scheduled scripts: `_index.json` is a list with unique names, and every entry has a body (and every body an entry) |
| L-ONB-01 | lifecycle §0 | Origin `existing` without `ops/onboarding/*-summary.md`: no `REQ-*` / `DES-*` documents. The same check refuses `pls step` P1–P5 / G1–G4, `pls gate`, `bootstrap-plan` and `release-plan` |
| L-MRG-01 | ADR-0011 | No unresolved semantic-merge conflict in `site.json` |
| L-PRC-01 | D21 | Every process has a `View` object (none → API 500, record screen fails) |
| L-GATE-01 | I4 | A gate status written in a REQ, DES or G3 record has a matching `pls gate` record by an approver of the profile; a damaged gate record is reported here |
| L-PRF-01 | I4 | Profile rows Approvers / Operators / Origin and environment roles (`stg`, `prod`) have a `pls profile set` record, and the files still show the recorded value |

**Checks made by other commands — never in the output of `pls lint`** (not checked by the test):

| Check | Source | Checks |
|---|---|---|
| L-DEP-01 | D4 | Deploy payload contains complete SiteSettings |
| L-SLOT-02 | A2 | **Pre-deploy** (in `pls plan` / `pls slots`): slots used on the live target agree with the ledger and git — blocks the plan |
| P-MIG-01 | A1, ADR-0004 | `plan` / `release-plan` refuse a data-impacting change without a migration folder (`migration.json`, `backup/`, `dry-run.md`) |

### 7.3 AI assets (framework templates, installed into project repos)

Naming: `pls-<phase>-<role>` (`p1`…`p6`, `kb`, `x`) — see `CLAUDE.md`.

| Asset | Kind | Phase |
|---|---|---|
| `pls-p1-requirements-analyst` | skill | P1 |
| `pls-p2-solution-designer` | skill | P2 |
| `pls-p3-config-builder` (scripts are part of it) | skill | P3 |
| `pls-p4-test-writer` | skill | P4 |
| `pls-p4-permission-reviewer`, `pls-p4-script-reviewer`, `pls-p4-over-coding-reviewer`, `pls-p4-coverage-reviewer` | read-only agents | P4 |
| `pls-p5-release-manager` | skill | P5 |
| `pls-p6-ops-watcher` | agent | P6 |
| `pls-x-lifecycle` (+ project `CLAUDE.md` template) | skill (orchestration: phase order, gate stops, commands, token rules) | all |
| `pls-x-onboarding`, `pls-x-spec-recovery` (brownfield, branch `brownfield-adr`) | skills (take over an existing app read only; as-is specification) | before P1 |
| `pls-p3-script-engineer` (brownfield) | skill (editing legacy scripts) | P3 |
| `pls-p6-maintenance-triage` (brownfield) | skill (inquiries/incidents → cause and route) | P6 |
| `pls-kb-pleasanter` | knowledge base (Pleasanter behaviour; coverage in `skills/README.md`) | all |
| Hooks: env write guard, secret guard, post-edit lint | hooks | P3–P5 |
| Evals: sample requirements with expected designs/configs | evals | all |

Built skills, their versions and eval results: `skills/README.md` (the one source; not restated here). Eval cases are in `evals/<skill>/`, results in `evals/results/`. Grading is still done by hand. Rule: no case answer may appear in a skill. The other assets are built only when a slice needs them.

### 7.4 Observability

Usage of AI per project and phase (tokens, time, number of human corrections) is recorded, so the metrics in `docs/plan.md` can be measured.

## 8. Status summary

| Phase | Status | What exists |
|---|---|---|
| P1 Requirements | 🟢 demo | Skill `pls-p1-requirements-analyst` (version and evals: `skills/README.md`); used in slices #1–#3 |
| P2 Design | 🟢 demo | Skill `pls-p2-solution-designer` and KB `pls-kb-pleasanter` (`skills/README.md`); probes before G2; new-site design (ADR-0007) |
| P3 Build | 🟢 demo | `pack` / `unpack` / `canon` with `${site:x}` and `${principal:x}`; bootstrap and bind for new sites; skills `pls-p3-config-builder`, `pls-p3-script-engineer` |
| P4 Verify | 🟡 | `lint`, `coverage`, test specs through `pls test` / `runTests`, role tests with test users; no reviewer agents, no CI, no Playwright |
| P5 Release | 🟢 demo | `release-plan` (drift, slots, migration gate, order, rollback) → `apply` / `applyRelease` → `mark-applied` (round trip 0) → smoke; proven on stg in R-20261105-01, -05 and -E03 |
| P6 Operate | 🟡 | `pls drift` against the last applied release; one accepted-drift loop (slice 1.5); no scheduled watch and no incident flow yet |

### What the slices proved

| Slice | Kind of change | Proved |
|---|---|---|
| #1 | Process + status + column on an existing site | Full P1–P6 cycle; canonicalisation fold-back (S1); drift against the last release (S2) |
| 1.5 | Customer edit on stg | Drift → accept → P1 → record-only release |
| #2 | 2 sites, 2 migrations, permissions | Multi-site ordered release with automatic restore; migration gate; permissions and process ACL in git with principals mapped per environment; role tests catch wrong assumptions |
| #3 | New app (2 new sites) | Skeleton bootstrap + bind (ADR-0007); first release from the canonical skeleton; HTTP transport (ADR-0008) first real run |

## 9. Next step

The demo-stage gaps, in order of value:
1. **P6 on a permission/ACL drift.** Simulate a customer change to permissions or to a process ACL on stg, then run classify, accept or revert, and record the result in `ops/drift`.
2. **Transport (ADR-0003 / ADR-0008):** make HTTP the default where a network path exists, and decide what the customer-side deploy package for prod looks like.
3. **Migration at volume:** run M1/M2-type migrations on a copy with realistic data. Measure duration and the rollback.
4. **Line-level script diff (S6).** Then the first reviewer agent, probably the P4 coverage or permission reviewer.
5. **Evals:** automate grading. Evaluate the current P2 version on a new-site case.

## 10. Related decisions

All decisions, their status and what is built on each: `docs/adr/README.md` (the one list; not restated here). Findings: `docs/review-findings.md`. Deferred work: `docs/tech-debt.md`.
