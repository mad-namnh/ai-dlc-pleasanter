# AI-DLC for Pleasanter — Architecture

Version 0.2 (2026-11-05) — updated after vertical slice #1 (`docs/slices/slice-01-report.md`). This document is the frame of the framework. Every skill, agent, hook, check and tool must map to a phase, an artifact or an invariant described here. If something does not fit, change this document first (via an ADR) — do not build around it.

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
| I4 | **Humans approve at gates G1–G4; AI never approves its own work** | Gate records in `releases/`; reviewer agents are read-only |
| I5 | **Standard features before code.** Standard settings → formulas/プロセス (process)/ステータス制御 (status control) → server script → extended SQL → external integration. Climbing a rung requires a written reason | Design review (P2), over-coding reviewer (P4) |
| I6 | **Deterministic checks decide; AI explains.** Diffs, classifications and coverage are computed by code; AI only rewrites them into business language (B3) | `pls diff`, `pls classify`, `pls coverage` |
| I7 | **No secrets and no customer business data in git.** Configuration holds references only (`${secret:…}`, `${env:…}`) | Secret lint at unpack, in CI and pre-deploy (D5, ADR-0005) |
| I8 | **Every requirement is traceable to configuration and tests, and back** | Traceability ledger; coverage check at G3 |
| I9 | **Every escaped defect becomes a rule, check, skill change or eval** | Operate phase feedback loop (P6 → framework) |

## 3. Repositories and environments

### 3.1 Two kinds of repository

| Repository | Owner | Contains | Never contains |
|---|---|---|---|
| **Framework** (`ai-dlc-pleasanter`, this repo) | MADLAB | Architecture, ADRs, `pls` toolchain, check rules, skill/agent/hook templates, project template, evals, patterns | Customer configuration or data |
| **Project** (one per customer system) | MADLAB + customer | Requirements, design, unpacked configuration, tests, environment maps, release records, ops records | Secret values, business data |

### 3.2 Project repository layout (target)

v0.1 uses JSON for machine-read files (stdlib only). Reference implementation: the `pls-demo-inquiry` project repository from slice #1.

```
<customer>-<system>/
├─ CLAUDE.md                      # generated from the framework template + project rules
├─ .claude/                       # skills, agents, hooks installed from the framework (pinned version)
├─ requirements/
│  ├─ REQ-001-<slug>.md           # EARS statements, acceptance criteria, source (meeting, ticket)
│  └─ index.md                    # status per requirement (draft / G1-approved / released)
├─ design/
│  ├─ sites.md                    # site map, table types, links, ownership zone per site
│  ├─ slot-ledger.json            # column-slot allocation: site → slot → logical name → zone (ADR-0002)
│  ├─ permissions.md              # role × site × operation matrix
│  ├─ decisions/DES-001-*.md      # design decisions incl. ladder rung + reason (I5)
│  └─ 設計書/                     # generated design documents for the customer (Japanese)
├─ config/                        # UNPACKED desired state (I1)
│  └─ <site-logical-name>/
│     ├─ site.json                # SiteSettings without scripts, IDs replaced by logical references
│     ├─ server-scripts/*.js
│     ├─ scripts/*.js  styles/*.css
│     └─ meta.yaml                # logical name, reference type, parent, zone
├─ environments.json              # dev/stg/prod: base URL, role, logical name → SiteId map, ${env:} values
├─ secrets.catalog.json           # secret NAMES per environment, owner — no values (I7)
├─ tests/
│  ├─ api/                        # behaviour tests through the Pleasanter API
│  ├─ permissions/                # permission matrix tests (users × operations)
│  └─ smoke/                      # few Playwright flows
├─ traceability.json              # REQ ↔ design element ↔ config path ↔ test (I8)
├─ releases/
│  └─ R-YYYYMMDD-NN/
│     ├─ plan.json                # deploy plan: ordered steps, snapshot refs, rollback
│     ├─ diff-report.md           # business-language diff (AI) + raw diff (code)
│     ├─ checks.json              # results of every automated check
│     └─ approvals.md             # G3/G4 approvers, date, scope
└─ ops/
   ├─ drift/                      # drift reports and their resolution (accept / revert)
   └─ incidents/                  # incident → root cause → new rule (I9)
```

### 3.3 Environments

| Environment | Who writes | How | Role in config |
|---|---|---|---|
| local / dev (MADLAB) | Engineers and AI agents | `pls deploy` with write guard | `role: dev`, `allow_write: true` |
| stg (customer or MADLAB) | Pipeline only, after G3 | Deploy package | `role: stg` — tooling refuses direct writes |
| prod (customer on-prem) | Customer-side runner or operator, after G4 | Same deploy package (ADR-0003) | `role: prod` — unreachable from MADLAB |

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
| G4 | Release may go to production | Customer business owner + operator | Diff report, deploy plan with rollback, drift check clean, data-migration plan if any |

## 5. Phases

Each phase lists: goal, inputs, what AI does, outputs, automated checks, gate, and current status.

### P1 — Requirements (要件定義)

- **Goal:** turn customer intent into testable requirements.
- **Inputs:** meeting notes, emails, tickets, screenshots, existing site configuration (for change requests), drift accepted in P6.
- **AI does:**
  - `pls-p1-requirements-analyst`: extracts requirements as **EARS** statements, assigns REQ IDs, writes acceptance criteria.
  - Flags ambiguity, conflicts with existing requirements, and missing non-functional aspects (permissions, notifications, volume, audit).
  - Produces the customer-facing question list (Japanese) for open points.
- **Outputs:** `requirements/REQ-*.md`, `requirements/index.md`, question list.
- **Checks:** every REQ has EARS form + acceptance criteria; no duplicate IDs; open questions listed.
- **Gate:** G1.
- **Status:** not started.

### P2 — Design (設計)

- **Goal:** decide *how* Pleasanter will meet each requirement, as simply as possible.
- **Inputs:** approved REQs, current `config/` and `design/`, slot ledger.
- **AI does:**
  - `pls-p2-solution-designer`: maps each REQ to sites/columns/views/プロセス/notifications/permissions, climbing the I5 ladder only with a written reason.
  - Allocates column slots in the ledger (ADR-0002) and detects collisions.
  - Classifies the change: config-only / data-impacting / permission-impacting (ADR-0004).
  - Generates 設計書 for the customer from the design + configuration.
- **Outputs:** `design/*`, updated `traceability.json` (REQ → design element).
- **Checks:** every in-scope REQ has a design element; slot ledger consistent; ladder reasons present for rungs ≥ server script.
- **Gate:** G2.
- **Status:** not started.

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
- **Status:** **foundation proven** — round-trip of configuration via API is reliable on 1.5.2 (spike round 1: 0 differences, idempotent). Normalize/diff code exists in `spike/round-trip/`. 7 core components still to verify (round 2).

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
- **Status:** secret scan prototype only (`spike/round-trip/scripts/scan_secrets.py`).

### P5 — Release (リリース)

- **Goal:** change the target environment exactly as approved, with a way back.
- **Inputs:** G3-approved commit, target environment.
- **AI does:**
  - `pls-p5-release-manager`: turns the deterministic diff into a business-language report (Japanese for the customer), explains data/permission impact, drafts release notes.
- **Tooling does (deterministic):** `pls drift` against the **last released payload** (S2; must be clean or resolved) → `pls plan` (ordered steps by site dependency, complete payloads, snapshot, rollback) → deploy package.
- **Outputs:** `releases/R-*/` (plan, diff report, checks, approvals).
- **Checks:** drift clean; plan contains complete SiteSettings only (I2); data-impacting changes have migration + dry-run; post-deploy smoke + round-trip export equals git.
- **Gate:** G4.
- **Status:** write guard exists in spike tooling; drift/plan/package not built.

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
- **Status:** not started.

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

| Command | Phase | Purpose | Status |
|---|---|---|---|
| `pls export` | P3, P6 | Read site configuration from an environment | Browser runner (`tools/pls/browser/`); proper transport → ADR-0003 (S4) |
| `pls unpack` / `pack` | P3 | Site JSON ↔ readable tree; scripts as files; IDs ↔ logical references; secrets → references | **v0.1** (`tools/pls/pls.py`); secret → reference not yet |
| `pls validate` | P3, P4 | JSON schema (derived from real exports) | Not built |
| `pls lint` | P3, P4 | Rule catalogue §7.2 | **v0.1** — L-SEC-01, L-REF-01, L-SCR-01, L-SLOT-01, L-LAD-01 |
| `pls diff` | P4, P5 | Structured diff, deterministic (B3) | **v0.1** — keyed by ColumnName/Name/Id; scripts not line-level yet (S6) |
| `pls classify` | P2, P5 | config-only / data-impacting / permission-impacting (ADR-0004) | **v0.1** |
| `pls coverage` | P4 | REQ ↔ config ↔ test gaps | **v0.1** |
| `pls drift` | P5, P6 | Live vs **last applied release** (D11); reports whether reverting is data-impacting | **v0.2** |
| `pls slots` | P5, P6 | Column-slot check: live target vs git vs slot ledger (A2, ADR-0002) — collision, slot used outside the ledger (incl. editor-only slots), repurposed label, git slot not allocated | **v0.3** |
| `pls plan` / `deploy` | P5 | Ordered, complete-payload deploy with snapshot and rollback (A3, D4); **refuses on unresolved drift and on column-slot findings** (missing ledger = refused) | **v0.3** — `pls plan` (one site) and `pls release-plan` (several sites: order by `${site:x}` dependencies, per-site snapshot + rollback, reverse-order restore, nothing written if any site fails). Runner `applyRelease`: preflight on `UpdatedTime`, ordered apply, automatic restore on failure; smoke tests still run by hand (`runTests`) |
| `pls canon` | P3 | Apply Pleasanter's save-time normalisation (`tools/pls/canonical-defaults.json`, D8) | **v0.2** |
| `pls mark-applied` | P5 | Record a release as applied only after verifying live == payload | **v0.2** |

### 7.2 Lint rule catalogue (seeded from findings)

| Rule | Source | Checks |
|---|---|---|
| L-SEC-01 | D5 | No secret-like values in configuration or scripts |
| L-REF-01 | D3 | No hard-coded SiteIds in script bodies |
| L-SCR-01 | D7 | No top-level `const`/`let` in shared server scripts |
| L-DEP-01 | D4 | Deploy payload contains complete SiteSettings |
| L-SLOT-01 | A2 | Column slots in git match the slot ledger |
| L-SLOT-02 | A2 | **Pre-deploy** (in `pls plan` / `pls slots`): slots used on the live target agree with the ledger and git — blocks the plan |
| L-LAD-01 | I5 | Server scripts / extended SQL have a design decision with a ladder reason |
| L-CAN-01 | D8 | Configuration is in Pleasanter's canonical form |

### 7.3 AI assets (framework templates, installed into project repos)

Naming: `pls-<phase>-<role>` (`p1`…`p6`, `kb`, `x`) — see `CLAUDE.md`.

| Asset | Kind | Phase |
|---|---|---|
| `pls-p1-requirements-analyst` | skill | P1 |
| `pls-p2-solution-designer` | skill | P2 |
| `pls-p3-config-builder`, `pls-p3-script-builder` | skills | P3 |
| `pls-p4-test-writer` | skill | P4 |
| `pls-p4-permission-reviewer`, `pls-p4-script-reviewer`, `pls-p4-over-coding-reviewer`, `pls-p4-coverage-reviewer` | read-only agents | P4 |
| `pls-p5-release-manager` | agent | P5 |
| `pls-p6-ops-watcher` | agent | P6 |
| `pls-kb-pleasanter` | knowledge base (Pleasanter behaviour: D7–D10, S7) | all |
| Hooks: env write guard, secret guard, post-edit lint | hooks | P3–P5 |
| Evals: sample requirements with expected designs/configs | evals | all |

Built (v0.1, `skills/`): `pls-kb-pleasanter`, `pls-p1-requirements-analyst`, `pls-p2-solution-designer` — each with an eval case in `evals/`. The others are built only when a slice needs them.

### 7.4 Observability

Usage of AI per project and phase (tokens, time, number of human corrections) is recorded, so the metrics in `docs/plan.md` can be measured.

## 8. Status summary

| Phase | Status | What exists |
|---|---|---|
| P1 Requirements | 🟡 | Skill `pls-p1-requirements-analyst` v0.1 + eval case 001 |
| P2 Design | 🟡 | Skill `pls-p2-solution-designer` v0.1 + knowledge base `pls-kb-pleasanter` + eval case 001 |
| P3 Build | 🟡 | `pls unpack/pack` with logical references; canonicalise-via-dev step proven |
| P4 Verify | 🟡 | `pls lint` (6 rules), `pls coverage`, browser test runner (create / exec process / UI button / config checks) |
| P5 Release | 🟡 | `pls plan` (complete payload, rollback, classification), pre-apply drift re-check, business diff report |
| P6 Operate | 🟡 | `pls drift` against the last applied release; revert classification |

## 9. Next step

Slice #1 is done; gaps S1–S3 are closed in `pls` v0.2; the first skills are extracted. Next: run the eval cases with a fresh agent to validate the skills, then slice #2 on a real customer requirement using the skills for P1–P2.

## 10. Related decisions

ADR-0001 (scope in git), ADR-0002 (column slots), ADR-0003 (production deploy), ADR-0004 (data-impacting changes), ADR-0005 (secrets). Findings: `docs/review-findings.md`. Deferred work: `docs/tech-debt.md`.
