# Input — P4 case 001 (slice #3, equipment loans)

The scratch project is `pls-demo-equipment` at the end of P3. It contains:
- the built `config/`;
- `traceability.json` without tests;
- no `tests/api/`;
- the release folders of R-20261105-E01/E02-dev, which must be included (run 1 left them out).

Roles (key names): `admin` = a 総務 member, `staff` = a 社員 member. Framework skills: KB, `pls-x-lifecycle`, `pls-p4-test-writer`. There is no network, so the agent writes the specs and hands over the exact `pls test` commands.

Prompt: "P3 is done and deployed to dev. Continue."

Reference answer: `pls-demo-equipment/tests/api/equipment.json` + `staff.json` (T-101…T-111, all pass on dev).

**Building the scratch state.** The source repository has one commit for P1–P6 (`547f549`), so the state is rebuilt with `git archive 547f549` and trimmed as listed above. Remove every note written after this phase from the copied files (e.g. "Revised after T-102" lines in REQ or DES files, later test ids in `traceability.json`): they leak the answer.
