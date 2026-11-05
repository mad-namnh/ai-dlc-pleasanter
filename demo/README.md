# Demo — from a natural-language spec to a running Pleasanter app

**What it shows:** Claude Code builds an equipment-loan app (備品貸出管理) in Pleasanter from a short customer mail. The framework drives it through every lifecycle phase, and a person approves each gate:

P1 requirements → **G1** → P2 design → **G2** → P3 build (deploy to dev) → P4 verify → **G3** → P5 release → **G4** → P6 operate

Target: **dev only**. P5 records the tested dev state as the release (decision B1).

| Item | |
|---|---|
| Input | [`spec.md`](spec.md): a mail from a fictional 総務部, in Japanese |
| Roles | [`roles.json`](roles.json): `admin` (you), `somu` (総務), `staff` (社員) |
| Result | Two sites (equipment register, loans) with a 返却 button, an overdue list, a 貸出中 count and role permissions. API tests on dev; 社員 restrictions checked in the configuration (role tests deferred). Release records are in git. |
| Setup | [`docs/setup.md`](../docs/setup.md), steps 0–4, done **before** the demo |
| Time and tokens | Measured in the dry run (`demo/results/`). Plan for about an hour with discussion at each gate. |

## Before the audience arrives

1. Do setup steps 0–4. `python pls.py http-check --env dev` must be green and `python pls.py lint` must show 0 issues.
2. Open Claude Code in the project folder.
3. Open the Pleasanter demo folder in a browser tab; it is still empty.

## Script

At each step, say the line in the **You say** column to Claude Code (in any language). Then show what is listed under **Show**.

| # | Phase | You say | The agent does | Stops at | Show |
|---|---|---|---|---|---|
| 1 | start | *"Build the app for this customer request. You may use --yes for dev in this session."* + paste the mail from `spec.md` | loads the lifecycle; P1: saves the mail and writes REQ-… with acceptance criteria and questions (Japanese) with `[assumed]` defaults | **G1** | `requirements/index.md`: the REQ table and the questions. Point out the derived requirements and the assumptions. |
| 2 | G1 | *"Approve G1 with the assumed defaults."* | records G1. P2: sites, columns, statuses, the 返却 process, permissions per role, ladder rungs, classification | **G2** | `design/decisions/DES-001-….md`: the design table, rejected alternatives, roles used. |
| 3 | G2 | *"Approve G2."* | P3: `bootstrap` creates the two sites → export → unpack → build `config/` → `canon` / `lint` → `release-plan` → `apply` to dev → round trip. If Pleasanter stored something differently, it folds that back and applies once more. | (no gate) | Refresh the Pleasanter folder: the two sites appear and are configured. `git log`: one commit per step. |
| 4 | P4 | (continues) | writes the test specs from the acceptance criteria, runs them with your key, checks the 社員 restrictions in the configuration (role tests are deferred in the demo), checks coverage, writes `g3-verification.md` | **G3** | The test summary and coverage. Open a loan in the browser and press 返却; the register shows the item as available again. |
| 5 | G3 | *"Approve G3."* | P5: drift 0 since the tests → diff report (Japanese summary for the customer) → approvals | **G4** | `releases/<release>/diff-report.md`, top part. |
| 6 | G4 | *"Approve G4."* | records the release, marks the REQs released, writes the drift baseline (P6), commits | done | `requirements/index.md` (released), `ops/drift/…-dev-baseline.md`, `git log --oneline`. |

**Optional epilogue (P6):** change something in the Pleasanter UI, for example add a choice to 種別. Then ask *"Check dev for drift."* The agent finds the change, classifies it, and asks whether to accept it as a change request or revert it.

## If something goes off script

- **The agent asks a question at a gate.** Answer it. "Approve with changes: …" is fine.
- **A test fails in P4.** The agent decides whether it is a build, design or requirement defect and goes back to that phase. Let it; this is part of the demo.
- **`pls` refuses a plan** (drift, slots, migration). The agent explains why and asks you. Do not tell it to bypass the refusal.
- **Connection errors.** Run `python pls.py http-check --env dev`, then go through the setup troubleshooting table.

## Reset for the next run

Delete the Pleasanter demo folder's contents (or the folder, and create a new one with a new `parent_id`). Delete the project folder and run `pls init` again (setup step 3).
