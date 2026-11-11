# Review — AU5 ADR-0018 and probe (round 1)

- Reviewer: `pls-x-reviewer`, model opus, effort high; working tree against `75dd68a`.
- Verdict: **accept with fixes**. No Critical or High.
- Reviewer ran: unit suite 3.12 (404 OK), node (15 pass), an offline harness with fake `Client.call` / opener (scratchpad, no network), `git status` before and after (unchanged).
- Not verifiable by the reviewer: real 1.5.2 behaviour, endpoint names and answers of stage B, whether a token is needed, the `TenantManager` default, soft delete.

| Id | Sev | Finding | Disposition |
|---|---|---|---|
| M1 | Medium | ADR question "delete keeps LoginId taken" listed as answered, but the probe cannot show it; a key that outlives its user was not checked | Fixed: question reworded to what the probe sees; candidate keys re-checked after delete (`keys_after_delete`); trash-box / LoginId moved to "not answered" |
| M2 | Medium | ADR names ADR-0017 rule 2 but not rule 3 (one member, the operator); B/C would silently break an Accepted ADR | Fixed: Context states both rules and that a superseding ADR is needed |
| M3 | Medium | Test-user passwords/keys in `.pls/` vs CLAUDE.md Mandatory 1 ("operator's own key files"); connections.json edits and password lifetime unstated | Fixed: Context says B–D need Nam's reading/change of Mandatory 1; open question on files, connections.json, password removal |
| L1 | Low | Issued key printable through `answer_shape` when it is in `Target` | Fixed: candidates scrubbed before the answer is printed |
| L2 | Low | Stage B results lost on exception / Ctrl+C | Fixed: result dict filled in place |
| L3 | Low | No skip if the read-back shows `TenantManager` | Fixed: stage B skipped |
| L4 | Low | Hand-cleanup text silent on `unconfirmed` | Fixed in docstring |
| L5 | Low | Stage B follows redirects (unscrubbed SSO host) | Fixed: no-redirect handler |
| L6 | Low | Final print may fail on a redirected cp932 console | Fixed: stdout reconfigured to UTF-8 |
| L7 | Low | A stage B failure may be the probe's flaw, not Pleasanter's | Fixed: ADR recommendation says so |
| L8 | Low | No lifecycle for test users | Fixed: open question |

Re-check after fixes (Orchestrator, reviewer's harness): all scenarios — no leak of password, operator key, issued key, cookie or host; Ctrl+C at `createapikey` keeps login/session results; cleanup-lookup failure deletes nothing and reports. Fixes not re-reviewed independently.
