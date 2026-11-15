# Plan — D40: link lookup on the screen needs 自動ポストバック (1.5.2.0)

- **Tier:** Critical (KB claim used by designs; I9).
- **Evidence:** Nam's screen checks on MADLAB dev (1.5.2.0 build 201520), 2026-11-14/15, probe sites lines 44954 / master 44953 left by `pls kb-verify` (D40 unguarded); source reads in `plans/2026-11-14-kb-verify-results-store-promo/source-notes.md` (observations 1–7, H1–H4).
- **Nam's decision (2026-11-15, AskUserQuestion):** new task with its own budget; curator updates D40, review, commit after review with no High open.

## Work

1. KB (curator): D40 — screen part verified by a person: with the link written in the JSON form and the site saved on the screen, choosing the master fills the `To` column only when the link column has 自動ポストバック (`AutoPostBack`) on; `OverwriteForm` not needed; without it nothing is filled (also after F5). Source refs. API create (NumB 0) stays failed/open (H1). Observation 1 open. Not covered: saved value after save/reopen, other roles, Overwrite. D41a: note only if the curator finds it affected. `skills/README.md` KB version.
2. `docs/review-findings.md` D40 row; `docs/tech-debt.md`: a kb-verify op to re-save a probe site's settings (to tell H1 apart) — no probe change now (no op exists: `pls_kbverify.OPS`).
3. Copy the screen observations as evidence into this folder.

## Out of scope

- Probe changes, `pls` code, the trial repository (DES-001 note → told to Nam).

## Acceptance

- KB says only what was observed or read (source refs); fails stay fails.
- Suites green (KB tests); review: no Critical/High open.
