# REQ-010 — 経理チーム can view 請求 inquiries

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-improvement-request.md` — item 2 (請求に関する問い合わせは経理チームでも状況を確認したい)
- **Type (EARS):** ubiquitous

## Requirement

The 問い合わせ site shall let members of the 経理チーム open and list inquiries whose カテゴリ is 請求.

## Acceptance criteria

1. A test user in the 経理チーム `[assumed]` (Q14) can list the 問い合わせ site, filter it by カテゴリ = 請求, and open each such inquiry on the edit screen (API `get` returns the records).
2. The 経理 user sees 状況, 対応担当, 対応期限 and the other columns of those inquiries as the support staff see them.
3. Scope of visibility: the 経理 user may also see inquiries of other categories `[assumed]` (Q13). If the customer requires 請求 only, this criterion becomes "an inquiry with カテゴリ ≠ 請求 is not returned to the 経理 user" — restricting visibility per record by category is **not covered by `pls-kb-pleasanter`** and must be verified by P2 before it can be promised.
4. Inquiries still holding 契約・請求 (not reclassified, REQ-008) are visible to 経理 under assumption Q13 (all inquiries); under a 請求-only restriction they would not be (impact of REQ-007/008 on this requirement).
5. Role test with a real 経理 test user — note that role tests are `deferred` in the project profile; G1 decides whether this requirement needs them.

## Notes for P2

- KB D19 (1.5.2): site permission value 1 (Read) lets a group read records and attachments, and makes create / update / delete / process execution / comments return 403. It also exposes the site settings through `getsite` (D5) — no secrets are in them today (`aiEnv` holds only the gateway URL).
- No `permissions.json` or `design/roles.json` exists in this project; current permissions are unknown (PO4). The 経理 group and its members are environment-specific principals (KB D15, L-PERM-01).
