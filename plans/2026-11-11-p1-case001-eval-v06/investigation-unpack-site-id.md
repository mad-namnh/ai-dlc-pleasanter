# Investigation — `pls unpack` left `"siteId": "44574"` literal in `ai1.js`

Found by the P1 case 002 run of 2026-11-11 (agent question PO3). Investigation only; nothing changed in `tools/pls`.

## Facts (each checked)

1. `pls-demo-inquiry/releases/R-20261105-05/rollback-inquiries.json` (stg) holds `ai1` CONF `"related": {"siteId": "44574", …}`; 44574 is stg 対応履歴 in `environments.json`. `R-20261105-01/rollback.json` holds `"44566"` (the dev id, on stg — the D3 spike finding).
2. `pls unpack` maps script numbers through `pls_scripts.replace_ids` (`pls.py` `logical()` → `to_refs` → `SX.replace_ids`). Since `5ae8391` (2026-11-08, "site ids are replaced only where they are written as site ids") a number is replaced only in an `ID_CONTEXT` (`pls_scripts.py:119`) or a recorded reference (`design/refs-literal.json`).
3. Direct check of `replace_ids` with `{"44574": "responses"}`:
   - `"siteId": "44574"` → unchanged
   - `"siteId": 44574` → `${site:responses}`
   - `siteId: "44574"` → `"${site:responses}"`
   - `siteId = "44574"` → `"${site:responses}"`
   The second alternative of `ID_CONTEXT` (`%(name)s["']\s*[:,]\s*`, a quoted key) allows no opening quote before the number; the first alternative (unquoted key) does (`["']?`). A JSON-style quoted key with a quoted value — the form `ai1` uses — is therefore not seen as a site id.
4. The real project is affected: `pls lint` on a clean copy of `pls-demo-inquiry` HEAD (`../_agent-scratch/demo-inquiry-lint-copy/`, `git archive`, no `.pls/`) reports `L-REF-03 inquiries ServerScripts/ai1: ${site:responses} outside a site-id context becomes a plain number on the next unpack`. The project has no `design/refs-literal.json`.
5. Consequence: the next unpack of any export of `inquiries` writes the environment's number into git; a pack for another environment then sends that number unchanged, and the AI script reads 対応履歴 of the wrong environment — the D3 failure the reference exists to prevent. `pls lint` warns (L-REF-03, L-REF-01 does not fire because the number is not in an id context either).
6. The eval cases are affected only through their input: case 001 `input.md` already says `${site:responses}` must be restored by hand; case 002 `input.md` does not.

## Options (Nam decides)

- **A (recommended): widen `ID_CONTEXT` alternative 2 to accept an opening quote** (`%(name)s["']\s*[:,]\s*["']?`), same as alternative 1. Tests: the four forms above for unpack, L-REF-03 no longer firing for the git form, the PLAY BOARD negatives still unchanged. Tier Critical (environment references, D3): independent review. Also add one line to case 002 `input.md` only if A is not taken.
- **B: record a reference decision in `pls-demo-inquiry`** (`pls refs --ref`, `design/refs-literal.json`). Fixes the demo only; any other app with the same CONF form stays exposed.
- **C: leave as is**; lint L-REF-03 already warns. The case 002 input gets "restore `${site:responses}` by hand" as case 001 has.

## Open question

- Whether other common forms are missed (e.g. `"siteId": '44574'`, `SiteId": "44574"` inside a template literal) — to cover in the tests of option A.
