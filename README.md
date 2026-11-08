# ai-dlc-pleasanter

MADLAB's AI-DLC (AI-Driven Development Lifecycle) framework for **Pleasanter (プリザンター)** projects.

**To run it:** [`docs/setup.md`](docs/setup.md) (prepare Pleasanter, `pls init`, connect), then the demo in [`demo/README.md`](demo/README.md).

**Visual guide:** [`demo/lifecycle-and-demo-guide.html`](demo/lifecycle-and-demo-guide.html) — lifecycle diagram, phases, gates and the demo script on one page (open it in a browser).

**To understand it:** [`docs/architecture.md`](docs/architecture.md) — the lifecycle frame (P1 requirements → P6 operate, gates G1–G4, invariants, components).

Goal: bring the model "source of truth in git → AI works through hooks → verification & human approval (G1–G4) → failures fed back as rules" into a low-code environment, where the **source of truth is configuration** (SiteSettings, scripts, permissions, …) rather than source code.

## Status

State of branch `brownfield-adr` (2026-11-08). `main` is the demo baseline.

| Item | Status |
|---|---|
| Architecture (lifecycle P1–P6, gates G1–G4, invariants I1–I9) | ✅ v0.3 — `docs/architecture.md` |
| ADRs | 0001–0012: 0004, 0006, 0012 accepted; 0005 partly; 0001–0003, 0007–0011 proposed (`docs/adr/README.md`) |
| Vertical slices | ✅ #1–#3 (`docs/slices/`), demo run D5 (`demo-equipment`, released on dev) |
| `pls` toolchain | ✅ stdlib Python, HTTP transport — unpack/pack/canon/lint/diff/drift/classify/coverage, release-plan/apply/mark-applied, bootstrap, test, init/setup/skills; brownfield: version, adopt, env-compare, refs, xref, sandbox, harvest, merge-site, kb-verify. 180 Python + 6 node tests, write-path inventory test, gate records (`pls gate`) |
| Skills | ✅ 12 — KB, P1–P5, lifecycle (routes new / existing apps), onboarding, spec-recovery, script-engineer, maintenance-triage; evals in `evals/` |
| Brownfield readiness (plan Step 4c) | 🟡 BR1–BR9 built and run on MADLAB dev; waiting for the first real project (onboarding) |
| AI gateway (Bedrock) | ⏸ Parked reference pattern (`patterns/ai-gateway/`), not framework core |

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

Projects are created with `pls init` (new app, or `--origin existing` to take over an app that already runs); the visual guide is `demo/lifecycle-and-demo-guide.html`.

## Getting started

1. Read `docs/architecture.md`.
2. Read `docs/plan.md` for what is next.

## Documentation language

All `*.md` files in this repository are written in **English** (see `CLAUDE.md`).
