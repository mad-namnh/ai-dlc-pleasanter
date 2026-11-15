# Review — access lists mapped

## Round 1 (pls-x-reviewer, opus, high) — accept with fixes; Low only

- **L1:** pls_scope docstring said principals are not mapped → updated (mapped; only round-trip evidence missing).
- **L2:** P3 config-layout, P2 checklist, KB schema name process access control only → TD-58 (skill text needs an eval; KB through the curator).
- **L3:** `Users: -1` (every authenticated user, ColumnAccessControl.cs l.144, source-derived) was called an environment-specific id → kept as a fixed value in unpack, payload, lint and the adopt summary; test.
- **L4:** pack refusal / lint gave no remedy → messages name it (write `${principal:<name>}`; unpack / harvest after mapping).
- **Note:** `View` objects nested in processes / status controls / dashboard parts / links record `Depts/Groups/Users` — not mapped; whether the UI sets them is unknown → TD-58, with WS1.6.
