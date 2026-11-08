# Input — lifecycle case 002 (fictional)

A project repository just created by `pls init juchu --origin existing --stage project --target stg --approver "Sato (G1, G4), Nam (G2, G3)"`. Its `CLAUDE.md` profile:

| Item | Value |
|---|---|
| Origin | `existing` |
| Stage | `project` |
| Release target | `stg` |
| Approvers | G1, G4: Sato; G2, G3: Nam |
| Role tests | `per-role keys` |

The repository is otherwise empty: no `requirements/REQ-*`, no `design/`, no `config/<site>/`, no `ops/onboarding/`. `environments.json` has `dev` (reachable, role dev) only.

The person's first message:
「受注一覧（dev のサイト 1201）に『納期』の項目を追加して、納期を過ぎた受注を一覧で見られるようにしてください。」
