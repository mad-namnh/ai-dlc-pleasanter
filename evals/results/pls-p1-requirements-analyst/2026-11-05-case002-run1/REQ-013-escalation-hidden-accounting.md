# REQ-013 — エスカレーション is not offered to 経理チーム (derived)

- **Status:** awaiting G1
- **Source:** derived from REQ-010/REQ-012 impact analysis: Pleasanter still shows process buttons whose display condition matches to read-only users (KB D19). A 経理 member opening a 優先度 高 inquiry in 受付/対応中/顧客回答待ち would see エスカレーション (REQ-001/REQ-002), press it and get an error — contradicting 「見るだけ」.
- **Type (EARS):** unwanted behaviour

## Requirement

If the user viewing an inquiry is a member of the 経理チーム, then the system shall not offer the **エスカレーション** action.

## Acceptance criteria

1. 経理 test user opens an inquiry with 優先度 高 and 状況 対応中 → no エスカレーション button.
2. A support user (edit rights) opens the same inquiry → the エスカレーション button is shown and works as in REQ-001 (REQ-002 unchanged for support users).
3. API execution of the escalation by the 経理 test user → refused (HTTP 403, KB D20); 状況 and エスカレーション日時 unchanged.

## Notes (for P2)

- Hiding a button needs process access control (`Groups`/`Users`/`Depts`, KB D20), which lists who **may** execute it. That changes the approved Q1 assumption ("anyone with edit rights") into an explicit list of support principals — Q14, EP-4. DES-001 open point Q1 already anticipated access control.
