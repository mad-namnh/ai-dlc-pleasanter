# ADR-0010: Mail and scheduled-job safety outside production

- **Status:** Proposed (2026-11-05)
- **Date:** 2026-11-05
- **Deciders:** Nam
- **Related:** TD-10 (mail deferred), ADR-0012 (background server scripts), ADR-0003 (production), I3; plan Step 4c

## Context

Notifications (通知) and reminders (リマインダー) round-trip through the site API (spike checklist rows 13–14) and are part of `config/`. They are not only configuration: **they run**. A notification fires when a record changes; a reminder fires on a schedule. The brownfield candidate also runs **scheduled server scripts** (ADR-0012) and sends mail.

On a non-production environment this is a risk the framework currently ignores:
- whether dev can send real mail is **unknown** for the candidate project (SMTP configured by the server operator, outside Pleasanter configuration);
- a configuration copied from production carries real addresses and placeholders (`[Manager]`) that resolve to real users;
- `pls test` creates and changes records on dev and executes processes, which fires notifications;
- reminders and scheduled jobs keep running on dev whether or not anyone is testing.

TD-10 deferred mail for the demo stage. A real project cannot defer it: a test run must never mail customers or staff.

## Open questions

- [ ] Is SMTP configured on the candidate's dev and stg, and to which server? — *customer IT / server operator*.
- [ ] Can a mail sink (smtp4dev, MailHog or similar) be installed for dev, and can the agent read it (API or files)? — *customer IT*.
- [ ] Field names of the address settings of reminders (notifications use `Address`, KB `schema.md`) — *spike*.
- [ ] Can reminders and scheduled jobs be disabled per environment without changing the configuration that is released? — *probe*.

## Options

### Option A — Rely on people (checklists, care)
- Pros: no code.
- Cons: one forgotten test sends real mail; not auditable.

### Option B — Declared state per environment + guards + lint
- Pros: the tool refuses risky actions until someone states that the environment is safe; cheap.
- Cons: the declaration can be wrong; still no proof that mail is correct.

### Option C — Option B + a mail sink required for mail tests
- Pros: mail becomes testable (recipients, subject, body) instead of "not automatically testable".
- Cons: needs customer IT to install and expose the sink.

## Decision

**Option B now, Option C as soon as a sink exists (proposed).**

1. `environments.json` gets `envs.<e>.side_effects = {"mail": "unknown|sink|disabled|live", "jobs": "unknown|disabled|live"}`. Default `unknown`. Only the person sets these values, after checking with the server operator; the agent never changes them to get past a refusal (same rule as `allow_write`).
2. **Guards in `pls`:**
   - `test` refuses specs that create/update records or execute processes on a site with notifications, reminders or a scheduled job, unless `mail` is `sink` or `disabled`;
   - `apply` / `bootstrap` on dev or stg print a warning in the plan when the release adds or changes notifications, reminders or jobs and `mail`/`jobs` is `unknown` or `live`, and refuse when it is `unknown`;
   - prod is never written by `pls` (ADR-0003), so nothing changes there.
3. **Lint `L-MAIL-01`:** a literal mail address in a notification or reminder is an error. Use `${env:x}` (per-environment address) or `${principal:x}`; Pleasanter placeholders such as `[Manager]` are allowed.
4. **P4 with a sink:** test specs get an `op: "mail"` step that reads the sink and checks recipients and subject. Without a sink, mail stays a configuration check, and G3 says so.
5. **P2 / impact checklist:** any change touching notifications, reminders or jobs states the side effects per environment.

## Consequences

- Easier: tests on dev cannot mail real people by accident; mail can finally be tested (TD-10 closed when the sink exists).
- Harder / costs: one question to customer IT per environment before the first test; specs on sites with notifications need a sink.
- Follow-up: implement the flags, guards and L-MAIL-01; spike the reminder address fields; write the `mail` test op once a sink is available; update `docs/setup.md` (state of mail per environment is a setup item).
