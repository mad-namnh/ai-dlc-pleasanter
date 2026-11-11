# REQ-009 — AI 推定カテゴリ follows the new categories (derived)

- **Status:** awaiting G1
- **Source:** derived from REQ-007 impact analysis: the AI first response (server script 「AI問い合わせ一次対応」) and the column AI: 推定カテゴリ both enumerate the old category list (操作方法/不具合/契約・請求/機能要望/その他). Without a change, the AI keeps proposing 契約・請求, which is no longer a カテゴリ choice.
- **Type (EARS):** event-driven

## Requirement

When the AI first response runs on an inquiry, the system shall set AI: 推定カテゴリ only to one of the カテゴリ choices 操作方法, 不具合, 契約, 請求, 機能要望 or その他.

## Acceptance criteria

1. AI: 推定カテゴリ offers the same choices, in the same order, as カテゴリ (REQ-007).
2. After saving an inquiry with 「AIで一次対応する」 on, AI: 推定カテゴリ is empty or one of the six choices; it is never 契約・請求.
3. A billing inquiry used as test input (e.g. 請求書の金額に関する問い合わせ) gets 請求; a contract inquiry (e.g. 解約の手続き) gets 契約. *(Not fully deterministic: the AI answer can vary — run as a smoke test, not as a pass/fail gate; criteria from Q9.)*
4. 「AIで一次対応する」 still turns itself off after the run, and 推奨優先度 / 回答の下書き are still written (existing behaviour unchanged).

## Notes

- For P2: `ai1.js` `CONF.outputs[category]` (instruction text and `allowed` list) and `Columns[ClassF].ChoicesText`. The script header says it is generated from `spec.json` and overwritten on re-registration — P2 must change the source, not only the file.
- Past values of AI: 推定カテゴリ = 契約・請求 — Q12 `[assumed]` kept as they are.
