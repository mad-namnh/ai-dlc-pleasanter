# DES-004 — 経理チーム: read-only access to 問い合わせ and 対応履歴

- **Status:** **not ready for G2** — draft (agent, 2026-11-11). Blocked by prerequisite G2-P1 (current permissions of `inquiries` are not in git) and by a derived requirement (DR-1) that needs G1. See *Open points*.
- **Requirements:** REQ-010, REQ-011, REQ-012 (G1 approved, Nam, 2026-11-05; Q13–Q15 accepted as assumed: 「経理」 group, all inquiries and 対応履歴 visible read-only, no comments, attachments may be opened/downloaded)
- **Change classification (ADR-0004):** **permission-impacting** — a new principal gets read access on `inquiries` and, through inheritance, on `responses`; the process `escalate` gets access control (DR-1). No record value changes.

## Ladder (I5)

Rung 1 (site permissions) and rung 2 (process access control on an existing プロセス). No script.

## Roles (step 1b)

| Role | Principal | Group name | Source |
|---|---|---|---|
| `accounting` | Group | 経理 | Q13 [assumed]: the customer prepares a 「経理」 group; rights per group |
| `support` | Group | 問い合わせ管理_サポート担当 (proposed; replace by the customer's group if one exists) | **DR-1 — pending G1.** Who may escalate today = "anyone with edit rights" (Q1 [assumed]) |
| `admin` | User | operator's own user (bound by `pls init`) | existing |

Groups are created by the person after G2; `pls principals --env dev` binds their ids by name. Configuration uses only `${principal:accounting}`, `${principal:support}`, `${principal:admin}`.

## Permission matrix (target)

Role × site × operation (R read, C create, U update, D delete, M manage site/permissions):

| Role | 問い合わせ (`inquiries`) | 対応履歴 (`responses`) | Comments | Attachments |
|---|---|---|---|---|
| existing entries (support staff, サポート責任者, admin) | **unchanged** (REQ-010 AC4) — exact entries unknown, G2-P1 | inherited from `inquiries` (unchanged) | as today | as today |
| `accounting` (経理) | R only | R only (inherited — `config/responses/permissions.json` has `inherit: ${site:inquiries}`, no own entries) | none (Q15) | open/download (Q15) — part of R, to confirm by probe PR-1 |

Role × process:

| Process | `support` | `admin` | `accounting` | others with update right |
|---|---|---|---|---|
| `escalate` (エスカレーション) | may press | may press | **may not press, button hidden** (REQ-012 AC4, AC5) | see DR-1 |

## Design

| # | Element | Setting (P3) | REQ | Rung |
|---|---|---|---|---|
| E1 | `inquiries` site permissions | `config/inquiries/permissions.json` (new in git — G2-P1): existing entries exactly as exported + `${principal:accounting}` with the **read-only** permission value (value from probe PR-1; `511` = all rights is the only value in the KB) | REQ-010, REQ-012 | 1 |
| E2 | `responses` site permissions | unchanged: keeps `inherit: ${site:inquiries}` → 経理 gets the same read-only right on 対応履歴 | REQ-011, REQ-012 | 1 |
| E3 | Process `escalate` access control (D20) | `Processes[escalate]` `Groups` = `${principal:support}`, `Users` = `${principal:admin}`; display condition unchanged (ClassE 高, Status 100/200/300) | REQ-012 AC4, AC5 (+ DR-1) | 2 |

### Why E3 (branch that is safe if the expectation is wrong)

The design must not rely on a read-only permission to hide the エスカレーション button: the framework's known behaviour is that a restricted role still sees process buttons and gets an error when pressing them (D19, cited by the P2 skill; **not** written in `pls-kb-pleasanter` `behaviours.md`). Process access control (D20) is the safe branch: the button is limited to the roles that may escalate, whatever the read-only value does.

Integrity does not depend on E3: a user without update right cannot change the record through the API either way (REQ-012 AC1–AC4), to be confirmed by PR-1. E3 serves REQ-012 AC5 (no button on screen).

E3 changes who may escalate among the **existing** users unless the `support` group holds everyone who has edit rights today. That is a new impact on REQ-001/Q1 → **derived requirement DR-1, raised to P1/G1, not absorbed here**:

> **DR-1 (proposed REQ-016):** The エスカレーション button of 問い合わせ管理 shall be shown to, and executable by, only the members of the support group and admin; members of the 経理チーム shall not see it.

If G1 rejects DR-1, the alternative is E3 = not added and REQ-012 AC5 downgraded to "the button may show; pressing it is refused" — that also needs G1 (it changes an approved criterion).

## Probes (dev only, written down — not run in this dry run)

| # | Probe | Contains (the combination the design relies on) | Expected | Changes the design? |
|---|---|---|---|---|
| PR-1 | Read-only value and refusals | dev probe copy of `inquiries` with the `escalate` process (same display condition) and E3 access control; child copy of `responses` inheriting from it with a linked record; test user in a probe 経理 group with the candidate read-only value; record inside the display condition | `get` OK on both sites; `create`/`update`/`delete` refused on both (record the HTTP status for the KB, REQ-012 note); `ProcessId` execution refused, record unchanged; edit screen without save/delete/エスカレーション; attachment downloadable; comment not possible | Value only, if as expected. If attachments need another bit, or comments are allowed with the value → back to G1 for Q15 |
| PR-2 | Process access control | same probe site; a second user with update right **not** in the access-control list | button hidden for that user and API execution refused | Yes — if access control does not hide the button, REQ-012 AC5 cannot be met with settings → G1 decision. Integrity unaffected (permission) |
| PR-3 | Inheritance | `responses` copy with `inherit` from the `inquiries` copy | 経理 rights on `responses` = rights on `inquiries` | Yes — if not inherited, E2 becomes an own `permissions.json` on `responses` |

PR-2 and PR-3 can change the design: they are **G2 prerequisites**. They cannot run in this dry run, so the design takes the safe branch (E3) and presents them as confirmations — they must run on dev before G2 if an environment is available. Results go into `pls-kb-pleasanter` (D19/D20 entries are missing there).

## Rejected alternatives

- **Rely on read-only permission to hide the button** — D19 (a restricted role still sees process buttons).
- **Grant 経理 on the parent folder** — would give 経理 access to every site under it.
- **Record-level restriction to カテゴリ 請求** — Q14 [assumed] all visible; record-level permission is not in the KB and would need probes that endanger C1.
- **`NoDisplayIfReadOnly`** to hide things from read-only users — behaviour not in the KB; does not address the process button.
- **Server script refusing updates by 経理** — rung 3 not needed; permissions refuse writes.

## Impact analysis

| Existing element | Impact | Action |
|---|---|---|
| `inquiries` permissions (not in git) | must keep the existing entries identical (REQ-010 AC4); if `inquiries` inherits from its folder today, adding an own entry breaks the inheritance — later folder changes stop reaching it | **G2-P1**: export the permissions of `inquiries` from dev and stg (read-only), unpack to `config/inquiries/permissions.json`, then finish E1 |
| `responses` permissions (`inherit: ${site:inquiries}`) | 経理 gets read on 対応履歴 automatically (REQ-011) | none; PR-3 confirms |
| Process `escalate` | 経理 would see the button (D19); access control changes who may press it | E3 + DR-1 to G1 |
| Process `escalate` notification, Notification #1 (`[Manager]`), Reminder 1 (`[Owner]`) | recipients unchanged; 経理 receives nothing | none |
| AI script `ai1` | runs only on save; a read-only user cannot save | none |
| Views, aggregation, grid | 経理 sees all inquiries (Q14); filter on カテゴリ 請求 serves REQ-010 AC2 (needs DES-003 E1) | none |
| Export | not granted by the read-only value (Q15 does not ask for it) | open point to the customer if 経理 needs export |
| Principals per environment | `accounting`, `support` must exist in dev and stg before P3 (`pls principals`) | after G2, by the person |

## P4 tests to plan (TD-11)

With a 経理 test user on dev: REQ-010 AC1–AC3, REQ-011 AC1–AC3, REQ-012 AC1–AC4 (API), AC5 and AC6 on screen; with a support test user: エスカレーション still works (REQ-001/REQ-002 regression); with a non-listed editor: button hidden (DR-1).

## Open points

- **G2-P1** (prerequisite, read-only export by the person): current permissions of `inquiries` on dev and stg. `requirements/index.md` speaks of "`permissions.json`: inherit + admin" but no `config/inquiries/permissions.json` exists in this project.
- **DR-1** to G1 (project owner), with customer question Q24 below.
- PR-1…PR-3 on dev; KB additions D19/D20 and the refusal status.
- Customer questions Q13–Q15 stay open; new question Q24 (日本語):
  - Q24: 経理チームの方には「エスカレーション」ボタンを表示しないようにするため、ボタンを押せる人をグループで指定します。エスカレーションを行うサポート担当の方が所属するグループはありますか？ ない場合、「サポート担当」グループを作成してよいですか？
