# REQ-008 — Past 契約・請求 inquiries are counted under 契約 or 請求

- **Status:** awaiting G1 (customer wrote 「できれば」 — G1 decides whether it is in scope for 12/10; see Q10, Q25)
- **Source:** `sources/2026-11-11-improvement-request.md` — item 1 (過去の問い合わせも、できれば新しいカテゴリで集計できるようにしたい)
- **Type (EARS):** ubiquitous

## Requirement

The 問い合わせ site shall hold カテゴリ 契約 or 請求, as decided by the customer, for every inquiry that held 契約・請求 before REQ-007.

## Acceptance criteria

1. After the reclassification, no inquiry listed in the customer's reclassification list `[assumed]` (Q10) holds カテゴリ = 契約・請求; each holds the value the list gives it.
2. The number of inquiries with 契約 plus the number with 請求 among the reclassified ones equals the number that held 契約・請求 before (checked against a backup taken before the change).
3. No other column of a reclassified inquiry changes (compare with the backup).
4. Filtering the list by カテゴリ = 契約 or = 請求 returns the reclassified past inquiries together with new ones.
5. *(Not automatically testable: whether each past inquiry was put in the right category is a business judgement; the customer checks it — Q10.)*

## Notes for P2

- Which past inquiry is 契約 and which is 請求 cannot be derived from the configuration; someone must decide per record (Q10). The number of affected records is unknown (no data export in this repository).
- Data migration on live data: back up first (KB D14: API updates did not create versions), key on 問い合わせ番号 and check uniqueness (KB D18). Classify as data-impacting.
- Inquiries not reclassified keep 契約・請求 (REQ-007 AC 4); they are counted under neither new category.
