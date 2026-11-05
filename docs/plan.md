# ai-dlc-pleasanter roadmap

Principle: **validate the biggest assumption first, then build in thin vertical slices** (see review C2), not in horizontal layers.

The frame every step serves is `docs/architecture.md` (phases P1–P6, gates G1–G4). Work that does not map to a phase there is out of scope or goes to `patterns/`.

## Step 1 — Round-trip spike (1–2 weeks) — round 1 done

Question: does Pleasanter 1.5.x configuration survive export → re-import → identical to the original? Which parts must be done manually?

- Procedure: `spike/round-trip/README.md`
- Output: report based on `spike/round-trip/report-template.md` + a **Go / Change direction / No-go** decision
- Round 1 (2026-11-05): **conditional Go** — see `spike/round-trip/report-20261105.md`. Round 2 must cover the remaining 7 core components.

## Step 2 — Decide 5 ADRs (≈1 week)

| ADR | Topic | Depends on |
|---|---|---|
| 0001 | Scope of configuration managed in git | Spike results |
| 0002 | Column-slot ranges per ownership zone | 0001, agreement with customer (deferred: TD-01) |
| 0003 | Production deployment method | Customer IT (deferred: TD-02) |
| 0004 | Data-impacting changes & dedicated gate | 0001 |
| 0005 | Configuration storage & secrets policy | Runtime part accepted; storage part deferred (TD-03) |

## Step 3 — Vertical slice #1 through P1–P6 — DONE (2026-11-05, `docs/slices/slice-01-report.md`)

One small, real requirement, carried through **all six phases** at the minimum level, on a spike copy site:

| Phase | Minimum for slice #1 |
|---|---|
| P1 Requirements | 1–3 EARS requirements written by AI from a short request; human approves (G1) |
| P2 Design | AI maps them to columns/views/プロセス with ladder reasons; slot ledger entries; classification (G2) |
| P3 Build | `pls export` + `unpack`; AI edits `config/`; `pack`; deploy to dev |
| P4 Verify | Lint rules L-SEC-01, L-REF-01, L-SCR-01; 1 API test per requirement; coverage check (G3) |
| P5 Release | `pls drift` + `pls diff` + business-language report; deploy to a second copy site as "stg" (G4) |
| P6 Operate | Make one manual UI change on the "stg" copy; detect it as drift and resolve it |

Done when: the whole chain runs from a project-repo skeleton, each gate has a record, and gaps found are written back into `docs/architecture.md`.

Spike round 2 (remaining 7 core components) runs in parallel with P3 of the slice.

## Step 4 — Thicken each stage — items 1–4 done; proven in slice #2 (`docs/slices/slice-02-report.md`)

Priority after slice #1:

0. ✅ Close slice gaps S1–S3 in `pls` (v0.2: canon, drift vs last release, plan blocks on drift, mark-applied)
0. ✅ Extract skills `pls-p1-requirements-analyst` and `pls-p2-solution-designer` (+ knowledge base `pls-kb-pleasanter`, S7)
0. ✅ Run eval case 001 for both skills with a fresh agent; fix the skills until they pass (skills v0.2, `evals/results/*/2026-11-05.md`; found escaped defect: duplicate mail to [Manager] on escalation)
0. ⏸ Mail sink for notification tests (S5) — deferred: mail not needed at this stage (TD-10)

Then:

1. ✅ Drift check + column-slot conflict check before deploy (A2, D4 — mandatory) — `pls plan` refuses on drift (v0.2) and on slot findings (v0.3, L-SLOT-02, `pls slots`)
2. ✅ Deploy plan: dependency ordering, snapshot, configuration rollback (A3) — `pls release-plan` + runner `applyRelease` (v0.3); open: automatic smoke-then-restore, creating new sites
3. ✅ Data migration (A1) — ADR-0004 accepted after probes D12–D14; migration gate in `pls plan` / `release-plan`; runner `backupRecords` / `bulkUpsert`. Open: first real migration (volume, dry run on a data copy)
4. ✅ Permission matrix (C3) — site permissions in git, opt-in (ADR-0006, D15), drift + permission-impacting classification, L-PERM-01. Open: effective-access tests per role (TD-11)
5. First skills/agents, only for what the pilot needs — next: skills v0.3 from slice #2 findings (S2-1, S2-4)
6. Slice #2 ✅ (2026-11-05): multi-site release, migrations M1/M2, permissions + process ACL across environments; R-20261105-05 on stg

## Step 4b — Demo readiness ← NEXT (review: `docs/reviews/demo-readiness.md`)

**Goal:** another person clones the framework, creates a project from a natural-language spec and sets one connection config. The agent then carries the app through the lifecycle to **dev**, with a human approving at the gates. The run must use few tokens.

**Definition of done:** a **demo dry run** passes. The runner is someone who did not build the framework, working with Claude Code on a machine that can reach Pleasanter. They go from a clean clone to a **dev release** with round trip 0 and tests passing, using only:
- the repositories;
- `docs/setup.md`;
- the spec.

Measure tokens and wall time per phase, and record them in `demo/results/`.

### Work items (in order)

| # | Item | Deliverables | Acceptance |
|---|---|---|---|
| D1 ✅ | **Lifecycle runbook** — done 2026-11-05: `skills/pls-x-lifecycle` 0.1 + `templates/project/CLAUDE.md`; lifecycle case 001 pass (review R2-1, R2-2, R3-5) | `templates/project/CLAUDE.md`.<br>Skill `pls-x-lifecycle`: phase order P1→P6, gate stops (the agent stops and asks; it never approves), where gate decisions are written, the exact `pls` command per step, error handling (refused plan, failed apply → automatic restore), and token rules (read `pls` summaries, never whole payload, rollback or export files; no base64 when HTTP works). | A fresh agent given only the project and a spec reaches G1 and stops correctly. After "approve G1" it continues to G2, and so on. |
| D2 | **Skills P3–P5** (R2-1, R2-3, R2-5) | `pls-p3-config-builder`: design → `config/` edits using KB `schema.md`; canonical-form fold-back; lint/coverage loop.<br>`pls-p4-test-writer` + `references/test-spec.md`: the format of `ops`, `as_key`, `expectHttp`, `spec.vars`, `$var` and `list`; acceptance criteria → tests; role tests; G3 evidence template.<br>`pls-p5-release-manager`: `release-plan` → diff report (Japanese) → `apply` → `mark-applied` → smoke; templates for `diff-report.md`, `g3-verification.md`, `approvals.md`.<br>P6 as a runbook step: drift baseline after release. | Each skill has an eval case built from slice #3 (equipment) and graded by its rubric. No case answer may appear in a skill. |
| D3 | **Project scaffold** (R3-1, R3-2) | `pls init <dir> --framework <path>` (or `templates/project/` + copy script) creates:<br>• `CLAUDE.md`, `.gitignore`, `environments.json` with `dev`/`stg` placeholders (`parent_id`, empty `sites`, `principals` per role);<br>• `connections.example.json`, empty ledger and traceability, the `requirements/`, `design/`, `config/`, `tests/`, `releases/` and `ops/` folders;<br>• skills copied and `framework.lock` written.<br>Framework path read from `framework.lock` (or env `PLS_HOME`) instead of a fixed `../`. `pls skills check` compares the project copy with the lock. | Unit tests; `pls init` then `pls lint` passes on the empty project. |
| D4 | **Setup guide + demo package** (R1, R3-3, R3-4) | `docs/setup.md`:<br>• prerequisites (Python 3.10+, Claude Code on a machine that can reach Pleasanter, Pleasanter 1.5.x);<br>• one parent folder per environment;<br>• groups and users per role, API keys in environment variables;<br>• `connections.json`, `http-check`.<br>`demo/`: spec (equipment-loan request, Japanese), scenario script (what to say at each gate, expected stops, expected duration), the list of roles the spec needs, and a reset note (delete the demo folder in the UI). | A person follows `setup.md` to a green `http-check` without asking anyone. |
| D5 | **Real HTTP rehearsal** (R2-4) | Nam's terminal on dev, in a new demo folder: `init` → `bootstrap` → `release-plan` → `apply` → `test` (both roles) → `mark-applied`. Fix whatever breaks. | Recorded in `demo/results/`; apply and bootstrap proven over HTTP. |
| D6 | **Clean-up** (R3-6) | README status and layout updated.<br>Framework `CLAUDE.md` rules updated for `pls` (no spike-era paths).<br>`spike/`, `patterns/` and `evals/results/` moved under `archive/`, or clearly marked non-core.<br>`HANDOFF.md` reduced to current state + next step. | A newcomer reading README → setup → demo finds no stale statement. |
| D7 | **Demo dry run — fresh agent session** | Clean clone → setup → spec → P1…P6 on dev, with Nam answering the gates. Record tokens, time and human corrections per phase in `demo/results/`. | Pass; fixes folded back into D1–D6. |
| D8 | **Team acceptance run** | A team member runs the demo alone from `docs/setup.md` + `demo/`, then gives feedback (where they got stuck, what was unclear). | They reach the dev release without help → demo ready. |

### Decisions (Nam, 2026-11-05)

- **Demo target = dev only.** No stg in the demo.
  - P5 still runs, against dev, through the same release path: `release-plan` → diff report → G4 for that dev release → `apply` → `mark-applied` → tests. P6 = drift baseline on dev.
  - stg stays supported by the tools but is out of the demo.
  - `demo/` and `templates/project/` declare only `dev`: one parent folder on MADLAB dev.
- **Dry run (D7) = a fresh agent session** (Claude Code, local, network path to dev), started from a clean clone.
- **Final acceptance (D8) = a team member who did not build the framework.** They run the demo from `docs/setup.md` + `demo/`. The framework is built for the team, so this is the real definition of done.

### Deferred (not needed for the demo)

Migrations over HTTP, reviewer agents, CI, Playwright smoke, prod / customer-side deploy package (ADR-0003), mail (TD-10), P6 on permission drift.

## Step 5 — Real pilot & metrics (after the demo)

Metrics:
- Rate of AI changes correct on the first attempt
- Number of human corrections, and where
- Time from requirement to demo
- Drift incidents per month

## Decision log

| Date | Decision |
|---|---|
| 2026-11-04 | Split framework repo (`ai-dlc-pleasanter`) from customer project repos |
| 2026-11-04 | Constraints: on-prem, Pleasanter 1.5.x, customer may edit configuration |
| 2026-11-05 | Customer-facing questions (ADR-0002/0003/0005 storage) deferred as tech debt; use safest assumptions |
| 2026-11-05 | Spike runs on MADLAB internal dev (1.5.2) instead of localhost |
| 2026-11-05 | AI features call Claude via an internal gateway on Bedrock (IAM, no API keys); Terraform |
| 2026-11-05 | All repository documents are written in English |
| 2026-11-05 | AI gateway deployed to dev (ap-northeast-1) via Terraform in CloudShell as IAM user `namnh`; model `jp.anthropic.claude-haiku-5-5` (Japan-only inference profile) |
| 2026-11-05 | AI gateway parked as a reference pattern (`patterns/ai-gateway/`); not framework core |
| 2026-11-05 | `docs/architecture.md` v0.1 adopted as the frame: lifecycle P1–P6, gates G1–G4, invariants I1–I9 |
| 2026-11-05 | Slice #1 completed through P1–P6 on spike copies (escalation feature); architecture updated to v0.2 |
| 2026-11-05 | Skill/agent naming convention: `pls-<phase>-<role>` |
| 2026-11-05 | `pls` v0.2 (S1–S3 closed); skills v0.1: pls-kb-pleasanter, pls-p1-requirements-analyst, pls-p2-solution-designer |
| 2026-11-05 | Skills v0.2: slice answers removed from skills (eval leakage); eval case 001 passed for P1 and P2 with fresh agents |
| 2026-11-05 | AI gateway destroyed on AWS dev (`terraform destroy`, 13 resources) while parked; redeploy with `terraform apply` |
| 2026-11-05 | Mail deferred (TD-10): no mail sink, no mail tests, duplicate-mail defect left unfixed until mail is needed |
| 2026-11-05 | Slice 1.5: accepted stg drift 「緊急」 carried P6→P1→P5 with skills v0.2; R-20261105-02 record-only release; `pls` fix: last applied release ordered by instant (I9, regression test added) |
| 2026-11-05 | Step 4 items 1–4 done in `pls` v0.3: slot-collision check, multi-site release plan + automatic restore, migration gate (ADR-0004 accepted), site permissions in git (ADR-0006) |
| 2026-11-05 | Slice #2 (カテゴリ split, 経理 read, 合計対応時間) released to stg as R-20261105-05; B4 redesigned after T-015 (process access control, D20); test groups 372/373 kept until prod groups exist |
| 2026-11-05 | Stage = test/demo to shape architecture, design and process; customer questions, prod environment, real groups and mail deferred to the prod stage |
| 2026-11-05 | Feature work paused; demo readiness first (review `docs/reviews/demo-readiness.md`, plan Step 4b D1–D7) |
