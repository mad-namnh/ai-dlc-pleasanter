# ADR-0010: Mail and scheduled-job safety outside production

- **Status:** Proposed (2026-11-05) — mail part implemented on branch `brownfield-adr` (plan BR1); jobs guard implemented 2026-11-09 (ADR-0012 option B)
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

### Implementation notes (BR1, 2026-11-05)

- `tools/pls/pls_side_effects.py`; wired into `lint`, `release-plan`, `apply`, `test` and `http-check`; 15 tests in `tests/test_side_effects.py`. An independent code review found nine gaps (wrong site for creates without `site`, `--var` records of other sites, plans made before the check, processes sharing a name, addresses glued to Japanese text, …); all fixed and covered by tests.
- `bootstrap` needs no guard: it creates empty skeleton sites (`SiteSettings {}`, D26), which send nothing. The guard applies to the release that configures them.
- `test` reads the **live** settings of every site a writing spec touches, so mail elements added outside git are also caught. A create goes to its `site` or the command's site (never `run_on`); an update, delete or process run on a record given by `--var` counts for **every** site of the environment, because its site is unknown. Specs that only read (`get`, `list`, `siteConfig`) are never blocked.
- `apply` refuses a plan that records no mail changes at all (made before this check) unless mail is `sink` or `disabled`: re-run `release-plan`.
- Every notification and reminder counts, also disabled ones and non-mail notification types (safe side).
- `release-plan` records the changed mail elements per site (`per_site.<site>.side_effects`, `MAIL …` lines) and notes when `apply` will refuse; plans for prod are not affected (prod is never written by `pls`).
- Reminders count as mail elements.
- **Jobs guard (2026-11-09, audit F-05).** The tool cannot see the tenant (D31), so a project "has jobs" when it declares scheduled scripts in git (`config/_tenant/scheduled-scripts/`, ADR-0012). A scheduled script is tenant-wide, not tied to a site, so every declared job counts for every writing test.
  - `test`: a spec that writes is refused while the project declares jobs and `jobs` is `unknown`; `live` prints a warning. A project that declares no jobs is not blocked, even with `jobs: unknown` — onboarding asks for the list.
  - `release-plan`: records `plan.jobs` (fingerprint per job = sha256 of its index entry and body **with `${site:x}` / `${principal:x}` / `${env:x}` resolved for the env**, so a changed environment value is a changed job) and the manual deploy step; when jobs changed, the resolved files the operator copies are written to `releases/<R>/scheduled-scripts/`; operator report row. A bad `_index.json`, a body that is not UTF-8 or an unresolved reference refuses the plan.
  - Baseline: the last applied release of the env whose job changes a person confirmed with `pls jobs-verified <R> --by <operator of the env or G4 approver> --quote … [--approved-by <G4 approver>]` (or that changed no job; who may confirm: ADR-0012 implementation notes). Until the manual deploy is confirmed, the next release lists the same changes again. None → every job counts as added.
  - `apply`: refuses a release that changes jobs while `jobs` is `unknown`; a plan without a `jobs` record (made before this check) while the project declares jobs and `jobs` is not `disabled`; a hand-broken `jobs` record; and a plan whose scheduled scripts in git (or their environment values) changed since it was made. Prints the manual step. Lint L-JOB-01 checks the layout.
  - **Sandboxes** (ADR-0011) share the base environment's SMTP and tenant: their `mail` / `jobs` state is the riskier of their own copy and the base's current value (also for mail), and a sandbox release never lists or deploys scheduled scripts — they go through the base environment's releases only.
  - Limits: a release plan is made per set of sites, so a change that touches only scheduled scripts still needs a release plan with at least one site. Lint of the job bodies (L-REF-01, L-SEC-01, `node --check`, ADR-0012 item 2) is not built yet.
- The mail sink step for P4 (`op: "mail"`) is not built yet: it needs a sink on the candidate's dev.
- **Known limit:** a server script or a summary that writes to **another** site can fire that site's notifications; the guard does not follow such chains. It is safe only when the other site is also in the spec or in the environment's site list (as with `--var` records). Covered fully once mail is `sink` or `disabled`.

## Consequences

- Easier: tests on dev cannot mail real people by accident; mail can finally be tested (TD-10 closed when the sink exists).
- Harder / costs: one question to customer IT per environment before the first test; specs on sites with notifications need a sink.
- Follow-up: implement the flags, guards and L-MAIL-01; spike the reminder address fields; write the `mail` test op once a sink is available; update `docs/setup.md` (state of mail per environment is a setup item).
