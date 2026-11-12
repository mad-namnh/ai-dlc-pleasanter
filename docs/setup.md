# Setup — run the AI-DLC framework against your Pleasanter

There are two parts:
- **Once per machine and Pleasanter environment** (about 10 minutes): prepare Pleasanter, then run `pls setup`.
- **For every new app or demo**: one command, `pls init`.

Nothing secret goes into git or into the chat.

## What you need

| Item | Notes |
|---|---|
| Pleasanter **1.5.x**, a **dev** environment | Verified on 1.5.2. Never production: the tool refuses to write to `role: prod`. |
| Your Pleasanter user | It must be able to create sites in one folder. Creating groups is needed later, after the permission design (G2). |
| **Python 3.10+** and **git** | On macOS/Linux use `python3` wherever this guide says `python`. An older Python is refused with a message. `pls` writes its files (JSON, reports, records) with LF line endings on every OS; script bodies keep the line endings Pleasanter stores. |
| **Claude Code** on a machine that can reach Pleasanter over HTTPS | The agent works through `pls` over HTTP. |
| This repository, cloned as `ai-dlc-pleasanter` | `git clone <url> ai-dlc-pleasanter` |

## Once: prepare Pleasanter and this machine

1. **In Pleasanter:**
   - a **folder** for the apps, e.g. `AI-DLC-DEMO`;
   - an **API key** for your user: user menu → API settings.
2. **On this machine**, from the folder that contains `ai-dlc-pleasanter`:

   ```
   python ai-dlc-pleasanter/tools/pls/pls.py setup
   ```

   It asks five things:
   - the Pleasanter URL;
   - the folder: paste its URL from the browser;
   - your API key: typed hidden;
   - your login id;
   - whether `pls` may **write** to this Pleasanter from projects made with the profile (`y`/`n`, default `n`). This is your local opt-in, `allow_write` (ADR-0021): writes then go only to an environment with `role: dev` (stg after G4), never to prod. Answer `y` for a dev server you use for demos.

   It then checks the folder with your key, finds your user id, and saves a **profile**:
   - `~/.pls/profiles/dev.json` holds the URL, the folder and your user id;
   - the key is stored separately in `~/.pls/profiles/dev.admin.key`, outside every repository.

   Run it again whenever something changes; it offers the stored answers as defaults. A profile saved before setup asked about writes counts as `n` until you answer.

## Every demo or new app

```
python ai-dlc-pleasanter/tools/pls/pls.py init demo-equipment --approver "<your name>"
cd demo-equipment
python pls.py http-check --env dev
```

For an app that **already runs** in Pleasanter (takeover, 運用保守), add `--origin existing` (usually with `--stage project --target stg`): the agent then starts with onboarding, not with requirements.

`init` creates a ready project from the profile:
- `CLAUDE.md` with the project profile: stage `demo`, release target `dev`, you as approver, role tests deferred;
- the layout and the launcher `pls.py`;
- the skills, locked in `.claude/framework.lock`;
- `environments.json` and `.pls/connections.json`, filled in;
- the first git commit.

`http-check` must show HTTP 200 and `writes: allowed`. It shows `writes: refused` while `allow_write` is false: answer `y` in `pls setup` for the next projects, or set `"allow_write": true` for this project in `.pls/connections.json` yourself (dev/stg only; never an agent). Then open Claude Code in the folder and give it the spec. For the demo, follow [`demo/README.md`](../demo/README.md).

**Permissions are designed, not set up.** The roles and their groups come out of the design (P2). After G2, on dev, run `python pls.py principals --env dev --create` in your terminal: it lists the groups of the design that do not exist yet, asks you to type `dev`, creates them with you as the only member and binds them (ADR-0017; your dev key must be a tenant administrator). Elsewhere the agent tells you which groups to create in Pleasanter, then binds them with `python pls.py principals --env <env>`.

**Role tests.** With role tests `deferred` (the demo default) the agent works with your key only and proves the restrictions of the other roles in the configuration. With `per-role keys`, run `python pls.py test-users --env dev` in your terminal after `principals` and type `dev`: it creates one test user per role (`zz_test_<project>_<role>`), issues its API key into `.pls/test-users/`, adds `keys.<role>` to `.pls/connections.json` and adds the user to the role's group (ADR-0018, ADR-0019; your dev key must be a tenant administrator). If it ends with PERSON STEP, log in as that user, create its key under User > API settings, save it in the file it names and run it again. Removing test users is by hand for now (TD-24).

**Pleasanter version (ADR-0009).** Run `python pls.py version --env dev` once. It detects the build and the settings schema by itself. The application version is only shown to a logged-in user, so open `<url>/versions` in your browser and record what it says: `python pls.py version --env dev --app 1.5.2.0`. When the server is upgraded, `http-check` warns that the build changed; run `version` again.

**KB verification (optional, ADR-0009).** To re-check the knowledge base on your Pleasanter version: create a folder for probe sites, put its id in `environments.json` → `envs.dev.values.kb_probe_parent`, then `python pls.py kb-verify --env dev`. It creates one small probe site per probe once and reuses them.

**Mail and scheduled jobs (ADR-0010).** Notifications and reminders send mail when tests change records on dev. `environments.json` therefore says what each environment does with mail and jobs: `"side_effects": {"mail": "unknown", "jobs": "unknown"}`. While mail is `unknown`, `pls test` refuses tests that change records on a site with notifications or reminders, and `pls apply` refuses a release that adds or changes them. Ask whoever runs the Pleasanter server whether SMTP is configured, then set the value yourself:

| `mail` | Meaning |
|---|---|
| `unknown` | not checked yet (default) |
| `sink` | mail goes to a test mailbox (smtp4dev, MailHog, …), never to people |
| `disabled` | the server sends no mail |
| `live` | real mail is sent — tests on sites with notifications stay refused; releases show a warning |

`jobs` (`unknown`, `disabled`, `live`) is recorded the same way for scheduled server scripts (ADR-0012). The project declares them in `config/_tenant/scheduled-scripts/` (`<name>.js` + `_index.json`, a list of `{"name", "schedule", "enabled"}`). While the project declares any and `jobs` is `unknown`, `pls test` refuses tests that change records and `pls apply` refuses a release that changes a scheduled script; `live` gives a warning. Every release plan lists changed scheduled scripts with a manual deploy step (files resolved for the environment in `releases/<R>/scheduled-scripts/`); after copying them into tenant management, the person records the check with `pls jobs-verified <R> --by <name> --quote "…"` (an operator of that environment from the profile row `Operators`, or a G4 approver). A sandbox uses the riskier of its own and dev's values and never deploys scheduled scripts. The agent never changes these values. The demo app has no notifications, so the demo is not affected.

**Several developers (optional, ADR-0011).** Once per clone: `python pls.py merge-install` (semantic merge of `config/*/site.json`). Per developer: create a folder in Pleasanter, then `python pls.py sandbox create --name <you> --sites <a,b> --parent <folder id>`, `python pls.py bootstrap <B-…>`, `python pls.py sandbox refresh --name <you>`, `python pls.py apply <R-…>`.

## Environment variables

| Variable | What it changes |
|---|---|
| `PLS_HOME` | where the project launcher `pls.py` finds the framework (instead of `path` in `.claude/framework.lock`) |
| `PLS_CONNECTIONS` | another connection file instead of `.pls/connections.json`; the same role and `allow_write` rules apply to it (ADR-0021) |
| `PLS_PROFILE_DIR` | where `pls setup` keeps machine profiles (default `~/.pls/profiles`) |
| `PLS_ACTOR` | the name written into the run log as the actor (default: `git config user.name`); self-asserted, not an identity check |
| `PLS_DEBUG` | `1` prints the Python trace of an unexpected error (exit 3) |
| key references `env:NAME` | an API key read from the environment variable `NAME` (`.pls/connections.json` → `keys`) |

## When a release does not end applied

`pls apply` writes the state into `releases/<R>/plan.json` (`status`) and `apply-log.json`. Only `planned` can be applied; never run `apply` again for the others.

| Status | What happened | What you do |
|---|---|---|
| `refused` (back to `planned`) | nothing was written | fix what the message says, then run `apply` again |
| `rolled-back` | a site failed; every site already written was restored and read back equal to its rollback file | fix the cause; make a new release plan with a new id |
| `uncertain` | a write got no answer: the site may or may not hold the new configuration; nothing was restored | export every site of the release (`pls export`), then `pls mark-applied <R> --export <site>=<file> …` records what is there |
| `recovery-required` | a restore failed or did not read back equal, or the write guard (role, `allow_write`, G4 outside dev, a readable `environments.json`) stopped holding after some sites were written — then nothing more was written and nothing restored | a person restores the sites the message names from `releases/<R>/rollback-<site>.json` in Pleasanter, then exports every site and runs `pls mark-applied` (the message prints the exact command) |
| `applying` | the process stopped during the writes (crash, closed terminal) | as for `uncertain` |
| `applied-unverified` | written, read-back not finished | export every site and run `pls mark-applied` |

`role`, `allow_write` and (outside dev) the G4 record are read again before every site of a release and before restoring: switching `allow_write` to false while a release runs stops it before the next write. A site changed by someone else mid-release ends `rolled-back` when the restores read back equal. `bootstrap` and `migrate` check the guard once per command (TD-39).

## Commands that need you

`python pls.py bootstrap B-…` (creates sites), `python pls.py apply R-…` (applies a release) and `python pls.py migrate R-…` ask you to type the release id, and the agent cannot type it. You have three options:
- run the command yourself;
- tell the agent once: *"you may use --yes for dev in this session"*;
- **for dev only, once per project:** tell the agent that it may write to dev without asking each time. It records your words with `python pls.py profile set dev-writes on --env dev --approver <you> --quote "<your words>"`, and from then on these three commands on that dev environment run without the question; each release names the record (`apply-log.json` → `confirmed`). A sandbox needs its own record; stg and prod always ask. Withdraw it with `python pls.py profile set dev-writes off --env dev --approver <you> --quote "…"` (ADR-0024).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `setup`: `folder …: HTTP 401` | Wrong or expired key: create a new one and run `setup` again. |
| `setup`: `HTTP 404` or `not a folder` | The URL or folder id is wrong, or your user cannot see that folder. |
| `setup` asks for your user id | It was not found by login id; type the id from the user management list. |
| `principals`: `MISSING …` | On dev: `python pls.py principals --env dev --create`. Elsewhere: create that group in Pleasanter (name exactly as listed), then run it again. |
| `principals`: `matches N groups` | Pleasanter allows two groups with the same name. Delete or rename the extra ones in Pleasanter, then run it again. |
| `principals`: `lookup of group … failed` | The lookup did not return a complete answer (connection, rights, or more than one page). Nothing was created; check `http-check` and run it again. |
| `principals --create`: `principals.admin is …` | Your own user is not bound. Create the project with a profile (`pls setup`, `pls init`) or add `"admin": "User,<your id>"` to the env's `principals`. |
| `principals --create`: `not a group with a final name` | `design/roles.json` has a role that is not `principal: "Group"` or still has a placeholder `group_name`. The design is fixed first (P2). |
| `principals --create`: `answered HTTP 403` | Your key is not a tenant administrator. Create the groups in Pleasanter instead. |
| `pls not found at …` | The launcher cannot find the framework. Fix `path` in `.claude/framework.lock`, or set `PLS_HOME` to the `ai-dlc-pleasanter` folder. |
| `L-ENV-01` from `lint` | The project was made without a profile. Run `pls setup`, then create the project again (or fill `environments.json` by hand). |
| `L-REF-04` from `lint` | An environment value that is a number or shorter than 6 characters is used inside longer text. Use it as the whole value of its field, or put the surrounding text into the value (`values` in `environments.json`). |
| `L-REF-02` from `lint` | A role used in the configuration has no group id yet. Create the group and run `python pls.py principals --env dev`. |
| `REFUSED (ADR-0010)` from `test` or `apply` | The site sends mail and `side_effects.mail` is not safe. Check SMTP with the server operator and set `mail` in `environments.json` (see above). |
| `L-MAIL-01` from `lint` | A notification or reminder holds a literal mail address. Put it in `values` and use `${env:NAME}`, or use a principal. |
| `pls: unexpected error (…)` (exit 3) | `pls` stopped on something it did not expect; nothing after that point ran. If the message names a file, the disk or the network, fix that and run again. Otherwise run the same command with `PLS_DEBUG=1` set and report the trace. A refusal is exit 2 and says what to do next. |
| `… has status '…', not 'planned'` | A release plan is used once. If it already wrote (`applying`, `applied-unverified`, `uncertain`, `recovery-required`): export the sites and run `pls mark-applied` as the message says. Otherwise make a new release plan with a new id. |
| `… is not a site this release may write …` | The plan names a site id that is not this environment's own (stale plan, or a shared site). Check `envs.<env>.sites`, then make a new release plan. |
| `pls skills check` differs | `project copy was edited`: change skills only in the framework, then run `python pls.py skills sync`. `framework has a newer version`: run `skills sync`. `framework has an older version`: update the framework checkout first (a sync would downgrade). `differs at the same version`: the framework changed a skill without a new version; sync takes it. |
| `WARNING: session … did P… work after a G4` from `usage report` | One Claude Code session held two change requests. Start a new session for each change request (lifecycle §2); the numbers are still counted. |
| `WARNING: project copies of … were edited` from `step` / `gate` | The command ran. Tell the person; change skills in the framework and run `skills sync`. |

**Without a profile:** `init` still works without `pls setup`. You then fill in `environments.json` (`parent_id`, `principals.admin`) and `.pls/connections.json` yourself. Keys go there as `env:NAME` or `file:PATH`, never the literal key.

## Clean up after a demo

Delete the sites inside the Pleasanter folder; agents never delete. Delete the project folder. The profile stays for the next run.
