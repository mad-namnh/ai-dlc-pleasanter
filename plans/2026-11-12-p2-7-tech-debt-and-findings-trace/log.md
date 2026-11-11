# Log — P2-7 tech debt and findings trace

Counts: subagent calls (not eval cases) 1/6, review rounds 1/2, fix attempts 0/3.

- 2026-11-12 | another session has uncommitted work (ADR-0023, `pls.py`, `pls_address_principals.py`, tests, KB, lifecycle) — stop point 9 reported; Nam chose to run P2-7 in parallel, touching only `docs/review-findings.md`, `docs/tech-debt.md` and this folder; `HANDOFF.md` after the other session commits.
- 2026-11-12 | checked each open item against the code: closed since the review — D3-review S6 (P2-2), N3 (setup / init), R2-6 (P0-5), F-02 (P2-6), F-07 (0 `ResourceWarning` in the suite output of 2026-11-11), F-08 (P2-9); open — S8, S9 (part), S10, N1, N2, N4, N5, N6 (part), R3-6, F-03, F-06, slice S6, S2-6, D7 post-deploy check → TD-25…TD-35; roadmap P3-2…P3-8 → TD-36.
- 2026-11-12 | decided without asking: register ids are not renamed (other documents cite them); a note says they are cited as RF-…; S2-7 is a project item of `pls-demo-inquiry`, not framework tech debt.
- 2026-11-12 | found: the register named lint L-SLOT-02, which does not exist (only L-SLOT-01); corrected.
- 2026-11-12 | subagent call 1/6: `pls-x-reviewer`, `sonnet`, effort `medium`, round 1/2 — accept with fixes, 2 Medium + 2 Low; M1 and L1 fixed (TD-37, TD-38, TD-35 text, D21 test name), M2 answered by grep and the suite run (`review.md`).
- 2026-11-12 | before the commit (working tree also holds the parallel session's uncommitted `pls_scope.py`, `test_scope.py`, KB files — not staged): `python -m unittest discover -s tools/pls/tests` → 447 OK; `node --test tools/pls/tests/test_runner.mjs` → 15 pass. Committed only `docs/review-findings.md`, `docs/tech-debt.md` and this folder. `HANDOFF.md` follows in a separate commit after the parallel session commits (plan, Out of scope).
