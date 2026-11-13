# Plan — TD-23: site id under a JSON-escaped or backtick-quoted key

- **Date / branch:** 2026-11-13 / `brownfield-adr`; parent `6b7693b`
- **Task (Nam, 2026-11-13):** "làm tiếp TD-23" — `docs/tech-debt.md` TD-23 (review of the quoted-value fix, `plans/2026-11-11-pls-quoted-site-id/review.md` F2).
- **Tier:** Critical (environment references: a missed id makes a pack for another environment send this environment's raw id, D3). Review `pls-x-reviewer`, `opus`, high.
- **Change:** in `pls_scripts.ID_CONTEXT`, the quoted-key alternative (`"siteId": …`) also accepts a backslash before each quote (JSON escaped inside a JS string: `'{\"siteId\": \"797\"}'`) and a backtick as the quote (`` `siteId`: 797 ``, `` "siteId": `797` ``). Nothing else changes; the browser runner has no copy of the rule. **Widened after review round 1 (F1; Nam 2026-11-13: "Mở rộng luôn trong TD-23"):** a bracketed name (`p["SiteId"] = 797`, `p['site_id'] === 797`, `797 === p["siteId"]`, `{["siteId"]: 797}`, `` [`siteId`]: 797 ``) and a backtick or escaped value under an unquoted name (`` siteId: `797` ``, `siteId: \"797\"`); JSON escaped twice → TD-42.

## Acceptance criteria
1. `replace_ids` turns `{\"siteId\": \"<id>\"}`, `{\"SiteId\":<id>}`, `{\'siteId\': \'<id>\'}`, `` `siteId`: <id> ``, `` "siteId": `<id>` `` into `${site:x}` and keeps the quotes and backslashes.
2. Look-alikes stay unchanged: `{\"siteIdx\": \"<id>\"}`, `{\"website_id\": \"<id>\"}`, `{\"status\": \"<id>\"}`, `{\"siteId\": \"<id>px\"}`, `` `siteIdx`: <id> ``; all earlier tests still pass.
3. `unstable_refs` does not report `{\"siteId\": \"${site:x}\"}` (L-REF-03); `literal_left` reports `{\"siteId\": \"<id>\"}` (L-REF-01).
4. End to end: unpack of a script with an escaped JSON string writes `${site:anken}`; no L-REF-03; the prod payload carries prod's id.
5. New tests fail on the parent; suites green (3.12, 3.10, node).
6. Docs: TD-23 closed in `docs/tech-debt.md`; `HANDOFF.md`.
7. (round 1 F1) the bracket / backtick / escaped-value forms above become `${site:x}`; look-alikes stay: `p["siteIdx"] = <id>`, `p["website_id"]`, `p["status"]`, `<id> === p["siteIdx"]`, `` siteIdx: `<id>` ``, `` siteId: `<id>px` ``, `p["siteId"] + <id>`, `[p["siteId"], <id>]`; TD-42 for JSON escaped twice; D3 row in `docs/review-findings.md`.
