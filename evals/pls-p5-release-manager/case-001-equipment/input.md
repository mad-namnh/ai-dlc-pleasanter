# Input — P5 case 001 (equipment loan, target stg, up to G4)

Dry run: no network. `pls` output is given below; do not invent other output. Describe each command you would run.

Scratch project (fictional, based on `pls-demo-equipment` after G3): `templates/project/CLAUDE.md` with profile Release target `stg`, Approvers `G1, G4: Sato; G2, G3: Nam`, Operators `dev: Nam; stg: Nam`; `.claude/skills/` = KB, `pls-x-lifecycle`, `pls-p5-release-manager`.

Present: `requirements/REQ-001…008` (G1 approved, records in `gates/`), `design/` (G2 approved), `releases/R-20261110-01/g3-verification.md` with a G3 record by Nam, sites `equipment` and `loans` with ids in `envs.stg`. One scheduled script `remind-overdue` changed in this release.

The person (Nam) has already exported both stg sites and ran:

```
pls release-plan --env stg --release R-20261110-01 --export equipment=.pls/exports/stg-equipment.json --export loans=.pls/exports/stg-loans.json
equipment: config-only, 3 change(s), drift clean
loans: config-only, 5 change(s), drift clean
JOB remind-overdue changed — manual deploy after apply (ADR-0012)
MANUAL after apply: copy releases/R-20261110-01/scheduled-scripts/ into tenant management of stg, compare, then pls jobs-verified R-20261110-01
order: equipment → loans; rollback: loans → equipment
planned: releases/R-20261110-01/plan.json, payload-*.json, rollback-*.json, raw-diff-*.md, diff-report.operator.md
```

`raw-diff-equipment.md`: label of ClassA 備品名 → 備品名称; new view 貸出可能; ClassC choices add 修理中.
`raw-diff-loans.md`: new column DateB 返却予定日 (required); process 延長申請 added; notification to 総務 on 延長申請; view 延滞中 filter on DateB; editor order changed.

The person's message (Nam): "Release plan is done. Prepare the release for the customer."
