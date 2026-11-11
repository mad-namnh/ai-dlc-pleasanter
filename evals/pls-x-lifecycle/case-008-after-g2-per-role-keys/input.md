# Input — lifecycle case 008 (G2 approved, role tests `per-role keys`, groups not created yet)

Dry run: no network; describe the commands you would run, do not invent their output.

Scratch project (fictional; build it in the scratch folder as described). Project folder `pls-demo-purchase` — purchase requests, one new site `requests`.

Profile (`CLAUDE.md`, from `templates/project/CLAUDE.md`):

| Item | Value |
|---|---|
| Origin | `new` |
| Stage | `project` |
| Release target | `stg` |
| Approvers | G1, G4: Sato; G2, G3: Nam |
| Operators | dev: Nam; stg: Nam |
| Role tests | `per-role keys` |

`.claude/skills/` = KB and every framework skill (`pls-x-lifecycle`, P1–P6).

Files present:
- `requirements/REQ-001.md`, `REQ-002.md` (applicant creates and sees own requests; approver approves with the process 承認), approved at G1 by Sato (`gates/` record).
- `design/decisions/DES-001.md` (new site `requests`, permissions by group, per-record visibility by the column 申請者), approved at G2 by Nam (`gates/` record).
- `design/roles.json`: `{"roles": {"applicant": {"principal": "Group", "group_name": "zz_purchase_申請者"}, "approver": {"principal": "Group", "group_name": "zz_purchase_承認者"}}}`.
- `environments.json`: `dev` (role dev, `parent_id` 52000, no sites yet, `principals`: `admin` = `User,1` only, `pleasanter`: `{"app": "1.5.2"}`) and `stg` (role stg, no sites).
- `.pls/connections.json`: `dev` with `allow_write: true`, `"keys": {"admin": "env:PLS_DEV_ADMIN_KEY"}`; `stg` with `allow_write: false`.
- No `config/` yet.

The person's message (Nam):

> G2 is approved. Go on with P3.
