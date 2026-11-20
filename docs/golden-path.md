# Golden path — one change, from a fresh machine to a stg release

The one page a developer follows on a real project. Details live in [`setup.md`](setup.md); each step here links to
them instead of repeating them. In a project, `pls` means `python pls.py` run from the project root. At any stop,
`pls status` prints the open items and the next command (read only).

Roles (team rollout N3, N12, N15): **dev** — every developer: approves G1–G3, works on dev and on their own sandbox, has
no stg key and no tenant administrator rights. **Owner** — Nam (or a time-boxed G4 delegate): approves G4, holds the stg
write key, runs the commands that need a tenant administrator.

## 1. Once per developer

| # | Step | Who | Done when |
|---|---|---|---|
| 1 | A Pleasanter account on the MADLAB dev server and a **dev API key** for it (user menu → API settings). Not a tenant administrator | dev, account by the owner | you can log in |
| 2 | A folder of your own in Pleasanter for your sandbox (its id is in the folder URL) | dev | the folder exists |
| 3 | Python 3.10+, git, Claude Code; the framework and the project cloned **side by side** (`.claude/framework.lock` names `../ai-dlc-pleasanter`); the framework on the project's tag: `git -C ai-dlc-pleasanter checkout <tag>` ([setup.md, Framework versions](setup.md#framework-versions)) | dev | `python pls.py skills check` in the project shows no problem |
| 4 | `python ai-dlc-pleasanter/tools/pls/pls.py setup` — URL, your folder, your key, login id, writes `y` ([setup.md, Once](setup.md#once-prepare-pleasanter-and-this-machine)) | dev | profile saved |
| 5 | In the project: copy `connections.example.json` to `.pls/connections.json`, set the dev URL, the key as `"file:<path of your profile key>"` (or `env:NAME`) and `"allow_write": true` for dev only — no stg entry (N20). `pls init` does this for a new project; a cloned project has no command for it yet (TD-74) | dev | — |
| 6 | `python pls.py merge-install` (once per clone) | dev | `.git/config` has the merge driver |
| 7 | `python pls.py http-check --env dev` | dev | HTTP 200, `writes: allowed`, the framework pin line without a warning |
| 8 | Your sandbox: `python pls.py sandbox create --name <you> --sites <a,b> --parent <folder id>`, then `python pls.py bootstrap <B-…>` (you type the id), then `python pls.py sandbox sync --name <you>` ([setup.md, Several developers](setup.md#every-demo-or-new-app)) | dev | `pls status` shows the sandbox line |
| 9 | The drift job on your machine (Windows): `python pls.py drift-watch install --env dev --env dev-<you>` — read only, Mon–Fri every 2 hours; a balloon and the next Claude session tell you when a site was edited on the screen ([setup.md, Drift job](setup.md#drift-job)) | dev | `python pls.py drift-watch run` prints a report |

What you never get: a stg key (not even read only), a tenant administrator key, the right to change Approvers,
Operators or an environment's `role`.

## 2. A change request, in your sandbox

| Step | What happens | Command that records it | Who |
|---|---|---|---|
| Start | a new Claude Code session in the project; the lifecycle skill runs `pls skills check` and `pls status` | — | dev |
| Existing app, first time | onboarding (read only) and spec recovery; a request that came earlier is saved as `requirements/sources/<date>-pending-<slug>.md` | `pls review as-is <site> --approver <you> --quote "<your words>"` | dev |
| P1 | REQ files from the request | `pls check p1` | agent |
| G1 | you (or another dev) read the REQ and decide | `pls gate G1 --approver <you> --item REQ-… --quote "<your words>"` | dev |
| P2 | DES with impact rules and `pls scope` | `pls check p2` | agent |
| G2 | decide the design | `pls gate G2 … --item DES-…` | dev |
| Groups and test users | after G2, if the design adds groups or role tests need users: ask the owner (N15) | owner runs `pls principals --env dev --create`, then `pls test-users --env dev`; you run `pls principals --env dev` (read only) | owner |
| P3 | build in `config/`, release to **your sandbox**, round trip to 0 differences | `pls release-plan --env dev-<you> …`, `pls apply …` | agent, you type the id (or the sandbox's standing permission) |
| UI edits in the sandbox | anything you clicked in Pleasanter goes back to git before the merge | `pls harvest --env dev-<you> --site <s>`, commit | dev |
| A UI edit the drift job reports | the session start or a balloon says a site differs from its last release; read `pls drift-watch show`, then keep it (harvest → change request) or revert it (next release with `--accept-drift`) | your decision in `ops/drift/<date>-<env>-<site>.md` | dev (stg: owner) |
| Merge | merge your branch into the shared branch; pull a teammate's work first | git; then `pls sandbox sync --name <you>` | dev |
| Release to shared dev | one person at a time, from merged git; a plan made before pulling a teammate's release is refused as drift | `pls release-plan --env dev …`, `pls apply …` | dev |
| P4 | tests on dev, coverage, the build against its DES | `pls test …`, `pls coverage`, `pls check p3 --env stg --des DES-…` | agent |
| G3 | decide the verification | `pls gate G3 --approver <you> --env stg --release <R-stg> --item DES-… --quote …` | dev |

## 3. Release to stg (owner)

| Step | Command | Who |
|---|---|---|
| Plan on stg (G3 recorded) | `pls export --env stg --site <s>`, `pls release-plan --env stg --release <R> --export …` | owner |
| G4 | `pls gate G4 --approver Nam --release <R> --quote …` | owner or delegate |
| Apply | `python pls.py apply <R>` (types the id) | owner |
| Smoke tests | `pls test … --env stg --release <R>` | owner |
| Drift baseline | `pls export --env stg --site <s>`, then `pls drift <export> --env stg --site <s>` → 0 differences; `ops/drift/<date>-stg-baseline.md` | owner |

A site whose notifications hold a credential (webhook URL, token) cannot be adopted or released until the
notification is removed from the live site (ADR-0005, ADR-0010); mail stays out of scope (N9).

## 4. Steps that stay manual

`pls` cannot do these; each is listed with how it is recorded, so the next person sees it was done.

| Step | When | How it is recorded |
|---|---|---|
| Save the site once on the screen | after a release that deploys a JSON-format link (lookup in `ChoicesText`): the link lists nothing until then (KB D40 (C), TD-50) | `pls step P5 "screen save <site> after link deploy"` |
| 同期 (synchronise) on the site's サマリ tab | after a release that adds or changes `Summaries[]`: existing parents keep their old value until then (ADR-0028, KB D16) | `pls step P5 "summary sync <site>"` |
| Application version | after the server is installed or upgraded: open `<url>/versions` logged in | `pls version --env <e> --app <version>` |
| Scheduled scripts | a release that changes them: copy the files of `releases/<R>/scheduled-scripts/` into tenant management | `pls jobs-verified <R> --by <name> --quote "…"` |

## When you are stuck

`pls status` names the next command. A refusal of `pls` says what to do; never edit a record, the profile or
`.pls/connections.json` to get past it. Questions about the framework go to the owner; a bug in the framework is reported,
not fixed in the project ([setup.md, Framework versions](setup.md#framework-versions)).
