# REQ-009 — AI: 推定カテゴリ follows the category split (derived)

- **Status:** awaiting G1
- **Source:** derived from REQ-007 impact analysis: 「AI: 推定カテゴリ」 and the AI first-response script enumerate the same category list as カテゴリ (including 契約・請求); after the split the AI would keep proposing a category that カテゴリ no longer offers
- **Type (EARS):** ubiquitous

## Requirement

The 問い合わせ site shall offer for AI: 推定カテゴリ the same choices as カテゴリ.

## Acceptance criteria

1. The edit screen and the list filter of AI: 推定カテゴリ show the same choices, in the same order, as カテゴリ after REQ-007 `[assumed]` (Q11).
2. After 「AIで一次対応する」 runs on an inquiry about a contract or about an invoice, AI: 推定カテゴリ holds one of the current カテゴリ choices and never 契約・請求. *(Not automatically testable in a deterministic way: the value comes from an external AI service; verified by a person on dev with one contract example and one invoice example — see Q11.)*
3. AI: 推定カテゴリ values already stored on past inquiries are not changed `[assumed]` (Q11).

## Notes

- For P2: `ClassF` choices and the category list inside server script `ai1` (output instruction and allowed list). An AI answer outside the allowed list is silently dropped by the script today, so a list that is not updated would make the AI category stay empty or stale rather than fail.
- Precedent: for 優先度 緊急 the same kind of impact was left unchanged at G1 (Q6). Here the old value disappears from カテゴリ, so leaving the AI list unchanged would break the existing behaviour; G1 may still decide otherwise (Q11).
