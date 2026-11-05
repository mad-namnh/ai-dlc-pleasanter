---
name: pls-p6-maintenance-triage
description: Phase P6 for inquiries and incidents (問い合わせ／障害) on a running Pleasanter application. Establishes facts first — drift, version change, environment differences, which scripts touch the field — then classifies the cause (configuration drift, script defect, data, requirement change, Pleasanter behaviour, environment) and routes it to the right phase. Use when a user or the customer reports that something does not work, works differently between environments, or changed by itself.
---

# pls-p6-maintenance-triage — from a report to the right phase

**Goal:** an evidence-based cause and a route (P1 change request, P6 drift decision, data migration, KB correction, environment fix) — **not a fix**. Nothing is changed in any environment in this skill.

## Inputs

- The report (who, what, when, which screen/record, which environment) — record ids only, never record contents in git.
- The project repository; the last applied release per environment; connections or site packages.

## Procedure

1. **Facts.** Restate the report in one paragraph: environment, site (logical name), record id, expected vs observed, since when. Missing facts → ask, in Japanese, in one message. If MADLAB cannot reach that environment (prod, usually), ask in the same message for a **site package** of the site: without data, with notifications, reminders and site/column permissions. It is stored in `.pls/packages/` (gitignored).
2. **Did the configuration change?** Reachable environment: `pls export --env <e> --site <s>` + `pls drift <export> --env <e> --site <s>`; differences → `pls classify`. Only a package: `pls env-compare --site <s> --source git --source <e>=<package>` (git = the last release; drift and classify read getsite exports only). This is the most frequent cause after "nobody changed anything".
3. **Did Pleasanter change?** Reachable: `pls http-check --env <e>` (build changed?) / `pls version`. Package: `pls version --env <e> --from-package <package>`. A version change makes every KB entry the behaviour relies on suspect (ADR-0009).
4. **Works here, not there?** `pls env-compare --site <s> --source <e1>=<export> --source <e2>=<export or package>`. The environment used as reference must itself show drift 0. `id-like` → map the id and compare again; `not-in-package` → ask for a package with that part.
5. **Which code touches it?** `pls xref --site <s>` → scripts that read or write the field; then read only those scripts' relevant lines.
6. **Side effects** (mail, scheduled jobs): `side_effects` of the environment and ADR-0010/0012 — a missing mail on dev may be by design.
7. **Classify** and route:

| Cause | Evidence | Route |
|---|---|---|
| Configuration drift | drift ≠ 0 | P6 decision: accept (→ P1 change request) or revert (release) |
| Script defect | xref + script lines + a failing reproduction | P1 change request (bug), P3 with `pls-p3-script-engineer` |
| Data | records inconsistent with the rules | data migration (ADR-0004) — never edit records directly |
| Requirement changed / misunderstood | behaviour matches the as-is spec | P1 change request |
| Pleasanter behaviour | matches a KB entry, or contradicts one | KB entry (I9); probe on dev |
| Environment | version, mail, jobs, permissions of the user | environment owner; `side_effects`, principals |

8. **Write** `ops/triage/<date>-<env>-<record id>-<topic>.md`: a short Japanese answer for the reporter (what happened, what happens next — no internal jargon), then the English analysis with the evidence (command outputs summarised, file:line of scripts). While evidence is missing, write it as an interim file with the open points marked and commit it; send the reporter only an acknowledgement until the cause is known.

## Never

- change configuration, scripts or data in any environment to "try" a fix;
- write record contents, personal data or secrets into the triage file;
- close a report as "cannot reproduce" without steps 2–5.
