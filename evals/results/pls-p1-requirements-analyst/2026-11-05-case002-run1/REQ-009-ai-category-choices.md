# REQ-009 — AI: 推定カテゴリ uses the new categories (derived)

- **Status:** awaiting G1
- **Source:** derived from REQ-007 impact analysis: the AI first response (existing feature, DES-000) estimates a category from a fixed list that contains 契約・請求 (column AI: 推定カテゴリ and the list of allowed answers / instruction text in the AI script). After REQ-007 it would keep proposing a category that is no longer offered in カテゴリ.
- **Type (EARS):** event-driven

## Requirement

When the AI first response is executed on an inquiry, the system shall set **AI: 推定カテゴリ** only to one of 操作方法, 不具合, 契約, 請求, 機能要望 or その他.

## Acceptance criteria

1. The choices of AI: 推定カテゴリ are 操作方法, 不具合, 契約, 請求, 機能要望, その他 (same list and order as カテゴリ, REQ-007).
2. On dev, saving a billing-related test inquiry with AIで一次対応する checked sets AI: 推定カテゴリ to 契約 or 請求, never 契約・請求.
3. Past values 契約・請求 in AI: 推定カテゴリ are left unchanged (`[assumed]`, Q12).
4. *(Not deterministically testable: the AI answer itself varies; criterion 2 is a sample test against the AI gateway on dev, and the "only allowed values are written" rule is tested with a stubbed answer.)*

## Notes (for P2)

- `ClassF` choices and `ai1` `CONF.outputs[category].allowed` + `instruction` enumerate the categories. `ai1` is generated from `spec.json` (header comment) — the change belongs in the generator input, not only in the script body.
- Depends on Q12 (customer may prefer to keep the AI list as is).
