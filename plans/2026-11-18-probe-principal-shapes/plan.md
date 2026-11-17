# Probe files name no principal in other shapes (TD-70)

Tier: Critical (kb-verify write guard on dev, ADR-0027 item 3). Nam 2026-11-18: "làm lần lượt TD-63, rồi TD-70, rồi TD-67".

- `pls_kbverify.literal_principals` also finds: a scalar `Users` / `Groups` / `Depts` that is not a variable; a permission entry as a whole text value (`User,5,511`); an id in `ColumnFilterHash` (object or JSON text) on Owner / Manager / Creator / Updator or on a column whose choices are `[[Users…]]` / `[[Groups…]]` / `[[Depts…]]`; all of these inside JSON text.
- Only tightens a refusal; every probe file in the KB still passes (suite).
- Tests: each shape refused in site settings, a settings step, a teardown; status filter, plain column filter, a scalar variable and a label with a comma still pass.
- Docs: ADR-0027 As built, TD-70 closed.
