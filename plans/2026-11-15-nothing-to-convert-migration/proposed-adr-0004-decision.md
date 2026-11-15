# Proposed change to ADR-0004 Decision 2 (needs Nam's approval of this exact text — stop point 1)

Direction chosen by Nam (2026-11-15): "Sửa ADR + apply kiểm lại". Version 1 of this text was approved ("duyet", 2026-11-15); review round 1 changed it (F2–F6), and Nam chose: production refuses the form (F2); "visible to the key" + open question (F6). This is version 2.

**Decision item 2 — add as a new paragraph:**

> **Nothing to convert.** When the affected site holds no records, `migration.json` may say `"nothing_to_convert": true` with `"data": []` instead of `keys`, the conversion and `rollback` (an explicit flag; empty data alone is still refused). `backup/` and `dry-run.md` stay required as for any migration. The folder's `site` must be a site of the release with a data-impacting change. It is not allowed for production: `pls package` and a plan for a `role: prod` environment refuse it, because its check runs only through `pls migrate` and `pls apply`. `pls migrate` sends nothing: it reads the site live and records the folder as migrated only when the operator's key sees 0 records there (the API lists only records the key may read — KB D36), otherwise it refuses. `pls apply` reads each such site again after the confirmation, right before the first configuration write, and refuses the whole release, writing nothing, if any record is visible by then; a record created after that read and before `updatesite` is not caught (Pleasanter has no conditional write). `--rollback` skips such a folder (it sent nothing) and rolls back the others.

**Decision item 3 — add:** "For a nothing-to-convert folder the conversion step is the live emptiness check, repeated by `apply`."

**Open questions — add:** "- [ ] Does an administrator / site-manager key see every record of a site through the items API `get` (record permissions, default view filters)? The nothing-to-convert check counts what the key sees — *kb-verify probe (TD-53)*"

**Status line:** add "Amended 2026-11-15 (nothing to convert)".
