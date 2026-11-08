# Handoff — state as of 2026-11-08 (branch `brownfield-adr`; sections below 'Current state' describe 2026-11-05)

> Next session may run on another Claude account: everything needed is in the two repositories; nothing lives only in the chat.

Read this first in a new session, then `CLAUDE.md` and `docs/architecture.md`.

## Current state — 2026-11-08 (read first)

- `main` (= GitHub) is the **demo baseline**; do not commit there unless Nam asks.
- All brownfield work is on the **local branch `brownfield-adr`** (not pushed): ADR-0009…0012, plan Step 4c BR1–BR9 built and run on MADLAB dev (kb-verify 7/7 on 1.5.2, sandbox trial, adopt of site 797 read-only), skills onboarding / spec-recovery / script-engineer / maintenance-triage, lifecycle routes by profile **Origin** (`new` / `existing`).
- Tests: 145 Python + 6 node, plus a write-path inventory test (`tools/pls/tests/test_write_guards.py`).
- Architecture audit after BR9: ready with conditions; fixes on the branch: template `.gitattributes`, docs refreshed, `pls gate` (I4), test/skill clarifications.
- Next: onboarding of the first real project on dev with `pls init <name> --origin existing --stage project --target stg`; Nam accepts ADR-0009/0010/0011 after that run.

## What this is

AI-DLC framework for Pleasanter projects (MADLAB). The goal is that AI assists the whole lifecycle with human gates G1–G4:

P1 requirements → P2 design → P3 build → P4 verify → P5 release → P6 operate

Owner: Nam. Discussion is in Vietnamese; **everything in the repos is English** (Pleasanter end-user messages stay Japanese).

## Repositories (on Nam's machine, `C:\Workspace\MADLAB\01. Project\`)

| Repo | Role |
|---|---|
| `ai-dlc-pleasanter` | Framework: architecture **v0.3**, ADRs 0001–0008, `tools/pls` 0.7, `skills/` (KB 0.9, P1 0.3, P2 0.5, P3 0.1, P4 0.2, P5 0.1, lifecycle 0.1), `evals/` (cases 001–002), `patterns/ai-gateway` (parked). Remote: `https://github.com/mad-namnh/ai-dlc-pleasanter` (`main`) |
| `pls-demo-inquiry` | First project repository: slices #1, 1.5 and #2. All of them are merged to `main`; no other branches. |
| `pls-demo-equipment` | Second project repository: slice #3, a new app (equipment loans) created by the framework (dev 44628/44629, stg 44671/44672) |
| `demo-equipment` | D5 demo run (2026-11-05), created by `pls init`: equipment loans from `demo/spec.md`, dev 44709/44710 under AI-DLC-DEMO (44708), release `R-20261105-01-dev`, G1–G4 approved by Nam. **Local only, never pushed** (demo project) |

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

## Stage (decided by Nam, 2026-11-05)

**Test / demo stage.** The goal now is to shape the architecture, design and process. It is not to deliver to a customer. Therefore:
- Customer questions (Q1–Q24, O7), the prod environment and the real groups (O3) are **prod-stage items**. They are deferred and do not block anything. Keep using the `[assumed]` defaults.
- The test principals (10061, 372, 373) stay as they are.
- Mail stays deferred (TD-10).

## Start of the next session

1. ✅ (2026-11-05) All three repos were checked and committed. The session must have `pls-demo-equipment` connected as a folder as well.
2. Optional: Nam re-runs `pls test tests/api/equipment.json --env dev --site loans` from `pls-demo-equipment` (HTTP transport) — expected all pass / pass-api-only.
3. Then continue with step 4 below (architecture gaps) or step 5 (architecture.md v0.3). Multi-user HTTP role tests are deferred (demo stage).

Tools: `pls` 0.7 (HTTP transport + browser runner fallback; `setup`, `init`, `principals`, `skills`), 54 python tests + 6 node tests. The agent sandbox cannot reach Pleasanter over HTTP (proxy 403); agents use the built-in browser runner, people use `pls` over HTTP.

## Current focus (2026-11-05, Nam)

**Feature work is paused. Demo readiness comes first.** Review: `docs/reviews/demo-readiness.md` (verdict: not ready). Plan: `docs/plan.md` Step 4b, items D1–D7, D1 is done (lifecycle skill + project CLAUDE.md template). D2 is done: skills P3, P4 and P5 0.1. Tool gaps are in TD-14 ((b)–(d) are needed before D7). D3 is done: `pls init`, launcher, `skills check|sync`, and TD-14 (a)–(d) fixed (pls 0.6). An independent architecture review after D3 gave GO with conditions (`docs/reviews/architect-review-d3.md`). D3b is done: B1–B3 are in the skills and KB; S1–S5 and S7 are fixed in `pls` 0.7 (53 + 6 tests). D4 is done and simplified: `pls setup` (once: URL, folder link, hidden key, login; groups found by name; profile in `~/.pls/profiles/`) + `pls init <name>` (ready project + first commit). Nam created folder AI-DLC-DEMO (44708) and groups zz_demo_総務 (374) / zz_demo_社員 (375). Permissions are a design step (P2 1b → `design/roles.json`; after G2 the groups are created and `pls principals` binds them). **D5 is done (2026-11-05)**: `pls init demo-equipment` + the demo script ran end to end on dev (P1→G4, 10/10 API tests, round trip and drift 0). Findings: (1) G2 groups must be created with exactly the names in `design/roles.json` — in the run the existing `zz_demo_*` groups were used instead; (2) KB 0.9 D28 `[[Users*]]`; (3) `siteConfig` does not substitute `$vars` (TD-14h, test-spec 0.2); (4) REQ-008 (permission only) has no API test while role tests are deferred — accepted at G3 on config + manual screen check; (5) `pls` tests read files without `encoding` and failed on a cp932 console — fixed. Test records deleted from dev. Presenter guide: `demo/lifecycle-and-demo-guide.html`. S6 and S8–S10 come in D6, before D7. Decided: the demo stops at **dev** (no stg); D7 is a fresh agent session; D8, a team member running it alone, is the real acceptance.

## Next steps (in order) — before the pause

1. ✅ Skills 0.3 / KB 0.6 from the slice #2 findings (commit c02bd12); project pin upgraded.
2. **Eval case 002** (P1, P2) with fresh agents — run 1 done (2026-11-05, `evals/results/*/2026-11-05-case002.md`):
   - P1 0.3: **PASS** (the input leaked the slice #2 REQ count through the source file header; `input.md` fixed).
   - P2 0.3: **FAIL** on one item: the probe for process buttons of a read-only role was composed correctly but scheduled after G2, and the design kept the expected (wrong) branch. Fixed in **P2 0.4** (design-changing probes are G2 prerequisites, otherwise take the safe branch).
   - Run 2 with 0.4: **PASS** (`evals/results/pls-p2-solution-designer/2026-11-05-case002.md`). `pls-demo-inquiry` pinned to P2 0.4.
   - Follow-ups: `pls classify` classifies process access control (`Processes[].Groups/Users/Depts`) as config-only — should be permission-impacting (tool gap); watch whether design-changing probes on verified behaviour (PRB-3 type) are treated as G2 prerequisites in the next case.
3. ✅ **Slice #3 — new app end to end (2026-11-05)**: equipment loans in `pls-demo-equipment`, P1→P6, G1–G4 approved, stg R-20261105-E03 applied (0-difference round trip, smoke pass, drift baseline 0). ADR-0007 (new sites), pls 0.4, KB 0.7 (D21–D27), skill P2 0.5. Report: `docs/slices/slice-03-report.md`.
3b. **HTTP transport (ADR-0008, pls 0.5)** — `pls http-check / export / bootstrap / apply / test / backup` with operator-local `.pls/connections.json` and keys in environment variables; role tests pick the key per spec (`as_key`). 37 unit tests (fake Pleasanter server). First real run on dev by Nam (2026-11-05): 総務 suite OK after 2 tool fixes (BOM, 1.0 vs 1); re-run of `equipment.json` after the fix pending. Multi-user (社員 key) run **deferred by Nam** — demo stage. API key pasted in chat during the run → Nam to revoke and recreate. The agent sandbox still has no network path, so agents keep the browser runner as fallback.
4. **Architecture / process gaps worth a demo slice:**
   - P6 operate on slice #2: a drift on permissions, and on the process ACL.
   - Transport ADR-0003: the manual base64 transfer is the most token-heavy step. Decide whether to automate it.
   - A migration on a larger data copy (plan Step 4 item 3).
   - Line-level script diff (S6).
5. ✅ `docs/architecture.md` v0.3: slices #1–#3, the transport, phase statuses and next steps (§9). Step 4 = architecture §9 items 1–5.
6. Prod-stage items (customer round, prod environment, real groups, mail) — later.

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
