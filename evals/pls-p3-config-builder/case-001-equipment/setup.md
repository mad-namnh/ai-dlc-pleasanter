# Setup — P3 case 001 (slice #3, equipment loans)

For whoever runs the case; the runner never opens this file.

The scratch project is `pls-demo-equipment` at the end of G2, with the files `input.md` lists. `releases/B-20261105-dev/bootstrap.json` must be included (run 1 left it out, and `pls` then treats a new summary as data-impacting); the skeleton exports must be unpacked into `config/`.

Reference answer: `pls-demo-equipment/config/` after R-20261105-E02-dev. Compare with `pls diff` against an export built from it.

**Building the scratch state.** The source repository has one commit for P1–P6 (`547f549`), so the state is rebuilt with `git archive 547f549` and trimmed as listed above. Remove every note written after this phase from the copied files (e.g. "Revised after T-102" lines in REQ or DES files, later test ids in `traceability.json`): they leak the answer.

Since 2026-11-17 the input no longer says "Framework at `../fw`: `tools/pls`, plus the skills …": that folder lies outside the run's scratch folder (a void run under the brief), and the scratch project gets no copy of `pls` (`evals/README.md`, "Local `pls` commands"). Copy the three skills into the scratch project's `.claude/skills/`; relay `pls` commands as the README says.
