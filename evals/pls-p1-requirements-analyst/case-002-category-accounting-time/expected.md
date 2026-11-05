# Rubric — case 002

## Must

- [ ] Source saved verbatim.
- [ ] Category split as a requirement, with acceptance criteria saying that 契約・請求 is no longer offered.
- [ ] Past 契約・請求 records are addressed. Either a requirement or a question with an `[assumed]` default; "leave as is" is acceptable only as a question.
- [ ] Derived item for the AI 推定カテゴリ list in `ai1` (protects existing behaviour).
- [ ] 経理 read access to 問い合わせ **and** 対応履歴, plus an unwanted-behaviour requirement that 経理 cannot change records.
- [ ] **Detects that 作業時間 already exists** on 対応履歴. The requirement uses it, or the overlap is a question with an `[assumed]` default. It does not silently ask for a new column. *(Slice #2: found only at the P2 prerequisite step.)*
- [ ] Total per inquiry as a requirement. A derived item or acceptance criterion says the existing 対応回数 keeps working.
- [ ] Questions in Japanese with `[assumed]` defaults, covering at least:
  - the mapping of past 契約・請求 records;
  - whether 経理 sees all inquiries or only 請求;
  - the unit of 対応時間;
  - who belongs to 経理チーム (the group).
- [ ] Exactly one `shall` per REQ; index with status awaiting G1.

## Must not

- [ ] Name mechanisms (Summary, permission value, ClassX/NumX slots, プロセス) in requirement statements.
- [ ] Mark anything approved.
- [ ] Add scope nobody asked for (e.g. a monthly report view) as a requirement instead of a question.
