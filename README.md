# ai-dlc-pleasanter

MADLAB's **AI-DLC** (AI-Driven Development Lifecycle) framework for **Pleasanter (プリザンター)** projects.

The source of truth of a Pleasanter app is its **configuration** (SiteSettings, scripts, permissions), not code. This
framework keeps that configuration in git, lets Claude Code do the work through skills and a deterministic tool
(`pls`), and stops at four human gates. Nothing reaches stg without a recorded approval.

```
P1 requirements ─G1─▶ P2 design ─G2─▶ P3 build ─▶ P4 verify ─G3─▶ P5 release ─G4─▶ P6 operate
      REQ files          DES files      config/ in git   tests, coverage   release plan      drift, triage
```

**Current release: [`v0.3.1`](CHANGELOG.md)** — use tags only, never a branch, in a project.

---

## Contents

1. [What you get](#1-what-you-get)
2. [Roles and rules](#2-roles-and-rules)
3. [Set up your machine (once)](#3-set-up-your-machine-once)
4. [Start a project](#4-start-a-project)
5. [Join an existing project](#5-join-an-existing-project)
6. [Daily work: one change request](#6-daily-work-one-change-request)
7. [Working with Claude Code](#7-working-with-claude-code)
8. [Release to stg (owner)](#8-release-to-stg-owner)
9. [Drift: when someone edits on the screen](#9-drift-when-someone-edits-on-the-screen)
10. [Steps that stay manual](#10-steps-that-stay-manual)
11. [Upgrading the framework](#11-upgrading-the-framework)
12. [Command cheat sheet](#12-command-cheat-sheet)
13. [Troubleshooting](#13-troubleshooting)
14. [Documentation map](#14-documentation-map)
15. [Status](#15-status)

---

## 1. What you get

| Part | What it does |
|---|---|
| **`pls`** (`tools/pls/`, standard-library Python) | Reads and writes Pleasanter over its API: export, unpack to readable files, lint, diff, classify a change (config-only / data-impacting / permission), plan a release with rollback, apply it with a read-back, record gates, check phase outputs, detect drift. Refuses unsafe writes by itself |
| **Skills** (`skills/`, installed into each project) | Tell Claude Code how to do each phase: requirements (EARS), design (ladder of standard features → scripts), build, tests, release, operations, onboarding of an existing app, spec recovery, script changes. A knowledge base (`pls-kb-pleasanter`) holds verified Pleasanter 1.5.2 behaviour |
| **Project template** (`templates/project/`) | What `pls init` creates: `CLAUDE.md` with the project profile, folders, hooks, `environments.json` |
| **Hooks** (written into each project) | Guardrails inside Claude Code: no hand edits of records, a question before any `--yes`, lint after a config edit, phase checks at the end of a turn, the project's model enforced, drift and framework-version notes at session start |
| **Evals** (`evals/`) | Blind test cases per skill; results in `evals/results/` |

**Environments.** Pleasanter **1.5.x** (verified on 1.5.2). Each project knows `dev` (shared), one **sandbox per
developer** (`dev-<you>`), `stg` (MADLAB's own stg). Customer stg / prod are out of scope for now (exported packages
only, applied by the customer).

## 2. Roles and rules

| Role | Who | Can |
|---|---|---|
| **dev** | every developer | approve **G1–G3** (own tasks included); work on shared dev and on their own sandbox; run all read commands |
| **owner** | Nam, or a G4 delegate with an end date | approve **G4**; hold the **stg write key**; run `principals --create` and `test-users` (tenant administrator); change Approvers, Operators, environment roles |
| **customer** | — | approves no gate in this framework |

**Never:**

- put an API key, password or webhook URL in git, in a file outside `.pls/`, or in the chat;
- edit `releases/`, `gates/`, `ops/log/`, `.pls/` or `environments.json` roles by hand to get past a refusal — `pls`
  says what to do instead;
- add `--yes` to a write unless you decided it for that target;
- copy customer data or configuration into this repository;
- change skills or `pls` inside a project — report the problem to the owner (it is fixed in the framework and released
  as a new tag).

A developer has **no stg key** (not even read only) and **no tenant administrator key**.

## 3. Set up your machine (once)

**You need:** Python 3.10+, git, [Claude Code](https://claude.com/claude-code) (v2.1.251 or later), access to the
MADLAB dev Pleasanter over HTTPS, a Pleasanter account (from the owner) and your own **API key** (Pleasanter: user menu →
API settings), and a **folder of your own** in Pleasanter for your sandbox (its id is in the folder URL).

```bash
# 1. clone the framework next to where your projects will live, on the release tag
git clone https://github.com/mad-namnh/ai-dlc-pleasanter.git
git -C ai-dlc-pleasanter checkout v0.3.1

# 2. save a machine profile (URL, folder, your key outside every repository)
python ai-dlc-pleasanter/tools/pls/pls.py setup
```

`setup` asks for the Pleasanter URL, your folder (paste its URL), your API key (hidden), your login id, and whether
`pls` may write to this Pleasanter (`y` for the MADLAB dev server). The key is stored in
`~/.pls/profiles/dev.admin.key`, never in a repository. Details: [`docs/setup.md`](docs/setup.md).

On macOS / Linux use `python3` wherever this guide says `python`.

## 4. Start a project

```bash
# a new app built by this project
python ai-dlc-pleasanter/tools/pls/pls.py init my-app --approver "<your name>"

# an app that already runs in Pleasanter (takeover, 運用保守): onboarding comes first
python ai-dlc-pleasanter/tools/pls/pls.py init my-app --origin existing --stage project --target stg

cd my-app
python pls.py http-check --env dev        # must show HTTP 200 and "writes: allowed" for dev
```

`init` writes the project profile (`CLAUDE.md`), the folders, the launcher `pls.py`, the skills (pinned in
`.claude/framework.lock`), the hooks, `environments.json`, `.pls/connections.json` and the first commit.
Inside a project, `pls` always means `python pls.py` from the project root.

The owner then records who approves what, once:

```bash
python pls.py profile set Approvers "G1–G3: Nam, Taro, Hana; G4: Nam" --approver Nam --quote "<their words>"
```

## 5. Join an existing project

```bash
git clone <project repository> my-app            # next to ai-dlc-pleasanter (the lock names ../ai-dlc-pleasanter)
git -C ai-dlc-pleasanter checkout <the tag in my-app/.claude/framework.lock>
cd my-app
python pls.py skills check                       # no problem expected
```

1. **Connection.** Copy `connections.example.json` to `.pls/connections.json`, set the dev URL, the key as
   `"file:<path of your profile key>"` (or `"env:NAME"`) and `"allow_write": true` **for dev only**. Add no stg entry.
2. `python pls.py merge-install` — semantic merge of `config/*/site.json` (once per clone).
3. `python pls.py http-check --env dev` — HTTP 200, `writes: allowed`, no framework-pin warning.
4. **Your sandbox:**
   ```bash
   python pls.py sandbox create --name <you> --sites <site-a,site-b> --parent <your folder id>
   python pls.py bootstrap B-…               # creates the sandbox sites; you type the id
   python pls.py sandbox sync --name <you>   # deploys the current git configuration to them
   ```
5. **Drift job** (Windows): `python pls.py drift-watch install --env dev --env dev-<you>` (see [§9](#9-drift-when-someone-edits-on-the-screen)).
6. `python pls.py status` — shows the sandbox and the next step.

## 6. Daily work: one change request

Open Claude Code in the project folder and describe the request in your own words (or paste the customer's mail).
**One Claude Code session per change request.** The lifecycle skill starts with `pls skills check` and `pls status`,
then leads you phase by phase. At any time, `python pls.py status` prints the open items and the next command.

| Phase | What happens | You do | Recorded by |
|---|---|---|---|
| **Existing app, first time** | onboarding (read only), as-is spec of the sites the change touches | answer its questions | `ops/onboarding/<date>-summary.md`, `pls review as-is` |
| **P1** | REQ files (EARS, acceptance criteria, open questions in Japanese with defaults). A rough idea → the agent interviews you first | answer, then read the REQs | `pls check p1` |
| **G1** | approve the requirements | say so in your own words | `pls gate G1 --approver <you> --item REQ-… --quote "<your words>"` |
| **P2** | DES: design per element on the ladder (standard settings first, scripts last), impact on existing behaviour, `pls scope` | read the DES | `pls check p2` |
| **G2** | approve the design | your words | `pls gate G2 … --item DES-…` |
| **Groups / test users** | if the design adds groups or role tests need users | ask the **owner** | owner: `pls principals --env dev --create`, `pls test-users --env dev` |
| **P3** | build in `config/`, release to **your sandbox**, round trip to 0 differences | type the release id when asked (or give the sandbox a standing permission) | `pls release-plan --env dev-<you> …`, `pls apply R-…` |
| **UI edits in your sandbox** | anything you clicked in Pleasanter goes back to git | `pls harvest --env dev-<you> --site <s>`, commit | git |
| **Merge** | merge your branch into the shared branch; pull a teammate's work first | git, then `pls sandbox sync --name <you>` | git |
| **Release to shared dev** | one person at a time, from merged git | type the id | `pls release-plan --env dev …`, `pls apply …` |
| **P4** | tests on dev (API), coverage, the build checked against its DES | read the G3 report | `pls test …`, `pls coverage`, `pls check p3 --env stg --des DES-…` |
| **G3** | approve the verification | your words | `pls gate G3 --approver <you> --env stg --release R-… --item DES-… --quote …` |
| **P5 (stg)** | the owner releases — [§8](#8-release-to-stg-owner) | — | — |

**How approvals work.** A gate is recorded only from a person's own words (`--quote`). The agent never approves and
never writes a gate record by hand. `pls gate G1` / `G2` / `G3` refuse while `pls check` reports a finding for that item,
unless the approver accepts the findings in their own words (`--accept-findings "<reason>"`).

**Writes need you.** `bootstrap`, `apply` and `migrate` ask you to type the release id. Alternatives: run the command
yourself; tell the agent "you may use `--yes` for dev-`<you>` in this session"; or, for dev or your sandbox only, record
a standing permission once: `pls profile set dev-writes on --env dev-<you> --approver <you> --quote "<your words>"`.
stg always asks.

## 7. Working with Claude Code

- **Open Claude Code in the project folder**, not in the framework. The project's `CLAUDE.md`, skills and hooks load
  from there.
- **Say what you want, not how.** "Customer wants escalation for high-priority inquiries: (mail)" is enough; the
  lifecycle skill picks the phase and the skill.
- **The model is fixed per project** (`.claude/settings.json`, `opus`); switching with `/model` is denied on purpose:
  the skills were evaluated on that model.
- **Hooks you will see:** an edit under `releases/`, `gates/`, `ops/log/` or `.pls/` is denied; a command with `--yes`
  asks you first; after a config edit, lint findings appear; at the end of a turn, `pls check` findings appear; at
  session start, a note if the framework is not the pinned version or the drift job found something.
- **When the agent asks a question**, answer it. Questions for the customer are written in Japanese in
  `requirements/index.md`, each with the default the agent assumes until the customer answers.
- **When `pls` refuses**, read the message: it says what to do. Never ask the agent to work around it.

## 8. Release to stg (owner)

Only the owner (or a G4 delegate with an end date) has a stg key with `allow_write`.

| Step | Command |
|---|---|
| Plan on stg (after G3) | `pls export --env stg --site <s>` per site, then `pls release-plan --env stg --release R-… --export <s>=<file> …` |
| Report for G4 | the agent writes `releases/R-…/diff-report.md` (Japanese, business words) and `approvals.md` |
| G4 | `pls gate G4 --approver Nam --release R-… --quote "<words>"` — binds this plan and its files; any later change needs a new G4 |
| Apply | `python pls.py apply R-…` (type the id); ends with a read-back that must show 0 differences |
| Scheduled scripts, if any | copy `releases/R-…/scheduled-scripts/` into tenant management, compare, then `pls jobs-verified R-… --by <name> --quote "…"` |
| Smoke tests | `pls test … --env stg --release R-…` |
| Drift baseline | `pls export`, `pls drift` → 0 differences, `ops/drift/<date>-stg-baseline.md` |

**Delegating G4** while away, always with a last day:
`pls profile set Approvers "G1–G3: Nam, Taro, Hana; G4: Nam; G4 until 2026-12-05: Taro" --approver Nam --quote "…"`.

If an apply ends other than `applied`, **never run it again** — see the table "When a release does not end applied" in
[`docs/setup.md`](docs/setup.md#when-a-release-does-not-end-applied).

## 9. Drift: when someone edits on the screen

A customer or a teammate may change a site in the Pleasanter UI. The **drift job** finds it without you asking.

```bash
python pls.py drift-watch install --env dev --env dev-<you>   # once per clone (Windows Task Scheduler)
python pls.py drift-watch run                                 # check now
python pls.py drift-watch show                                # last report
python pls.py drift-watch remove                              # unregister
```

- Runs **Monday–Friday from 09:00, every 2 hours**, while you are logged on; read only; results stay in
  `.pls/drift-watch/`. The owner adds `--env stg`.
- You see a **Windows balloon** when something changed, and the last result at the **start of each Claude session**.
- The report gives, per drifted site, the differences, how reverting would be classified, and the **two ways on**:
  keep the UI change (`pls harvest`, then a change request through the gates) or revert it in the next release
  (`--accept-drift`). Write your decision into `ops/drift/<date>-<env>-<site>.md` and commit it.
- Not reported while your folder lacks a teammate's release that is on the shared branch: `git pull` first.

## 10. Steps that stay manual

`pls` cannot do these; record each so the next person sees it was done.

| Step | When | Record |
|---|---|---|
| Save the site once on the screen | after a release that deploys a lookup link (`ChoicesText` JSON) | `pls step P5 "screen save <site> after link deploy"` |
| 同期 (synchronise) on the サマリ tab | after a release that adds or changes `Summaries[]` | `pls step P5 "summary sync <site>"` |
| Application version | after a server install or upgrade (open `<url>/versions`) | `pls version --env <e> --app <version>` |
| Scheduled scripts | a release that changes them | `pls jobs-verified R-… --by <name> --quote "…"` |

## 11. Upgrading the framework

A project pins the framework in `.claude/framework.lock`. Writes to stg are refused while the running framework differs
from the pin.

```bash
git -C ai-dlc-pleasanter fetch --tags
git -C ai-dlc-pleasanter checkout v0.3.1          # the new tag; read its CHANGELOG.md entry first
cd my-app
python pls.py skills sync                         # skills, launcher, lock
python pls.py hook install                        # hooks and the project model
git add .claude pls.py && git commit -m "chore: framework v0.3.1"
```

Do what the [`CHANGELOG.md`](CHANGELOG.md) entry says (e.g. install the drift job). Template files the project owns
(`CLAUDE.md`, `.gitignore`) are never copied over: `skills sync` names them, you merge by hand.

## 12. Command cheat sheet

Run in the project folder as `python pls.py <command>`. Read-only commands are safe at any time.

| Purpose | Command | Writes Pleasanter? |
|---|---|---|
| Where am I, what next | `status` | no |
| Connection, key, version, pin | `http-check --env <e>` | no |
| Phase checks | `check p1` · `check p2` · `check p3 --env <e> --des DES-…` | no |
| Lint the configuration | `lint` (`--summary`) | no |
| Components without round-trip evidence | `scope [--site S]` | no |
| Read a site | `export --env <e> --site <s>` | no |
| Site → readable files / back | `unpack <export> --env <e> --site <s>` · `pack --env <e> --site <s>` | no |
| Compare with the last release | `drift <export> --env <e> --site <s>` | no |
| Classify a change | `classify <export> --env <e> --site <s>` | no |
| Plan a release | `release-plan --env <e> --release R-… --export <s>=<file> …` | no |
| Apply a release | `apply R-…` | **yes** (asks) |
| Create sites for a new app / sandbox | `bootstrap B-…` | **yes** (asks) |
| Your sandbox | `sandbox create` · `sandbox sync --name <you>` · `sandbox drop` | sync: **yes** |
| UI edits back to git | `harvest --env <e> --site <s>` | no |
| Tests | `test <spec> --env <e> [--release R-…]` | records only as the spec says |
| Coverage REQ → DES → config → tests | `coverage [--env <e>]` | no |
| Record a gate | `gate G1|G2|G3|G4 --approver <name> --quote "<words>" …` | no |
| Project profile | `profile set <field> … --approver … --quote …` | no |
| Site ids in scripts | `refs --site <s>` (`--keep` / `--ref` record a person's decision) | no |
| Scripts ↔ columns index | `xref --site <s>` | no |
| Drift job | `drift-watch run|show|install|remove` | no |
| Skills and pin | `skills check` · `skills sync` | no |
| Groups / test users (owner) | `principals --env dev --create` · `test-users --env dev` | **yes** (asks) |

Full list: `python pls.py -h` and `python pls.py <command> -h`; reference in
[`docs/architecture.md` §7.1](docs/architecture.md).

## 13. Troubleshooting

| You see | Do |
|---|---|
| `writes: refused` in `http-check` | `"allow_write": true` for dev in your own `.pls/connections.json` (never for stg on a dev machine) |
| `REFUSED: the framework … pinned` | `git -C ai-dlc-pleasanter checkout <tag in .claude/framework.lock>`, or upgrade the project ([§11](#11-upgrading-the-framework)) |
| `pls not found at …` | the framework is not next to the project: fix `path` in `.claude/framework.lock` or set `PLS_HOME` |
| a release plan refused as **drift** | `git pull` (a teammate released), or harvest your UI edits, then plan again |
| `REFUSED (ADR-0010)` from `test` / `apply` | the site sends mail and `side_effects.mail` is not safe: ask the server operator, set it in `environments.json` |
| `L-REF-01` from `lint` | a site id is written as a number in a script: `pls refs --site <s>` lists it (RAW); write `${site:name}` |
| `pls gate` refuses with findings | fix what `pls check p1|p2|p3` reports, or accept them in your own words (`--accept-findings`) |
| an apply ended `uncertain` / `recovery-required` | do **not** apply again; follow the message (export, `mark-applied`) |
| `pls: unexpected error` (exit 3) | run again with `PLS_DEBUG=1` and send the trace to the owner |

More: [`docs/setup.md` → Troubleshooting](docs/setup.md#troubleshooting).

## 14. Documentation map

| Read | For |
|---|---|
| [`docs/golden-path.md`](docs/golden-path.md) | the one-page path of a developer on a real project |
| [`docs/setup.md`](docs/setup.md) | every setup detail, environment variables, failed releases, team rules, troubleshooting |
| [`docs/architecture.md`](docs/architecture.md) | the frame: phases, gates, invariants, components, command and lint reference |
| [`docs/adr/`](docs/adr/README.md) | every architecture decision and its status |
| [`CHANGELOG.md`](CHANGELOG.md) | what each release changes and what a project must do after upgrading |
| [`skills/README.md`](skills/README.md) | skill versions and what changed in each |
| [`evals/README.md`](evals/README.md) | how skills are evaluated; results in `evals/results/` |
| [`demo/README.md`](demo/README.md) · [`demo/lifecycle-and-demo-guide.html`](demo/lifecycle-and-demo-guide.html) | the demo run and a visual guide (open in a browser) |
| [`docs/tech-debt.md`](docs/tech-debt.md) | deferred work with deadlines |
| [`CLAUDE.md`](CLAUDE.md) · [`docs/agent-rules.md`](docs/agent-rules.md) | rules for agents working on this framework itself |

## 15. Status

Release **v0.3.1** (2026-11-20). Feature freeze; team rollout plan:
[`plans/2026-11-18-team-rollout-after-freeze/plan.md`](plans/2026-11-18-team-rollout-after-freeze/plan.md).
`main` holds the last release; work happens on `brownfield-adr`; CI runs both suites on every push
([`.github/workflows/framework-ci.yml`](.github/workflows/framework-ci.yml)).

| Item | State |
|---|---|
| Architecture v0.3 (P1–P6, G1–G4, invariants I1–I9), ADRs 0001–0031 | ✅ |
| `pls` toolchain, HTTP transport, write guards, gate records, phase checks, drift job | ✅ |
| Skills (11) — P1 0.9, P2 0.14, P3 config 0.12, P3 script 0.8, P4 0.10, P5 0.13, P6 0.4, lifecycle 0.33, onboarding 0.9, spec recovery 0.5, KB 0.36 | ✅ evaluated (see `evals/results/`) |
| Team use: gates for a team, sandboxes, version pinning, one model per project, CI, `pls status`, golden path, drift job | ✅ |
| Trial with two accounts, then one developer on a real change | ⏳ next |
| Customer stg / prod deployment | ⏸ later, on request |

**Repository split.** This repository holds the framework only: tools, skills, rules, ADRs, synthetic spikes. It never
contains customer configuration or data. Each customer project has its own repository, created with `pls init`.

All documentation in this repository is in English (`CLAUDE.md`); messages shown to Pleasanter end users stay in
Japanese.
