# Vertical slice #1 — report (2026-11-05)

One small requirement carried through **all six phases** on spike copy sites, to validate `docs/architecture.md` v0.1.

- **Requirement:** escalation button for 問い合わせ (inquiries) — priority 高 inquiries can be escalated to the support manager, with timestamp and mail.
- **Project repository:** `pls-demo-inquiry` (separate from this framework repository, as designed)
- **Environments:** dev = sites 44565/44566, stg = sites 44573/44574 (copies inside the spike folder 44562 on MADLAB dev, Pleasanter 1.5.2)
- **Gates:** G1–G4 approved by the project owner (who acted as both MADLAB tech lead and customer owner for this slice)

## Result per phase

| Phase | What happened | Artifacts (project repo) | Verdict |
|---|---|---|---|
| P1 Requirements | AI wrote 4 EARS requirements from a 2-sentence request, incl. one **derived** from impact analysis (REQ-004) and 4 open questions for the customer | `requirements/` | ✅ G1 |
| P2 Design | Standard プロセス only (no code). Original idea (checkbox flag) **rejected** after checking Pleasanter's real UI: checkbox filters are 2-state. Status-based design + impact analysis on views, notifications, AI script | `design/decisions/DES-001`, `design/slot-ledger.json`, `traceability.json` | ✅ G2 |
| P3 Build | AI edited the unpacked config in git; `pls pack` → deploy to dev. Pleasanter **canonicalised** the saved config (added 11 defaults, dropped 1) → folded back into git → git ≡ dev (canonical SHA-256 match) | `config/inquiries/` | ✅ |
| P4 Verify | `pls lint` 0 issues; 6/6 API tests (incl. UI button presence); coverage 4/4; probe: API enforces the process display condition | `tests/api/`, `tests/results/`, `g3-verification.md` | ✅ G3 |
| P5 Release | Drift re-checked immediately before apply; complete payload; rollback saved; stg ≡ git after release; 6/6 smoke on stg. The release also fixed a **real D3 defect on stg** (its AI script was reading dev's data) | `releases/R-20261105-01/` (plan, payload, rollback, diff report in Japanese, approvals) | ✅ G4 |
| P6 Operate | Simulated customer UI edit (priority 「緊急」) detected by `pls drift`; ops report found that escalation does not cover 緊急 and that **reverting would be data-impacting**; decision left to a human | `ops/drift/stg-20261105.md` | ✅ (decision pending) |

## Gaps found → framework backlog

| # | Gap | Severity | Change to the framework |
|---|---|---|---|
| S1 | Pleasanter **canonicalises configuration on save** (adds default fields, drops default-valued fields). Without folding back, every drift check reports false positives | High | ✅ `pls canon` + `canonical-defaults.json` + L-CAN-01 (v0.2). P3 step "canonicalise via dev" (deploy → export → unpack) or a defaults table in `pls`; finding D8 |
| S2 | `pls drift` compares live with **git HEAD**, which already contains unreleased changes. Drift must be computed against the **last released payload** | High | ✅ `pls drift` uses the last applied release; `pls plan` refuses on drift; `pls mark-applied` (v0.2) |
| S3 | Reverting drift can itself be **data-impacting** (removing a choice that records use) | High | ✅ drift report states whether reverting is data-impacting (v0.2) |
| S4 | No network path from tooling to Pleasanter in this setup. The browser runner + gzip/SHA-256 transfer worked and was safe, but is manual | Medium | Decide the transport in ADR-0003 (customer-side runner; built-in MCP D1 as candidate) |
| S5 | Mail delivery (REQ-003) cannot be tested | Medium | Mail sink (e.g. smtp4dev/MailHog) in dev/stg; test op `mailbox` |
| S6 | Script changes appear as one opaque "Body changed" row in diffs | Low | Line-level diff for scripts in `pls diff` / reports |
| S7 | Pleasanter behaviour knowledge (2-state checkbox filters, API enforces process display conditions, defaults) was discovered by probing | Medium | ✅ `pls-kb-pleasanter` v0.1. Seed a **Pleasanter knowledge base** (`pls-kb-pleasanter`) used by the `pls-p2-solution-designer` skill; findings D9, D10 |
| S8 | All AI roles were played by one general agent | — | ✅ v0.1 in `skills/` with eval cases. Extract the first skills from this slice: `pls-p1-requirements-analyst` (EARS + derived requirements + open questions), `pls-p2-solution-designer` (ladder + impact analysis), backed by `pls-kb-pleasanter` |

## What the architecture got right

- The six phases and four gates were sufficient; no phase was missing or redundant.
- I2 (complete payload + pre-deploy drift check) prevented nothing bad this time, but S2/S3 show it is essential.
- I6 (deterministic diff, AI explains) produced a customer-ready Japanese report from a 6-row raw diff.
- Logical references (`${site:…}`, `${env:…}`) fixed a real cross-environment defect (D3) by construction.

## Test data left behind

dev records 44575–44579, stg records 44580–44581 (spike folder; cleaned with TD-08).
