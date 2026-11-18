# Plan — D40/D41a: screen checks on the deployed app site; release needs a screen re-save

- **Tier:** Critical (KB claims used by designs and by the release procedure).
- **Evidence:** `evidence-screen-checks-deployed-site.md` (Nam, 2026-11-15).
- **Work:** curator: D40 (deployed by `updatesite`: JSON-link drop-down empty until the site is saved on the screen; then lookup and stored value right — account not stated), D41a (formula over the looked-up value shown on the screen only with 自動ポストバック on the other operand; stored right after save). Orchestrator: review-findings, tech-debt (release step: re-save on the screen after an `updatesite` deploy of a JSON link — no API way known), README KB version, HANDOFF.
- **Out of scope:** `pls` code; trial repository (message to Nam).
- **Acceptance:** KB says only what was reported or read; suites green; review no Critical/High.
