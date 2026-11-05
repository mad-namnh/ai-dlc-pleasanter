# Input — P3 case 001 (slice #3, equipment loans)

The scratch project is `pls-demo-equipment` at the end of G2. It contains:
- the requirements;
- `design/`: DES-001, PRB-001 and the slot ledger;
- `traceability.json` without tests;
- `environments.json` (dev only, ids bound);
- **the skeleton exports unpacked into `config/`**;
- `releases/B-20261105-dev/bootstrap.json`, which must be included (run 1 left it out, and `pls` then treats a new summary as data-impacting);
- `.gitignore` and `requirements/sources/`.

Framework at `../fw`: `tools/pls`, plus the skills KB, `pls-x-lifecycle` and `pls-p3-config-builder`. Project `CLAUDE.md` from the template (stage demo, target dev).

There is no network, so the agent stops before the deploy. Prompt: "G2 is approved. Continue."

Reference answer: `pls-demo-equipment/config/` after R-20261105-E02-dev. Compare with `pls diff` against an export built from it.
