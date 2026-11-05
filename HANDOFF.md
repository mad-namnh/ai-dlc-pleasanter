# Handoff — state as of 2026-11-05 (afternoon, after eval run) JST

Read this first in a new session, then `CLAUDE.md` and `docs/architecture.md`.

## What this is

AI-DLC framework for Pleasanter projects (MADLAB). Goal: AI assists the whole lifecycle P1 requirements → P2 design → P3 build → P4 verify → P5 release → P6 operate, with human gates G1–G4. Owner: Nam. Discussion in Vietnamese; **everything in the repos is English** (Pleasanter end-user messages stay Japanese).

## Repositories (on Nam's machine, `C:\Workspace\MADLAB\01. Project\`)

| Repo | Role |
|---|---|
| `ai-dlc-pleasanter` | Framework: architecture v0.2, ADRs, `tools/pls` v0.2, `skills/` v0.1, `evals/`, `patterns/ai-gateway` (parked) |
| `pls-demo-inquiry` | First project repository (slice #1): requirements, design, config, tests, releases, ops |

`_to_delete/` folders are leftovers (the agent shell cannot delete files); safe to delete.

## Status

- Architecture v0.2 — `docs/architecture.md`; slice #1 report — `docs/slices/slice-01-report.md`
- `pls` v0.3 — unpack, pack, canon, lint, diff, drift (vs last applied release), classify, coverage, **slots** (pre-deploy slot-collision check, A2), plan (refuses on drift and on slot findings), **release-plan** (multi-site, dependency order, reverse-order rollback), mark-applied. Runner `applyRelease` (preflight, ordered apply, automatic restore). Tests: `python -m unittest discover -s tools/pls/tests` 18/18, `node --test tools/pls/tests/test_runner.mjs` 4/4 (fix 2026-11-05: last applied release chosen by instant, not by `applied_at` string — mixed UTC offsets made drift use an older baseline).
- **Slice 1.5 done (2026-11-05)** — `pls-demo-inquiry` branch `slice-1.5-urgent`: stg drift 「緊急」 accepted and carried P6 → P1 → P5 with skills v0.2. REQ-005 released as **R-20261105-02** (record-only: stg already matched git, no write to stg). REQ-006 (escalate 緊急) withdrawn at G1. Dev deploy + 8/8 API tests; stg drift now clean → **stg releases unblocked**.
- Skills v0.2 — `pls-kb-pleasanter`, `pls-p1-requirements-analyst`, `pls-p2-solution-designer`. Eval case 001 **passed** for P1 and P2 with fresh agents on a pre-slice scratch project (`evals/results/*/2026-11-05.md`). v0.1 leaked the slice #1 answer (examples + pointer to the rubric) — removed. P1 failed run 1 (two `shall`s, scope creep) → skill fixed → run 2 passed. `pls-demo-inquiry/.claude/skills` still pins v0.1.

## Next steps (in order)

1. Merge branches into `main` (framework `framework-v0.2`; project `slice-01` + `slice-1.5-urgent`). Mail stays deferred (TD-10).
2. Record KB entries from evidence: process data change fills an `EditorReadOnly` column (slice #1 T-001); probe `Reminders[].Condition` and placeholders in process-notification `Subject` on dev.
3. Slice #2 on a real customer requirement, using the skills for P1–P2 (upgrade the project pin to v0.2).
4. Evals: run each case ≥ 3 times (two P1 runs made opposite status assumptions); automate grading (tech debt).

## Escaped defect found by the eval (I9)

In R-20261105-01, view 未完了 (Id 2) now includes status 150, and notification #1 (to [Manager], watches Status/ClassE, condition = view 2, subject 「優先度「高」の問い合わせが未対応です」) therefore also fires on every escalation → the manager gets a second, misleading mail. Notification #1 also does not filter on 優先度 at all. Both independent P1 runs and the P2 run found it; slice #1 did not. Needs a requirement (P1/G1) and a fix; rubrics updated. **Deferred with all mail work (TD-10).**

## Resolved: drift on stg (was blocking releases)

`pls-demo-inquiry/ops/drift/stg-20261105.md`: 優先度 「緊急」 added on stg → **accepted** (Nam), REQ-005 released in R-20261105-02; 緊急 is not escalatable (Q5 = no). Customer confirmation of Q-adopt/Q6/Q7 still open.

## Environments

| Item | Value |
|---|---|
| Pleasanter dev (1.5.2) | `https://pleasanter-dev.mad-lab.jp/` — reachable **only from the built-in browser** of the Claude desktop app (the agent shell and cloud workspace are blocked by proxy). Log in manually; the API works with the session (no API key). |
| Spike folder | site 44562 `zz_spike_roundtrip` — all writes stay inside it |
| Slice #1 dev | 問い合わせ 44565, 対応履歴 44566 |
| Slice #1 stg | 問い合わせ 44573, 対応履歴 44574 (release R-20261105-01 applied) |
| Original demo sites | 42410 / 42411 — **never written to** by the framework |
| AWS dev (ap-northeast-1) | AI gateway **destroyed 2026-11-05** (`terraform destroy`, 13 resources) — nothing billable left from the pattern. Terraform files + empty state + pre-destroy backup remain in CloudShell home of `namnh`. The AI feature (「AIで一次対応する」) on dev 44565 / stg 44573 now fails when ticked; normal saves are unaffected. |

## How transport works today (see `docs/slices/slice-01-report.md` S4)

Exports and payloads move between the browser and the repo as gzip + base64, always verified with SHA-256 on both sides before use. Deploys only with complete payloads, after re-checking that the target did not change since the plan.

## Open items elsewhere

- `docs/tech-debt.md` TD-01…TD-09 (customer questions deferred; gateway HTTPS/cost alarm; Terraform state; spike folder cleanup; MFA for `namnh`).
- Demo site 42410 still has the D7 bug (shared script `const`) and the old API-key script; fixing it is the owner's call.
- Revoke the Anthropic API keys once nothing uses them.
