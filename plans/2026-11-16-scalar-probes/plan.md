# Plan — scalar round-trip probes D43–D47 (settings coverage WS3a)

- **Tier:** Standard (KB probe definitions and unverified KB rows; no claim, no code).
- **Change:** five kb-verify probes (stored shape of 86 scalar SiteSettings keys, values non-default against Pleasanter_1.5.2.0 RecordingData and the shipped Parameters; D47 includes the four mail address keys with example.invalid addresses, the round-trip evidence ADR-0001 needs for them); index entries with verified_on []; behaviours.md rows 'not verified — no run yet'. Written by pls-kb-curator from the Orchestrator's generated files (validated with check_probe).
- **Next (Nam):** run `pls kb-verify --env dev`; then the curator records results and the Orchestrator adds the stored keys to VERIFIED_KEYS.
- **Acceptance:** (1) probes load and match the index; (2) KB rows say not verified, probe contained, not covered; (3) suite green on HEAD plus these files only; (4) review no open Critical/High.
