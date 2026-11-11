# Plan — `pls unpack` sees a quoted site id under a quoted key

- **Task (Nam, 2026-11-11):** option A of `plans/2026-11-11-p1-case001-eval-v06/investigation-unpack-site-id.md` ("1.A").
- **Tier:** Critical (environment references; a wrong id makes a script read another environment's data, D3). Independent review required.
- **Change:** `ID_CONTEXT` alternative for a quoted key (`"SiteId": 797`) also accepts an opening quote before the number (`"siteId": "797"`), as the unquoted-key alternative already does.

## Acceptance criteria
1. `replace_ids` turns `"siteId": "<id>"`, `'siteId': '<id>'`, `"SiteId":"<id>"`, `"NOTIFICATION_SITE_ID", "<id>"` into `${site:x}` and keeps the quotes.
2. Look-alikes stay unchanged: `"siteIdx": "<id>"`, `"website_id": "<id>"`, `"status": "<id>"`, `"siteId": "<id>px"`; all earlier negatives in `test_scripts.py` still pass.
3. `unstable_refs` no longer reports `"siteId": "${site:x}"` (lint L-REF-03); `literal_left` reports `"siteId": "<id>"` (lint L-REF-01).
4. End to end: unpack of a script with `{"related": {"siteId": "797"}}` writes `${site:anken}`; lint has no L-REF-03; the prod payload carries prod's id.
5. New tests fail on the parent commit; both suites green on 3.12; Python suite on 3.10.
