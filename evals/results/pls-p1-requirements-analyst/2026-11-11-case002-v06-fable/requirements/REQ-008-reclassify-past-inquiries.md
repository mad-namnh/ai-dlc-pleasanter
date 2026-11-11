# REQ-008 — Past 契約・請求 inquiries are held under the new categories (depends on Q9)

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-category-accounting-worktime.md` (item 1: 「過去の問い合わせも、できれば新しいカテゴリで集計できるようにしたいです」)
- **Type (EARS):** unwanted behaviour

## Requirement

If an inquiry recorded before the change holds カテゴリ = 契約・請求 and the customer has classified it as 契約 or 請求, then the system shall hold that inquiry under the classified category.

## Acceptance criteria

1. After the migration, every inquiry named in the customer's classification holds カテゴリ = 契約 or 請求 exactly as classified (checked through the API against the classification list) `[assumed]` (Q9: the customer supplies the classification; nothing is guessed from the text).
2. No column other than カテゴリ changes on a migrated inquiry (compared with a backup of the affected records taken before the migration).
3. An inquiry the customer did not classify still holds 契約・請求 and can still be opened and found with the カテゴリ filter `[assumed]` (Q9).
4. The number of inquiries under 契約 + 請求 + (remaining) 契約・請求 after the migration equals the number under 契約・請求 before it.
5. Filtering the list by カテゴリ = 契約 or 請求 returns the migrated inquiries, including those in status 解決 and クローズ（対応不要） `[assumed]` (Q9: all past inquiries are in scope, whatever their status; Q10: counting by the existing filter / aggregation screens is enough).

## Notes

- The customer wrote 「できれば」: G1 decides whether this enters the scope for 12/10 (Q23).
- Which past inquiry is 契約 and which is 請求 cannot be derived from the configuration; it is a customer decision per record (Q9).
- For P2: data migration on `inquiries.ClassD`. KB: API updates did not create record versions (D14) → back up first; `bulkupsert` keyed on a unique business id (D13, D18). How an orphan value (契約・請求 after the choice is removed) behaves in filters and aggregations is verified only for the edit screen (D12) — probe before relying on criterion 3.
- The production / customer data is touched only by an authorised operator; the migration runs outside weekday business hours (constraint C-2 in `index.md`).
