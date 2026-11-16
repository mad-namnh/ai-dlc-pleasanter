# Review — mail address keys into VERIFIED_KEYS

## Round 1 (pls-x-reviewer, opus, high) — accept with fixes; H1 open
- **H1 High:** with the keys verified, a hand-typed key in site.json passed release-plan silently: the payload drops it, but raw-diff-<site>.md is built from config/ and was written with the address (and showed a change never deployed); single-site plan the same (earlier). → `live_only_in_git_refusal`: release-plan (plan_site) and single-site plan refuse with L-SEC-01 before writing; tests check every release file (rglob) and the refusal.
- **M1 Medium:** spike checklist row 30 still said held back → updated.
- **L1 Low:** the "kept from the live site" scope line cannot fire now → kept as a guard for a key added to LIVE_ONLY_KEYS later, with a comment.
- **L2 Low:** no person stops any more for a site holding the keys → release-plan prints a NOTE naming them with TD-59 / TD-60; test asserts it.
- **EV-02:** test expectation refused → passing judged legitimate by the reviewer (KB D47 is the probe ADR-0010 named).

## Round 2 (same reviewer, opus, high) — accept with fixes, Low only
- H1, M1, L1, L2 fixed as stated; new tests fail on the parent (reviewer ran them in memory).
- N1 Low: refusal and NOTE not in the docs → ADR-0010 follow-up, HANDOFF, KB D47 (curator).
- N2 Low: single-site plan printed REFUSED twice → prints the refusal once.
- Not verified → added: `--accept-unverified` does not get past the refusal (test).
