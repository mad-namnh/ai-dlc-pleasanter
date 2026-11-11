# REQ-012 — 各部門の担当者 change nothing

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contract-management.md` — A6
- **Type (EARS):** unwanted behaviour

## Requirement

If a 各部門の担当者 attempts to create, change or delete a contract, then the system shall refuse the operation.

## Acceptance criteria

1. As 各部門の担当者, creating a contract is refused and no contract is created.
2. As 各部門の担当者, changing any item of a contract of the own 担当部門 is refused and the stored values are kept.
3. As 各部門の担当者, moving a contract of the own 担当部門 to another state is refused.
4. As 各部門の担当者, deleting a contract is refused.

## Notes

- A6: "chỉ xem hợp đồng của 担当部門 mình, không sửa gì". Deleting is read as part of "không sửa gì".
- KB D19 (1.5.2): a read-only right refuses create, update, delete and actions.
