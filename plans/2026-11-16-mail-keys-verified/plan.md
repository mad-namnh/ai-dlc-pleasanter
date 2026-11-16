# Plan — mail address keys into VERIFIED_KEYS

- **Tier:** Critical (scope gate `VERIFIED_KEYS`, ADR-0001).
- **Origin:** held back in 5554586 (review H1) until the keys are kept out of git; that was committed in 2d365cf with Nam's approval ("2 duyệt", 2026-11-16). Nam 2026-11-16: "cu lam tuan tu het khong can hoi".
- **Change:** `pls_scope.VERIFIED_KEYS` + `AddressBook`, `MailToDefault`, `MailCcDefault`, `MailBccDefault` (evidence: KB D47, kb-verify 2026-11-16, all four read back as sent). Tests: test_scope (the four are verified; held-back list without them), test_pls mail release-plan test (passes without a decision record — this replaces its earlier assertion that release-plan refused them, which encoded the held-back state).
- **Docs:** KB D47 row (curator), KB 0.30, ADR-0010 follow-up, ADR-0023, review-findings D43–D47, HANDOFF.
- **Acceptance:** (1) release-plan of a site whose live settings hold the four keys passes without `--accept-unverified` and writes no address into releases/; (2) the other held-back keys stay unverified; (3) tests fail on the parent; (4) suites green; (5) review: no open Critical/High.
