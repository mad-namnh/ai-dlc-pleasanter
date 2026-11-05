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

## Step 4 — Thicken each stage ← NEXT

Priority after slice #1:

0. ✅ Close slice gaps S1–S3 in `pls` (v0.2: canon, drift vs last release, plan blocks on drift, mark-applied)
0. ✅ Extract skills `pls-p1-requirements-analyst` and `pls-p2-solution-designer` (+ knowledge base `pls-kb-pleasanter`, S7)
0. ✅ Run eval case 001 for both skills with a fresh agent; fix the skills until they pass (skills v0.2, `evals/results/*/2026-11-05.md`; found escaped defect: duplicate mail to [Manager] on escalation)
0. ⏸ Mail sink for notification tests (S5) — deferred: mail not needed at this stage (TD-10)

Then:

1. ✅ Drift check + column-slot conflict check before deploy (A2, D4 — mandatory) — `pls plan` refuses on drift (v0.2) and on slot findings (v0.3, L-SLOT-02, `pls slots`)
2. Deploy plan: dependency ordering, snapshot, configuration rollback (A3)
3. Data migration (A1)
4. Permission matrix (C3)
5. First skills/agents, only for what the pilot needs

## Step 5 — Real pilot & metrics

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
