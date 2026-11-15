# Plan — scalar keys verified by kb-verify (settings coverage WS3a steps 4–5)

- **Date / branch / parent commit:** 2026-11-16 / `brownfield-adr` / `2dca8a3`
- **Objective:** record Nam's kb-verify run of probes D43–D47 in the KB and add the keys stored as sent to `VERIFIED_KEYS`.
- **Tier:** Critical (`VERIFIED_KEYS` decides what `release-plan` deploys without `--accept-unverified`).
- **Evidence:** `pls-trial-store-promo/ops/kb-verify/2026-11-16-dev.{md,json}` (run by Nam, MADLAB dev 1.5.2.0 build 201520): D43 20/20, D44 27/27, D45 14/14, D47 15/15 keys stored as sent; D46 9/10 — `DashboardPartsAsynchronousLoading` not stored (source: recorded only when it differs from `Parameters.Dashboard.AsynchronousLoadingDefault`, SiteSettings.cs l.1254).
- **Scope:** KB rows and index (curator); `tools/pls/pls_scope.py` VERIFIED_KEYS + docstring; `skills/README.md` KB 0.29; test.
- **Out of scope:** the screen effect of the switches (not probed); D46 split / re-probe with `false`; D40 / D41a (unchanged results); D42 screen observation (separate evidence, `plans/2026-11-16-d42-screen-check/`).
- **Stop points expected:** none (evidence from a person's run; no ADR Decision change).
- **Acceptance criteria:**
  1. Every key the D43–D47 probes expect stored is in `VERIFIED_KEYS` except `DashboardPartsAsynchronousLoading` (85 keys); that key stays a scope finding.
  2. KB rows D43–D47 and index.json match the run; nothing beyond the evidence is claimed.
  3. New test fails on the parent; suites green (3.12, 3.10, node).
  4. Review: no open Critical / High.
- **Subagents:** `pls-kb-curator` (opus, high), `pls-x-reviewer` (opus, high).
- **Documents:** `skills/README.md` (KB version), `HANDOFF.md` line at commit.
