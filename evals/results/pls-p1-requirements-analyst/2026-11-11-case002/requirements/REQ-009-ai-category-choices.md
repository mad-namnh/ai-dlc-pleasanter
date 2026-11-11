# REQ-009 — AI: 推定カテゴリ proposes only categories that カテゴリ offers (derived)

- **Status:** awaiting G1
- **Source:** derived from REQ-007 impact analysis: the existing AI first response (server script `ai1`, column AI: 推定カテゴリ) estimates a category from a fixed list that equals today's カテゴリ choices. After REQ-007 it would keep proposing 契約・請求, which カテゴリ no longer offers. Confirmation asked in Q12.
- **Type (EARS):** event-driven

## Requirement

When the AI first response runs on an inquiry, the system shall set AI: 推定カテゴリ only to one of the choices that カテゴリ offers.

## Acceptance criteria

1. AI: 推定カテゴリ offers 操作方法, 不具合, 契約, 請求, 機能要望, その他 (same list and order as カテゴリ, REQ-007).
2. The list of categories the AI may return is the same list; a returned value outside it is not written (existing behaviour of the script, kept).
3. AI: 推定カテゴリ values stored on past inquiries are not changed `[assumed]` (Q12).
4. *(Not automatically testable: which category the AI chooses for a given text depends on the external AI service; a test can only check that the written value is in the list.)*

## Notes for P2

- Elements: `Columns[ClassF].ChoicesText`; `ai1.js` CONF `outputs[category].allowed` and its `instruction` text (lists 契約・請求).
- `ai1.js` in `config/` holds a literal site id `"44574"` for the related 対応履歴 site, while DES-000 says it uses `${site:responses}` (KB D3). Not part of this request; raised to the project owner (PO3).
