# ai-dlc-pleasanter

MADLAB's AI-DLC (AI-Driven Development Lifecycle) framework for **Pleasanter (プリザンター)** projects.

**Start here: [`docs/architecture.md`](docs/architecture.md)** — the lifecycle frame (P1 requirements → P6 operate, gates G1–G4, invariants, components).

Goal: bring the model "source of truth in git → AI works through hooks → verification & human approval (G1–G4) → failures fed back as rules" into a low-code environment, where the **source of truth is configuration** (SiteSettings, scripts, permissions, …) rather than source code.

## Status

| Item | Status |
|---|---|
| Repository skeleton | ✅ Done |
| Architecture (lifecycle frame) | ✅ v0.1 — `docs/architecture.md` |
| Architecture review (A1–C5, D1–D7) | ✅ Recorded in `docs/review-findings.md` |
| ADR 0001–0005 | 🟡 Proposed with open questions; ADR-0005 partially accepted (runtime secrets) |
| Round-trip spike (B4) | 🟡 Round 1 done on internal dev (1.5.2) — **conditional Go**; round 2 pending (`spike/round-trip/report-20261105.md`) |
| AI gateway (Bedrock) | ⏸ Parked reference pattern for customer apps — deployed on dev, not framework core (`patterns/ai-gateway/`) |
| First vertical slice (P1→P6) | ✅ Done — `docs/slices/slice-01-report.md`; project repo `pls-demo-inquiry` |
| `pls` toolchain | 🟡 v0.2 — `tools/pls/` (unpack, pack, canon, lint, diff, drift, classify, coverage, plan, mark-applied) + browser runner |
| Skills | 🟡 v0.1 — `pls-kb-pleasanter`, `pls-p1-requirements-analyst`, `pls-p2-solution-designer` (`skills/`, evals in `evals/`) |

## Environment constraints (agreed)

- Customer runs Pleasanter **on-prem**
- Pleasanter **1.5.x** — internal dev is **1.5.2**; record the exact patch of both dev and customer in spike reports (they must match)
- The customer **can edit configuration** in the UI → two-way sync; drift handling is mandatory

## Repository split

- **This repository (framework)**: tools, rules, ADRs, spikes run on synthetic data. **Never** contains customer configuration or data.
- **Project repositories (one per customer)**: unpacked configuration, ledgers, EARS requirements. Hosted wherever the customer allows.

## Layout

```
ai-dlc-pleasanter/
├─ README.md
├─ CLAUDE.md               # rules for agents working in this repo
├─ tools/pls/              # deterministic toolchain (stdlib Python) + browser runner
├─ skills/                 # AI skills, named pls-<phase>-<role>, installed into project repos
├─ evals/                  # eval cases (input + rubric) per skill
├─ patterns/               # reusable solutions for customer apps (NOT framework core), e.g. ai-gateway
├─ docs/
│  ├─ architecture.md      # THE frame: lifecycle phases, gates, invariants, components
│  ├─ plan.md              # roadmap
│  ├─ review-findings.md   # architecture review results → backlog
│  ├─ tech-debt.md         # deliberately deferred work, with deadlines
│  ├─ slices/              # vertical slice reports
│  └─ adr/                 # architecture decision records
└─ spike/round-trip/       # spike B4: does configuration survive export → import unchanged?
   ├─ README.md            # procedure and go/no-go criteria
   ├─ browser/             # runner executed in a logged-in browser session
   ├─ env/                 # (optional) local Docker Pleasanter 1.5.x
   ├─ scripts/             # export / normalize / roundtrip / scan_secrets
   ├─ inventory-checklist.md
   ├─ report-template.md
   ├─ report-YYYYMMDD.md   # sanitized spike reports
   └─ data/                # (gitignored) exported data — NEVER commit
```

The `cli/`, `skills/`, `agents/`, `hooks/` and `test-harness/` directories are **intentionally not created yet**; they depend on the spike results and ADRs.

## Getting started

1. Read `docs/architecture.md`.
2. Read `docs/plan.md` for what is next.

## Documentation language

All `*.md` files in this repository are written in **English** (see `CLAUDE.md`).
