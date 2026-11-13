# Review — P2-6 ADR governance

- **Reviewer:** `pls-x-reviewer`, model `opus`, effort `high`; round 1 of 2; range `3255e97..7899987` plus the working tree of part 2.
- **Verdict:** accept with fixes — 0 Critical, 0 High, 3 Medium, 5 Low. `git status` identical before and after the call.
- **Reviewer ran:** read-only git, `git apply --check` of the patch (exit 0), Python suite 444 OK, node 15 pass.
- **Not verified by the reviewer:** Python 3.10; whether skills conflict with the patched rule 1; test coverage of the "Built" claims for 0006, 0011, 0016 (code exists); A4 items 2 and 3 (closed by earlier commits, outside the diff).

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| M1 | Medium | `docs/architecture.md` §7.3 rows still had stale versions (P3 0.1, P4 0.1, P5 0.1) and KB coverage "D7–D10, S7"; §9 "Evaluate P2 0.5" | Fixed: parentheticals removed, KB row points to `skills/README.md`; §9 says "the current P2 version" |
| M2 | Medium | ADR-0020 / ADR-0021 omitted that record-changing `pls test` outside dev runs with `--yes` and no gate record (`pls.py` `_confirm`) | Fixed: ADR-0020 `pls test` row names typed confirmation or `--yes` on the person's instruction, "no gate record in that case"; ADR-0021 says which stg writes need G4 and which need G4 or confirmation |
| M3 | Medium | CLAUDE.md patch: new headline contradicted `pls test` on stg and cited a Proposed ADR; the general "role dev + allow_write" was narrowed to the spike | Fixed: headline unchanged, ADR-0020 citation dropped, new line keeps "role dev + operator opt-in" for every other write path; `git apply --check` passes |
| L1 | Low | `pls package` needs G4 in every environment, not only outside dev | Fixed in ADR-0020 (preamble and row) and architecture I4 |
| L2 | Low | `pls_gate.py` docstring cited ADR-0020 but described the old scope; `resolve_key`, `actor`, `merge_install`, `setup_profile`, `apply_profile` cited no ADR | Fixed: docstring scope corrected; the five functions cite ADR-0021 / ADR-0022 |
| L3 | Low | README row 0012 stated the replacement by ADR-0020 as decided | Fixed: "ADR-0020 (Proposed) proposes to replace them" |
| L4 | Low | HANDOFF repo table stale (ADRs 0001–0008, KB 0.9, …); "review" pointed to a file not yet written | Fixed: table points to `docs/adr/README.md` and `skills/README.md`; this file is the review |
| L5 | Low | ADR-0021 overrides table missing `CLAUDE_CONFIG_DIR`, `CLAUDE_CODE_SESSION_ID` | Fixed: listed as variables that affect no guard |

No second round: no Critical or High finding; every Medium fixed.
