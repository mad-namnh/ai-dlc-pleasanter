# Input — P4 case 002 (role tests `per-role keys`, no role key on dev yet)

Dry run: no network; describe the commands you would run, do not invent their output.

Scratch project (fictional; build it in the scratch folder as described). Project folder `pls-demo-purchase` — purchase requests, one site `requests`.

Profile (`CLAUDE.md`, from `templates/project/CLAUDE.md`):

| Item | Value |
|---|---|
| Origin | `new` |
| Stage | `project` |
| Release target | `stg` |
| Approvers | G1, G4: Sato; G2, G3: Nam |
| Operators | dev: Nam; stg: Nam |
| Role tests | `per-role keys` |

`.claude/skills/` = KB, `pls-x-lifecycle`, `pls-p4-test-writer`.

Files present:
- `requirements/REQ-001.md` — 申請者 (applicant) creates a purchase request and sees only their own requests. Acceptance: an applicant can create a request; an applicant cannot read another applicant's request; an applicant cannot approve.
- `requirements/REQ-002.md` — 承認者 (approver) approves or rejects a request with the process 承認. Acceptance: an approver can approve a request in status 申請中; an approver cannot edit the amount after approval.
- `design/decisions/DES-001.md` — permissions: group 申請者 read/create own records (per-record visibility by the column 申請者), group 承認者 read all and the process 承認; `config/requests/` built accordingly (P3 done, round trip 0 on dev).
- `design/roles.json`: `{"roles": {"applicant": {"principal": "Group", "group_name": "zz_purchase_申請者"}, "approver": {"principal": "Group", "group_name": "zz_purchase_承認者"}}}`.
- `environments.json`: `dev` (role dev, site `requests` id 52010, `principals`: `admin` = `User,1`, `applicant` = `Group,401`, `approver` = `Group,402`, `pleasanter`: `{"app": "1.5.2"}`).
- `.pls/connections.json`: `dev` with `allow_write: true` and **one key only**, `"keys": {"admin": "env:PLS_DEV_ADMIN_KEY"}`.
- `traceability.json` with REQ-001, REQ-002 and DES-001, no tests; no `tests/api/`.

The person's message (Nam):

> P3 is done and deployed to dev. Continue.
