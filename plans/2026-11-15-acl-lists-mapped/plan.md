# Plan — principal ids in every access list (settings coverage WS1.1 + 6a)

- **Tier:** Critical (environment mapping, L-PERM-01, pack refusal).
- **Source:** plans/2026-11-15-settings-coverage/ inventory A (12 keys with unmapped ids), plan WS1.1 / 6a. Order approved by Nam.
- **Change:** acl_to_refs / acl_from_refs / L-PERM-01 / adopt summary iterate one fixed table ACL_LISTS (Processes, Views, Exports, DashboardParts, StatusControls, Create/Read/UpdateColumnAccessControls) instead of Processes only. pls_scope keeps refusing a status control with principals (no round-trip evidence), message updated. ADR-0006 Consequences as-built note (Decision unchanged: it is about site permissions; process ACL mapping came from D20); architecture L-PERM-01 row.
- **Not in this task:** RecordUsers (WS1.2), site-id lists (WS1.3), dashboard site strings (WS1.4), mail defaults exclusion (WS1.5), ids in view filters (WS1.6).
- **Acceptance:** (1) unpack maps each list to ${principal:x}; (2) payload resolves per environment and checks the principal type; (3) a raw id → L-PERM-01 and pack refusal naming the item; (4) process behaviour unchanged (existing tests); (5) new test fails on the parent; (6) suites green incl. 3.10; (7) review no open Critical/High.
