# Review — TD-62, TD-70

## Round 1 (pls-x-reviewer, opus, high) — accept with fixes; no Critical / High
- F1 Medium: mark-applied checked the whole raw export (ApiKey would block a release for good) → checks what it writes (Title, Body, ReferenceType, SiteSettings, permissions); test with ApiKey only.
- F2 Medium: teardowns not checked → a teardown holds no Users / Groups / Depts list; test.
- F3 Medium: diff / drift / plan printed live values → md_diff shows `(withheld: <names>)` for a secret-like value (credential fields read under their key); test.
- F4 Medium: adopt checked SiteSettings only → Title and Body too; test.
- F5 Low: legacy single-site mark-applied printed values → covered by md_diff.
- F6 Low: other principal shapes → TD-70 kept partly open; ADR-0027 says lists only.
- F7 Low: settings steps in cleanup → refused; test.
- F8 Low (optional): env-compare checks the mapped model, not the raw export → not changed (the report leaks nothing; the mapped value reads ${env:x}).

## Round 2 (same reviewer) — accept with fixes; no Critical / High
- N1 Medium: mail recipients withheld in diff tables (the G4 summary needs them) → Token / Headers always withheld; Address / To only when a value holds a URL (`://`) or a secret pattern; test.
- L1 Low: principal lists inside JSON text → added to TD-70's open shapes.
- L2 Low: masking tested through md_diff, not an end-to-end drift run → accepted (every caller goes through md_diff).
