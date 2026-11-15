# Review — scalar keys verified

## Round 1 (pls-x-reviewer, opus, high) — reject

- **H1:** the four mail address keys entered `VERIFIED_KEYS` against Nam's decision 2026-11-15 (kept out of git, WS1.5 not built) and no lint covers them → held back: 81 keys; test asserts they and `DashboardPartsAsynchronousLoading` stay unverified; KB D47 rule rewritten (curator): leave them out of git, set them on the screen, decision record until WS1.5.
- **M1:** inventory-checklist row 30; ADR-0023 Consequences follow-up line; review-findings rows D43–D47 and D46; sanitized evidence file in this folder, named in the pls_scope docstring.
- **L1:** KB "Keep only non-default values (`pls canon`)" was wrong for top-level scalars → reworded (curator).
- **L2:** per-key reading of the failed D46 probe → stated in the ADR-0023 follow-up line and the docstring.
- **L3:** KB version 0.28 in commit order (the uncommitted D40 change renumbers when it commits).
- **L4:** safety-relevant switches deploy as config-only → TD-63.

## Round 2 (pls-x-reviewer, opus, high) — accept with fixes; no Critical/High

- **M1:** D47 told people to set the mail keys on the screen and pass with a decision record; L-DEP-01 refuses a live-only key whatever the flags → D47 (curator): until WS1.5, `pls` cannot release a site that sets them; do not set them on managed sites, or ask Nam for an exception. README and docstring aligned.
- **M2:** five guard switches (+ `ExtendedHeader`) became config-only → held back from `VERIFIED_KEYS` (decision record still needed); 75 keys; TD-63 now names the condition (a classify rule per switch, WS2); test.
- **L1:** docstring heading "Not here:". **L2:** checklist row 30 marks API update. **L3:** SKILL.md Fact 2 says `pls canon` covers only Processes / Views (curator).
- **L4:** per-key reading of the failed D46 probe (ADR-0023 step 6 is written per probe) → recorded in the ADR-0023 follow-up line; Nam asked to confirm in the report.
