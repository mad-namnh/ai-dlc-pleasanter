# Review — D40 lookup / 自動ポストバック

## Round 1 (pls-x-reviewer, opus, high) — accept with fixes

- **F1 High:** the Do rule dropped the safe branch; screen observations used settings saved on the screen, the framework deploys through `updatesite` (B1: link not in effect); `AutoPostBack` written through `updatesite` not covered; `Columns` is a verified key, so only the KB text guards. → Fixed: curator (Do/consequence/Not covered), Orchestrator (review-findings D40, README, HANDOFF).
- **F2 Medium:** "administrator" and "自動ポストバック off" not in the evidence. → Fixed: "account not recorded"; "not set by the person (default off per source)".
- **F3 Low:** "verified by a person" with `verified_on` []. → Fixed: "observed on the screen by a person (not a probe run)".
- **F4 Low:** HANDOFF without shape qualifier; dates 2026-11-14/15; FieldResponse l.2632. → Fixed.
- Not verified by the reviewer: Nam's observations themselves; OverwriteForm discrepancy (possible explanation `ResponseLookups.LookupClearFormData`, client posts) — recorded as open; `AutoPostBack` round-trip.
- Commands: read-only git; 3.12 suite 595 OK; node 15 pass; status unchanged.

## Round 2 (pls-x-reviewer, opus, high) — accept with fixes

- F1–F4 resolved in the KB; no Critical/High.
- **F-M1 Medium:** TD-48 said "screen side is verified". → Fixed (reworded with the qualifiers).
- **F-L1:** TD-47 (c) done, not closed. → Closed.
- **F-L2:** impact-checklist change deferred only in HANDOFF. → TD-49 (closed by the next commit, Nam: "lam ca de xuat cua ban").
- **F-L3:** HANDOFF next steps stale. → New next steps (H1 check on 44954, screen check on an `updatesite`-deployed site, saved value).
- **F-L4:** multi-line JSON difference, "at once", "nothing tells the person", account. → Curator (account now known: Nam "use admin", evidence obs. 8).
- Concern: Python suite 598/1 failure from out-of-scope concurrent edits (`pls_migrate.py`, `refusals_without_a_test.txt`, not this task) → this change verified in a clean worktree of HEAD + the in-scope paths. Trial repo: one new untracked hand-over file written on Nam's request (decision to reopen 1A), nothing else.
