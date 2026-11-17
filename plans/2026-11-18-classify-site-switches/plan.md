# Classify six site switches (TD-63)

Tier: Critical (classification, `VERIFIED_KEYS`). Nam 2026-11-18: "làm lần lượt TD-63, rồi TD-70, rồi TD-67"; classes: "3 perm + 3 config (Recommended)".

- `classify`: CL-SERVER-SCRIPTS-OFF, CL-MIGRATION-MODE, CL-PHYSICAL-DELETE-HISTORIES → permission-impacting; CL-CLIENT-CODE-OFF (`ScriptsAllDisabled`, `HtmlsAllDisabled`), CL-EXTENDED-HEADER → config-only with a message (a script or event handler in the header is named).
- Effect read from the Pleasanter_1.5.2.0 source (2026-11-18): `ServerScriptUtilities.cs` (server scripts return early), `IssueModel.SetByApi` / `*Utilities` import (MigrationMode sets Creator, Updator, CreatedTime, UpdatedTime; no manage-site check on the API path; the import checkbox needs manage-site), `*Validators.cs` (physical history delete needs History.PhysicalDelete and the switch not false), `HtmlScripts.cs`, `HtmlTemplates.cs` (client scripts / HTML parts / ExtendedHeader written raw).
- `pls_scope.VERIFIED_KEYS` gains the six keys; impact rules + generated `impact-rules.md`; ADR-0004 As built; architecture §7.1 row; TD-63 closed.
- Tests: classify per key both directions, script note in ExtendedHeader, mixed release; scope test; impact rule samples.
