# Plan — mail address settings kept out of git (settings coverage WS1.5)

- **Tier:** Critical (I7 customer data; the updatesite write path).
- **Decision:** Nam 2026-11-15, verbatim "1. loai han khoi git" (plans/2026-11-15-settings-coverage/plan.md, Decisions).
- **Change:** pls_http.LIVE_ONLY_KEYS (AddressBook, MailToDefault, MailCcDefault, MailBccDefault). logical() drops them (unpack, harvest, drift, compare); release-plan / plan: not counted by L-DEP-01, left out of rollback files; Client.apply reads the site just before every updatesite and carries its values (a payload's own value is never sent); lint L-SEC-01 reports them in site.json. ADR-0010 Consequences as-built note (decision quoted); TD-59 browser runner.
- **Acceptance:** (1) never in git or release files; (2) release-plan not refused by L-DEP-01; (3) a write keeps the live values and never sends git's; (4) lint reports a hand edit; (5) new tests fail on the parent; (6) suites green incl. 3.10; (7) review no open Critical/High.
