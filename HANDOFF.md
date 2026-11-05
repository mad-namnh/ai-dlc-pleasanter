# Handoff — state as of 2026-11-05 (evening, after slice #2) JST

Read this first in a new session, then `CLAUDE.md` and `docs/architecture.md`.

## What this is

AI-DLC framework for Pleasanter projects (MADLAB). The goal is that AI assists the whole lifecycle with human gates G1–G4:

P1 requirements → P2 design → P3 build → P4 verify → P5 release → P6 operate

Owner: Nam. Discussion is in Vietnamese; **everything in the repos is English** (Pleasanter end-user messages stay Japanese).

## Repositories (on Nam's machine, `C:\Workspace\MADLAB\01. Project\`)

| Repo | Role |
|---|---|
| `ai-dlc-pleasanter` | Framework: architecture v0.2, ADRs, `tools/pls` v0.3, `skills/` (KB 0.5), `evals/`, `patterns/ai-gateway` (parked) |
| `pls-demo-inquiry` | First project repository: slices #1, 1.5 and #2. All of them are merged to `main`; no other branches. |

`_to_delete/` folders are leftovers (the agent shell cannot delete files); safe to delete.

## Status

- **Slice #2 done (2026-11-05)** — `docs/slices/slice-02-report.md`.
  - Scope: customer mail → REQ-007…015 → DES-003, in three parts:
    - カテゴリ split, with migration M1;
    - 経理 read-only access, with permissions in git;
    - 合計対応時間, with a Summary and migration M2.
  - Released to stg as **R-20261105-05**:
    - 2 sites, applied in dependency order, with automatic restore on failure;
    - round trip 0 differences;
    - smoke tests T-009, T-010 and T-016 pass.
  - One design loop: T-015 showed that a read-only user still sees process buttons. That led to KB D19 being corrected, D20 being added, B4 being redesigned with process access control, and G2 being approved again.
- `pls` v0.3:
  - Commands: unpack, pack, canon, lint, diff, drift, classify, coverage, slots, plan, release-plan, mark-applied.
  - Permissions and process ACLs (`Groups`/`Users`/`Depts`) are mapped per environment through `${principal:x}` (ADR-0006, D20).
  - Migration gate per ADR-0004.
  - Runner: `applyRelease`, `rollbackRelease`, `backupRecords`, `bulkUpsert`, and `runTests` (create on another site, `$var` references).
  - Tests: python 24/24, node 6/6.
- KB `pls-kb-pleasanter` 0.5: behaviours D12–D20 come from probes on dev.
- Skills v0.2 (P1, P2) passed eval case 001. They were used for slice #2.
- Slice #1 and slice 1.5 are done (see the reports and the decision log in `docs/plan.md`).

## Next steps (in order)

1. ✅ Skills 0.3 / KB 0.6 from the slice #2 findings (commit c02bd12), and the project pin was upgraded. **Next:** run eval case 002 (P1, P2) with fresh agents, 3 runs each.
2. **Customer round:** send Q8–Q24 and O7 (M2 changes 更新日時 and 更新者). Get the real groups for prod (O3), then add `prod` to `environments.json`.
3. **First real migration volume** (plan Step 4 item 3): M1 and M2 touched 0 records on stg, so rehearse on a copy of real data.
4. **Evals:** automate grading; run case 001 again on 0.3 to check for regressions.
5. Step 5 (real pilot and metrics) — choose the pilot project.

Mail stays deferred (TD-10). The escaped defect below waits for it.

## Escaped defect found by the eval (I9)

In R-20261105-01, view 未完了 (Id 2) now includes status 150. Notification #1 sends to [Manager], watches Status/ClassE, uses view 2 as its condition and has the subject 「優先度「高」の問い合わせが未対応です」. So it also fires on every escalation, and the manager gets a second, misleading mail. It also does not filter on 優先度 at all. **Deferred with all mail work (TD-10).**

## Environments

| Item | Value |
|---|---|
| Pleasanter dev (1.5.2) | `https://pleasanter-dev.mad-lab.jp/` — reachable **only from the built-in browser** of the Claude desktop app. Log in manually; the API works with the session (no API key). |
| Spike folder | site 44562 `zz_spike_roundtrip` — all writes stay inside it |
| Project dev | 問い合わせ 44565, 対応履歴 44566 (last: R-20261105-04-dev) |
| Project stg | 問い合わせ 44573, 対応履歴 44574 (last: **R-20261105-05**) |
| Test principals (dev/stg) | user `zz_test_keiri` (10061), groups `zz_test_経理` (372) and `zz_test_サポート` (373). **In use:** stg/dev permissions and the `escalate` process ACL point to 372/373, so keep them until prod groups replace them (O3). Credentials are in `pls-demo-inquiry/tests/seed/` (gitignored). |
| Probe sites | 44588 `zz_probe_data_20261105`, 44592 `zz_probe_child_20261105` — dummy data only; delete in the UI (TD-08) |
| Original demo sites | 42410 / 42411 — **never written to** by the framework |
| AWS dev | AI gateway destroyed 2026-11-05 (`terraform destroy`); the AI feature on 44565/44573 fails when ticked; normal saves are unaffected. |

## How transport works today (S4)

Exports and payloads move between the browser and the repo as gzip + base64. Large ones are split into halves, and each half is verified with SHA-256 on both sides before use. Deploys run only with complete payloads, after a preflight check that the target has not changed since the plan.

## Open items elsewhere

- `docs/tech-debt.md` TD-01…TD-11.
- Demo site 42410 still has the D7 bug (shared script `const`) and the old API-key script; fixing it is the owner's call.
- Revoke the Anthropic API keys once nothing uses them.
