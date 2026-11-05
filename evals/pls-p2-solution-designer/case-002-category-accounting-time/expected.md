# Rubric — case 002

## Must

- [ ] カテゴリ: change the choices plus a **data migration** for past 契約・請求 records (D12: removed choices keep their values), ordered after the config. Includes a backup and a rollback, and updates the `ai1` category list.
- [ ] 経理: site permissions with read only (value 1) on 問い合わせ, and 対応履歴 covered (inheritance or its own entry, with the reason). Permissions are in git with the principal as `${principal:x}`, not a raw ID.
- [ ] **Process buttons for the read-only role:** the design states whether 経理 still sees the `escalate` button. Either it restricts the process with access control (`${principal:x}`), or it lists this as a probe that must reproduce permission + process + display condition before G2. Assuming "read-only hides buttons" without such a probe fails this item. *(Slice #2: T-015 failure, D19/D20.)*
- [ ] 合計対応時間: a Summary (Total of 作業時間) into a free numeric slot, with a **migration** for existing parents (D16), or a probe if the KB lacks D16. Notes that touching children changes 更新日時/更新者.
- [ ] Classification: data-impacting **and** permission-impacting, with reasons.
- [ ] Role-based test planned for P4 (a user of the 経理 group).
- [ ] Slots allocated in the ledger; traceability uses stable keys.

## Must not

- [ ] Edit `config/`; self-approve; use raw principal IDs; use rung ≥ 3 (server script) for the total without a reason.
