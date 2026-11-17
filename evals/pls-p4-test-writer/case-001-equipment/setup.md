# Setup — P4 case 001 (slice #3, equipment loans)

For whoever runs the case; the runner never opens this file.

The scratch project is `pls-demo-equipment` at the end of P3, with the files `input.md` lists. The release folders of R-20261105-E01/E02-dev must be included (run 1 left them out).

Reference answer: `pls-demo-equipment/tests/api/equipment.json` + `staff.json` (T-101…T-111, all pass on dev).

**Building the scratch state.** The source repository has one commit for P1–P6 (`547f549`), so the state is rebuilt with `git archive 547f549` and trimmed as listed above. Remove every note written after this phase from the copied files (e.g. "Revised after T-102" lines in REQ or DES files, later test ids in `traceability.json`): they leak the answer.
