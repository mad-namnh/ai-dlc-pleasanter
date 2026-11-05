# Independent architecture review after D3 (2026-11-05)

- **Reviewer:** independent agent in the role of an expert system architect. It was not involved in building the framework and worked on read-only copies.
- **Scope:** framework `ai-dlc-pleasanter` at commit cfe3520 (`pls` 0.6, skills after D1–D3, `templates/project`), with `pls-demo-equipment` as reference.
- **Question:** is the framework ready for D4, writing `docs/setup.md` and the `demo/` package?

## Verdict: GO with conditions

The whole new-app command path was run against a fake Pleasanter server, and every command exists and works:

`init` → `bootstrap-plan` → `bootstrap` → `bind` → `export` → `unpack` → `canon` → `lint` → `coverage` → `release-plan` → `apply` (with `mark-applied`) → `test` → `drift`

Also confirmed: the write guards hold, the release order is right, and a summary on a brand-new site is not treated as data-impacting.

**Conditions:**
- Three process decisions (B1–B3) must be made before D4, because the setup guide and the demo scenario describe them.
- Tool defects S1–S4 sit on the write path. Fix them before D5, the real rehearsal.

## Findings

| ID | Sev | Area | Evidence | Problem | Fix |
|---|---|---|---|---|---|
| B1 | Blocker | P5 on dev | `docs/plan.md` Step 4b decisions vs `pls-x-lifecycle` P5, `pls-p5-release-manager`, `gates.md` | The plan says P5 on dev runs release-plan → G4 → apply. The skills say P5 on dev is only drift 0 + a release record. Either way the app is on dev before G3/G4. | Pick one model and state it in all four places; tell the demo audience that on dev, G4 records the release. |
| B2 | Blocker | Roles and principals | lifecycle P2 (principals filled in by the person during P2), template `environments.json`, `http-check` | It is undefined who names the roles, and when groups, users, keys and principals must exist. The person has to stop mid-P2. `http-check` turns red for a restricted key that cannot read the parent folder. | Fixed demo roles (e.g. `demo/roles.json`); P2 reuses the role names already in `principals`; a G2 check that every `${principal:x}` and every `as_key` exists; in `http-check`, 401 = bad key and 403/404 = valid key without access. |
| B3 | Blocker | P2 skeleton probe | `pls-p2-solution-designer/references/new-sites.md` vs lifecycle P2 and P3 step 1 | The new-site reference wants a skeleton probe before G2. No `pls` command creates probe sites, and bootstrapping the real sites before G2 contradicts the lifecycle, so the agent would improvise. | Either allow a person-confirmed `bootstrap` in P2, or ship skeleton exports per ReferenceType in the KB. |
| S1 | Should | bootstrap | `pls.py` bootstrap, `pls_http.py` bootstrap | Running `bootstrap --yes` twice creates duplicate sites and silently rebinds the ids. | Refuse when the status is `created`; when it is `partial`, finish only the missing steps. |
| S2 | Should | Fold-back loop | P3 step 6, lifecycle P3, `pls.py` drift baseline | After a later apply where `mark-applied` finds differences, the plan stays `planned`, and the fold-back release is refused as drift. It works only for the very first release. | Record `applied-with-differences` (post-apply export as the baseline), or a person-confirmed accept in `mark-applied`. |
| S3 | Should | Audit | `pls.py` `release_plan` | `release-plan` overwrites an existing release folder, including an `applied` plan. `--accept-drift` takes any string. | Refuse an existing release id; require that the decision file exists. |
| S4 | Should | Rollback | `pls.py` rollback payload, `pls_http.py` `apply_release` | Restore does not revert `InheritPermission` or `Permissions`. An error during restore is not caught, so no apply log is written. | Snapshot and restore permissions; catch errors per step; always write the log. |
| S5 | Should | lint in P2 | `pls.py` `read_tree` / lint | A meta-only `config/<site>` crashes lint with rc 2. An unresolved `${principal:x}` is only caught at `pack`. | Skip meta-only sites; add a reference-resolution rule per environment. |
| S6 | Should | Coverage | `pls.py` `coverage` | An empty `traceability.json` passes, and REQs missing from it are not reported. | Compare against in-scope `requirements/REQ-*.md`; print a total. |
| S7 | Should | CRLF scripts | `pls.py` unpack / `read_tree` | Script bodies with CRLF never round-trip, so drift always shows a change. | Read and write scripts with `newline=""`. |
| S8 | Should | dev fixes | `release_plan` migration gate | On dev, a P4→P3 fix that removes a choice or column, or adds a summary, needs a migration and a G2 reopen. A likely stall in the demo. | A person-acknowledged "test data only" override for `role: dev`, recorded in the plan. |
| S9 | Should | Person-run commands and keys | lifecycle rule 3; Windows `setx` | The agent shell has no stdin, so the person uses their own terminal. `setx` variables do not reach an already-running Claude Code. | `setup.md`: own terminal, restart after `setx`, or `file:` keys. Template `.claude/settings.json`: allow `python pls.py *`; deny reading `.pls/**`, payloads, rollbacks and results. |
| S10 | Should | Stale docs | README status/layout, framework `CLAUDE.md` (spike-era rules), HANDOFF environments ("browser only"), `skills/README.md` (copy by hand), references to a `setup.md` that does not exist yet, `bootstrap.json` "next" text, plan D3 `--framework` | Contradicts the `init` / HTTP workflow. | D6, before D7. |
| N1 | Nice | skills sync | `pls.py` `sync_skills` / `skills_check` | Orphan skills are not reported; every difference is reported as "newer"; the launcher and template are not synced. | Report and remove orphans; compare versions; include the launcher and template. |
| N2 | Nice | Launcher | `LAUNCHER` | A missing lock without `PLS_HOME` gives a raw traceback. | Show a clear message. |
| N3 | Nice | init UX | `init_project` | No `.pls/`, no `git init`; `parent_id` and principals are edited by hand. | Options `--parent-id`, `--url`, `--roles`; write `.pls/connections.json`; run `git init`. |
| N4 | Nice | unpack | `unpack` | Overwrites a site folder that has uncommitted edits. | Refuse a non-empty folder without `--force`. |
| N5 | Nice | P5 report | P5 skill | A new app's diff report is stitched together from incremental raw diffs whose values are cut at 70 characters. | A cumulative diff from the skeleton. |
| N6 | Nice | Misc | result names, `_stamp`, the mark-applied table header | Same-day result files overwrite each other; coverage mixes environments; the header labels read backwards. | Add time and environment to result names; fix the labels. |

## Verified by running

- **Unit tests:** 46 python + 6 node pass.
- **`init`:** creates the template, folders, launcher, 7 skills and a lock with hashes. In the new project, `lint` → 0 issues, `coverage` rc 0, `skills check` → match, and `http-check` gives clear errors.
- **Fake-server run:** bootstrap (refused without `--yes`), export, unpack, canon, release-plan (order, permission-impacting, new-site summary as a note), `apply --yes` + `mark-applied`, and two role test suites. The write guard refuses `test` and `apply` without `allow_write`.
- **Defects reproduced:** S1, S2, S3, S5, S7 and N1.
- **Not verified:** real Pleasanter, the browser runner, a Windows console.

**Token cost:** acceptable. All skills, references and `CLAUDE.md` together are about 80 KB, roughly 20–25k tokens. The larger risk is the agent improvising around S2, S8 and B3, and a permission prompt on every command (S9).

## Resolution (2026-11-05, D3b)

| ID | Resolution |
|---|---|
| B1 | Decided by Nam: P5 on dev = record only. plan.md, lifecycle, P5 and gates now agree |
| B2 | Decided by Nam: roles prepared before the demo (`demo/roles.json` in D4). P2 uses only roles in `principals`; G2 shows the roles; lint L-REF-02; `http-check` treats 403/404 as a valid key without access and 401 as a bad key |
| B3 | Decided by Nam: KB `references/skeletons.md` (createsite result, verified built-in columns); `new-sites.md` and lifecycle no longer ask for a probe write before G2 |
| S1 | `bootstrap` refuses a release that is already `created`; a `partial` one creates only the missing sites |
| S2 | `mark-applied` with differences → status `applied-differs` + `live-<site>.json`, used as the drift baseline |
| S3 | `release-plan` refuses an existing release id; `--accept-drift` must name an existing file |
| S4 | Rollback snapshot includes `InheritPermission`/`Permissions` when the payload changes them; a failing restore is logged and the others continue |
| S5 | lint skips meta-only sites; new rule L-REF-02 (every `${site/principal/env:x}` defined for every environment) |
| S7 | Script files are read and written with `newline=""`; CRLF bodies round-trip |
| S6, S8, S9, S10, N1–N6 | Open — S6/S8/S9/S10 in D6, before D7 |

Unit tests: 53 python (7 new) + 6 node, all pass.

