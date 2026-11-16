# Wording for Nam's approval — mail address settings kept out of git (stop points 1 and 2)

Nam's decision (2026-11-15, verbatim): "1. loai han khoi git". The texts below are the Orchestrator's wording of what that decision means in the framework; review round 2 (F1) asks that Nam approve them, because they add an exception to invariants I1 and I2. Nothing of this task is committed until he does.

## ADR-0010, Consequences (new bullet)

- As built (2026-11-16; decision by Nam 2026-11-15, verbatim "1. loai han khoi git" — `plans/2026-11-15-settings-coverage/plan.md`): `AddressBook`, `MailToDefault`, `MailCcDefault`, `MailBccDefault` hold customer mail addresses and never go to git. `unpack`, `harvest`, `adopt` drop them; payload, rollback and `live-<site>.json` files leave them out; each `updatesite` of `pls apply` and of its restores carries the values the site holds, from the read right before the write (`pls_http.LIVE_ONLY_KEYS`; kb-verify probe sites are written directly and hold none); lint L-SEC-01 reports them in `site.json`. Consequences: each environment's values are set on the screen; drift, compare and read-back do not see them; `release-plan` still refuses a site that holds them without round-trip evidence (`--accept-unverified` until a probe proves the round trip); a production package's checklist tells the operator to copy them into each file before updatesite (TD-60); the browser runner and `pls pack` output do not carry them (TD-59); `siteConfig` test steps refuse them (results are committed). A project that committed them before keeps them in git history; lint reports them and the next unpack or harvest removes them from `site.json`.

## docs/architecture.md rows

| I1 | **Git is the desired state; Pleasanter is the runtime.** Every managed site exists in the project repository as unpacked configuration — except the mail address settings `AddressBook` / `Mail*Default`, which are kept out of git and live only on each site (ADR-0010) | Round-trip (spike B4), `pls drift` |
| I2 | **A deploy always sends the complete configuration and is preceded by a drift check.** `updatesite` replaces SiteSettings entirely (D4) | `pls plan` refuses partial payloads; refuses to plan while unresolved drift exists. Exception: the mail address settings kept out of git (`AddressBook`, `Mail*Default`, ADR-0010) are not in payload files; `pls apply` adds the site's own values to each write |
| L-SEC-01 | D5 | No secret-like values in configuration or scripts, and no mail address settings in `site.json` (`AddressBook`, `Mail*Default` — kept out of git, ADR-0010; payloads leave them out even when site.json has them). Also a refusal before writing: `unpack`, `harvest`, `adopt` (config/) and `release-plan` (payload from config/, rollback from the live site) write nothing when one is found |
| L-DEP-01 | D4 | Deploy payload contains complete SiteSettings (the mail address settings kept out of git excepted: the write carries the live values, ADR-0010) |

## Question

Approve as written ("duyệt"), change the wording, or choose another form (e.g. a short new ADR instead of a Consequences bullet)?
