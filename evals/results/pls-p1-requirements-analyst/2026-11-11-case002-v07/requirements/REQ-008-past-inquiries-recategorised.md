# REQ-008 — Past 契約・請求 inquiries carry the new categories

- **Status:** awaiting G1 — the customer wrote 「できれば」: G1 decides whether this enters the scope and whether it may follow REQ-007 later (Q11)
- **Source:** `sources/2026-11-11-improvement-request.md` — item 1 (過去の問い合わせも、できれば新しいカテゴリで集計できるようにしたい)
- **Type (EARS):** ubiquitous

## Requirement

The 問い合わせ site shall hold カテゴリ 契約 or 請求, instead of 契約・請求, on every inquiry that was classified 契約・請求 before the change.

## Acceptance criteria

1. After the migration, filtering the list on カテゴリ = 契約・請求 returns 0 inquiries.
2. Each migrated inquiry holds the カテゴリ given for it in the classification list agreed with the customer (Q10 `[assumed]`): checked record by record against that list through the API.
3. No other column of a migrated inquiry changes (compare with the backup taken before the migration).
4. Filtering on カテゴリ = 契約 and = 請求 returns the past and the new inquiries together (aggregation by the new categories covers past data).
5. *(Not automatically testable: whether the classification itself is correct is a business judgement — the customer confirms the list, Q10.)*

## Notes

- Who decides 契約 vs 請求 for each past record, and how many records there are, is unknown — Q10. The configuration in `config/` holds no record data, so the number of affected inquiries is not known here.
- KB D12: if the choice is removed before the values are migrated, 契約・請求 stays on those records as an orphan option. KB D14: API updates create no versions — back up first. Data-impacting change: P2 must plan a migration.
- 「集計」: the site has no aggregation by カテゴリ today (aggregation is by 状況; crosstab view 3 is 状況×チャネル). How the customer aggregates today is not stated; this requirement covers the data, not a new aggregation view — see Q20 for the monthly report.
