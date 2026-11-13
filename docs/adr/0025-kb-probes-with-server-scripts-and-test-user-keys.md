# ADR-0025: KB probes with server scripts and a test user's key

- **Status:** Accepted (Nam: option B on 2026-11-12; deletion of the probe site confirmed on 2026-11-13) — built with AU1
- **Date:** 2026-11-13
- **Deciders:** Nam
- **Related:** I5, I9 (`docs/architecture.md` §2); ADR-0009 (version detection, `kb-verify` and its safety rules — this ADR amends them), ADR-0010 (mail and job safety outside production), ADR-0018 / ADR-0019 (test users per role and their keys), ADR-0023 (configuration shapes the KB does not cover); `docs/plan.md` Step 4d **AU1**; origin: trial `pls-demo-contracts` DES-001 C-1 (a server script reading the stored status), 2026-11-11

## Context

ADR-0023 lets the framework verify a configuration shape with `pls kb-verify` before a project relies on it. Two kinds of behaviour could not be probed that way, because the safety rules of ADR-0009 forbid them in probes:

- **server scripts** — probe sites refused `ServerScripts` at any depth, so behaviour such as "a `BeforeUpdate` script can read the stored value and refuse a direct status change" (trial C-1) had no automated check; the trial moved it to P3/P4 tests on the project's own site;
- **a second user's key** — probes ran under the administrator's key only (`as_key` forbidden), so "what a role can do on a site" (KB D19, D20) had only manual evidence.

Since AU5 (ADR-0018), `pls test-users --env <dev>` creates one test user per role on dev with its own key file under the operator's `.pls/test-users/`, and `pls principals` binds each role to a group. ADR-0010 records per environment whether mail goes to a sink, is disabled, or is live.

## Open questions

- [ ] Site deletion through the API on 1.5.x — **source-derived, not yet observed on a server.** Source at tag `Pleasanter_1.5.2.0` (read 2026-11-13): `Controllers/Api/ItemsController.cs` has `POST {id}/DeleteSite`, which calls `ItemModel.DeleteByApi(referenceType: "Sites")` → `SiteUtilities.DeleteByApi`; that method reads no body field and checks rights through `SiteValidators.OnDeleting` (not read). Whether the site goes to a trash box (`Sites_Deleted`) or is removed, and what happens to its records, is not read. `pls` therefore believes a delete only when `getsite` no longer finds the site afterwards; the first supervised run records the observed behaviour in the KB (curator, with that run's report).
- [ ] The names a server script uses to reach beyond its record (`items`, `notifications`, `httpClient`) come from the Pleasanter manual's object list as known to the framework, not from a check of the source at the version's tag. Whether `items` / `httpClient` in a server script honour the acting user's rights is not verified either.
- [ ] While a roles probe runs, the site's permissions are `User,<principals.admin>,511` plus the roles' groups, with inheritance cut. That assumes `principals.admin` is the user behind the operator's default key; if it is not, that key may lose access to the probe site, and teardown and delete then fail (the probe is `error`, a person cleans up). Not verified how Pleasanter treats a tenant administrator here.
- [ ] Not verified on a server: that `updatesite` without `ServerScripts` removes a stored script (D4 says SiteSettings are replaced whole; never round-tripped with a script by a probe), and that `Permissions` in `updatesite` replaces the list (D15). The first supervised `kb-verify` run reads the site back after the teardown.

## Options

### Option A — Keep the ADR-0009 rules; such behaviour is tested only in projects (P3/P4)
- Pros: nothing to build; probes cannot run code or act as another user.
- Cons: the answer is found again by each project, after G2; the KB stays manual for scripts and roles (AU1 not met).

### Option B — Allow both in `kb-verify`, under guards that `pls` checks (recommended)
A probe may carry server scripts at the top level of its settings and steps under a declared role's key, only when all of these hold:
1. the environment is `role: dev` and not a sandbox, and the probe site is under the probe folder (ADR-0009, unchanged);
2. the environment's `side_effects.mail` is `sink` or `disabled` — whatever a script does, no mail reaches a person;
3. a script body does not name `items`, `notifications` or `httpClient`, nor any of a list of common ways around a name (escapes, `globalThis`, `this`, `eval`, `Function`, `constructor`, `prototype`, `Reflect`, `Proxy`, `fromCharCode`, computed access other than `[0]` / `['literal']`); notifications and reminders stay forbidden at any depth. This refuses the obvious routes; it is not a sandbox: a script runs with the administrator's rights when the administrator's key saves a record, so the review of the probe file is the control against a script that reaches another site or the network;
4. each role is declared with its permission value (`roles: {<role>: 1–511}`), bound to a group on the environment, and its key reference is the test user's own key file written by `pls test-users` (never an operator's or a person's key), and that file does not hold the operator's default key;
5. the probe has a teardown without server scripts; after the run — also after a failure or an unexpected error — `pls` saves it, and for a probe with roles sets the site's permissions back to the administrator alone (a probe without roles never changes them). A site named by the state file but not provably the probe's own is never written (ADR-0009, unchanged).
A rule the probe file alone decides (3, 4's declaration, 5's teardown) refuses the whole `kb-verify` run before any write; a condition of the environment (2, 4's group and key file) makes only that probe `error` with the reason, before anything is written for it, and the other probes still run.
- Pros: C-1-style behaviour and role behaviour are verified once, in the framework, with evidence per version; no project decides it.
- Cons: a probe runs code on the dev server with the administrator's rights and acts as a test user; a mistaken script that gets past the name check could write outside the probe folder or call the network — the review of each probe file is part of the control.

### Option C — Server scripts only
- Pros: smaller change.
- Cons: role behaviour stays manual.

## Decision

**Option B** was chosen by Nam on 2026-11-12 (AskUserQuestion; the option he picked: "Both, guarded (Recommended)" — "kb-verify may run server-script probes and probes under a test user's key (keys.<role> from AU5). Guards: role dev only, the probe folder only, side_effects.mail must say no mail, probe site deleted afterwards. A write to dev still needs the person's command or --yes.").

On 2026-11-13, asked whether "left harmless" may stand in for deletion while the delete API is unverified, Nam answered: "can build duoc viet xoa luon cho AU1, apply patch rồi review vòng 2" (build the deletion too). Built as guard 6:

6. after the teardown of guard 5, `pls` deletes the probe site (`/api/items/<id>/deletesite`, the route of the 1.5.2 source) — only a site that `getsite` shows to be this probe's own just before — and believes the delete only when `getsite` answers 404 afterwards (any other answer — 200, 401, 5xx — is not believed); then the state file forgets it and the next run creates a new site. A delete that is refused, fails, or answers 200 while the site is still there leaves the site as guard 5 made it (no script, no grant), makes the probe `error` with the reason, and the next run reuses the site. Probes without a script or roles are unchanged (their site is kept and reused, ADR-0009).

## Consequences

- Easier: P2 can ask for a probe of a script or a role behaviour; `pls kb-verify` answers it on the environment's version, and the KB records it (ADR-0023 order of sources, step 4–6).
- Harder / costs: a probe file with a script or a role is reviewed like code; a person runs `kb-verify` (or names `--yes` for that dev environment) as before; the dev environment needs `pls test-users` and `pls principals` first for role probes.
- ADR-0009 (Proposed) still lists "no server scripts" and "no `as_key`" among its probe rules; this ADR amends them, and ADR-0009 changes only with Nam's decision on it.
- Built (2026-11-13): `tools/pls/pls_kbverify_guarded.py`; `kb-verify` per-role clients, permissions of the probe site while it runs, forced teardown, deletion with read-back; tests `tools/pls/tests/test_kbverify_guarded_probes.py` (the fake server's `deletesite` follows the source-derived route). The probe for C-1 itself is written by the KB curator with evidence, when a project asks for it.
