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
| **Python 3.10+** and **git** | On macOS/Linux use `python3` wherever this guide says `python`. |
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

   It asks four things:
   - the Pleasanter URL;
   - the folder: paste its URL from the browser;
   - your API key: typed hidden;
   - your login id.

   It then checks the folder with your key, finds your user id, and saves a **profile**:
   - `~/.pls/profiles/dev.json` holds the URL, the folder and your user id;
   - the key is stored separately in `~/.pls/profiles/dev.admin.key`, outside every repository.

   Run it again whenever something changes; it offers the stored answers as defaults.

## Every demo or new app

```
python ai-dlc-pleasanter/tools/pls/pls.py init demo-equipment --approver "<your name>"
cd demo-equipment
python pls.py http-check --env dev
```

`init` creates a ready project from the profile:
- `CLAUDE.md` with the project profile: stage `demo`, release target `dev`, you as approver, role tests deferred;
- the layout and the launcher `pls.py`;
- the skills, locked in `.claude/framework.lock`;
- `environments.json` and `.pls/connections.json`, filled in;
- the first git commit.

`http-check` must show HTTP 200 and `writes: allowed`. Then open Claude Code in the folder and give it the spec. For the demo, follow [`demo/README.md`](../demo/README.md).

**Permissions are designed, not set up.** The roles and their groups come out of the design (P2). After G2 the agent tells you which groups to create; they need no members in the demo. It then binds them with `python pls.py principals --env dev`.

**Demo stage:** role tests are deferred. The agent works with your key only, and proves the restrictions of the other roles in the configuration. Testing as each role, with a test user and key for each, comes in a later phase (TD-11).

**Pleasanter version (ADR-0009).** Run `python pls.py version --env dev` once. It detects the build and the settings schema by itself. The application version is only shown to a logged-in user, so open `<url>/versions` in your browser and record what it says: `python pls.py version --env dev --app 1.5.2.0`. When the server is upgraded, `http-check` warns that the build changed; run `version` again.

**Mail and scheduled jobs (ADR-0010).** Notifications and reminders send mail when tests change records on dev. `environments.json` therefore says what each environment does with mail and jobs: `"side_effects": {"mail": "unknown", "jobs": "unknown"}`. While mail is `unknown`, `pls test` refuses tests that change records on a site with notifications or reminders, and `pls apply` refuses a release that adds or changes them. Ask whoever runs the Pleasanter server whether SMTP is configured, then set the value yourself:

| `mail` | Meaning |
|---|---|
| `unknown` | not checked yet (default) |
| `sink` | mail goes to a test mailbox (smtp4dev, MailHog, …), never to people |
| `disabled` | the server sends no mail |
| `live` | real mail is sent — tests on sites with notifications stay refused; releases show a warning |

`jobs` (`unknown`, `disabled`, `live`) is recorded the same way for scheduled server scripts; its checks come with ADR-0012. The agent never changes these values. The demo app has no notifications, so the demo is not affected.

**Several developers (optional, ADR-0011).** Once per clone: `python pls.py merge-install` (semantic merge of `config/*/site.json`). Per developer: create a folder in Pleasanter, then `python pls.py sandbox create --name <you> --sites <a,b> --parent <folder id>`, `python pls.py bootstrap <B-…>`, `python pls.py sandbox refresh --name <you>`, `python pls.py apply <R-…>`.

## Commands that need you

`python pls.py bootstrap B-…` (creates sites) and `python pls.py apply R-…` (applies a release) ask you to type the release id, and the agent cannot type it. You have two options:
- run the command yourself;
- tell the agent once: *"you may use --yes for dev in this session"*.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `setup`: `folder …: HTTP 401` | Wrong or expired key: create a new one and run `setup` again. |
| `setup`: `HTTP 404` or `not a folder` | The URL or folder id is wrong, or your user cannot see that folder. |
| `setup` asks for your user id | It was not found by login id; type the id from the user management list. |
| `principals`: `MISSING …` | Create that group in Pleasanter (name exactly as listed), then run it again. |
| `pls not found at …` | The launcher cannot find the framework. Fix `path` in `.claude/framework.lock`, or set `PLS_HOME` to the `ai-dlc-pleasanter` folder. |
| `L-ENV-01` from `lint` | The project was made without a profile. Run `pls setup`, then create the project again (or fill `environments.json` by hand). |
| `L-REF-02` from `lint` | A role used in the configuration has no group id yet. Create the group and run `python pls.py principals --env dev`. |
| `REFUSED (ADR-0010)` from `test` or `apply` | The site sends mail and `side_effects.mail` is not safe. Check SMTP with the server operator and set `mail` in `environments.json` (see above). |
| `L-MAIL-01` from `lint` | A notification or reminder holds a literal mail address. Put it in `values` and use `${env:NAME}`, or use a principal. |
| `pls skills check` differs | Change skills only in the framework, then run `python pls.py skills sync`. |

**Without a profile:** `init` still works without `pls setup`. You then fill in `environments.json` (`parent_id`, `principals.admin`) and `.pls/connections.json` yourself. Keys go there as `env:NAME` or `file:PATH`, never the literal key.

## Clean up after a demo

Delete the sites inside the Pleasanter folder; agents never delete. Delete the project folder. The profile stays for the next run.
