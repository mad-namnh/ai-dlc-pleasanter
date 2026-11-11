# Review — AU2 probe + ADR-0017 (pls-x-reviewer, opus, high; working tree against b4e90dd)

## Round 1 — accept with fixes
| # | Sev | Finding | Disposition |
|---|---|---|---|
| F1 | High | `resolve_key(conn)` missing 2nd argument → probe crashes before any request | fixed: `resolve_key(conn, None)` |
| F2 | Medium | groups created in a failed step not deleted; `_find` ignored status; non-TransportError skipped the result | fixed: cleanup looks the name up again + ids answered by create; non-200 lookup raises; `BaseException` caught, result always printed; "unknown" when the final lookup fails |
| F3 | Medium | server URL could reach the printed result via transport errors / raw body | fixed: URL replaced by `<server>` in every message; raw body dropped |
| F4 | Medium | ADR claimed binding refuses ambiguous names; it reports them as missing | fixed in ADR rule 2 + tests in follow-up; binding defect noted there |
| F5 | Medium | dev/stg same tenant not addressed | fixed: open question added |
| F6 | Low | existing probe name not refused | fixed: stops, nothing created or deleted |
| F7 | Low | probe outside write-path inventory and run log | fixed: stated in ADR consequences and docstring |
| F8 | Low | sandbox env not refused | fixed: `sandbox_of` / `connection` refused |
| F9 | Low | plan.md stale | fixed |

Verified offline (fake client, no network): normal path → created 101, duplicate 102, both deleted, left []; lookup failure after create → error recorded with `<server>`, 101 deleted, left [].

## Round 2 — accept with fixes (all round-1 fixes confirmed except where noted)
| # | Sev | Finding | Disposition |
|---|---|---|---|
| R2-1 | High | cleanup deleted any id a create answered with — an unobserved `Id` could be another (tenant-wide) group; introduced by the F2 fix | fixed: only ids returned by an exact-name lookup are deleted; answered ids are reported (`create_answer_ids`, `create_answer_is_group_id`, `unconfirmed`), never deleted; failed cleanup lookup → nothing deleted |
| R2-2 | Low | string `GroupId` crashed the cleanup | fixed: digit strings converted, other values reported (`odd_group_ids`), never deleted |
| R2-3 | Low | host name could leak via TLS error text | fixed: URL, netloc and host name replaced by `<server>` |
| R2-4 | Low | exit 0 with groups left | fixed: non-zero when anything is left, unconfirmed or unknown |
| R2-5 | Low | ADR put group ids in `metrics.written` (site ids) | fixed: metric `groups_created` |

Verified offline by the Orchestrator (fake client): normal → rc 0, nothing left, `create_answer_is_group_id` true; create answering an existing group's id 7 → 7 not deleted, `unconfirmed` [7], rc 1; string ids → deleted, nothing left; TLS error with host → host not in output; delete 403 → rc 1, left [101, 102]; cleanup lookup fails → nothing deleted, rc 1.

**Not independently re-reviewed:** the review budget is 2 rounds (agent-rules §5). The R2-1 fix is verified only by the offline scenarios above. Nam decides whether the probe runs as is.

## Round 3 — code of `pls principals --create` (extra rounds allowed by Nam) — accept with fixes
| # | Sev | Finding | Disposition |
|---|---|---|---|
| F1 | Medium | non-Group roles, missing name (role-key fallback) and placeholders were created as groups | fixed: only `principal: "Group"` with a final `group_name` is created; anything else refused before the confirmation; test |
| F2 | Medium | a lookup answer of one page (TotalCount > Data, or 200 rows without count) was taken as complete → duplicate | fixed: `_lookup_all` returns unknown → refused; test |
| F3 | Low | docs/setup.md described only the manual step | fixed: paragraph + 5 troubleshooting rows |
| F4 | Low | bound roles not re-checked for duplicates | accepted, documented as a limit in ADR-0017 open questions |
| F5 | Low | exact-name check case-sensitive; server matching unknown | accepted, documented in ADR-0017 open questions |
| F6a | Low | Orchestrator normalised CRLF→LF in a KB file (curator's path) | disposition: line endings only, content unchanged — an exception to agent-rules §2 recorded here; next time the curator does it |
| F6b | Low | probe script kept although "retired" | ADR now says it stays as the record and is not run again |
| F6c | Low | no test for the run-log refusal of principals | fixed: test |
| F6d | info | G2 not checked before --create | accepted (same as other dev writes; not an ADR rule) |

After fixes: 3.12 404 OK (no skips), 3.10 404 OK (2 skipped), node 15 pass.
