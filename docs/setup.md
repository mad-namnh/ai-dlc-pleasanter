# Setup — run the AI-DLC framework against your Pleasanter

This takes you from a clone of this repository to a project where Claude Code can build a Pleasanter app from a specification. Allow about 30 minutes the first time, mostly for the Pleasanter preparation in step 2. Nothing secret goes into git or into the chat.

## 0. What you need

| Item | Notes |
|---|---|
| Pleasanter **1.5.x**, a **dev** environment | The framework is verified on 1.5.2. Never use production; the tool refuses to write to `role: prod`. |
| A Pleasanter user that can create sites in one folder | Usually your own admin user. |
| Rights to create groups and users | Or ask your Pleasanter administrator to do step 2b for you. |
| **Python 3.10+** and **git** | Check with `python --version`. On macOS/Linux use `python3` wherever this guide says `python`. |
| **Claude Code**, on a machine that can reach Pleasanter over HTTPS | The agent calls Pleasanter through `pls`. A cloud agent without a network path to your Pleasanter cannot run the demo. |

## 1. Get the framework

```
git clone <url of ai-dlc-pleasanter>
```

Keep the folder name `ai-dlc-pleasanter`. Projects are created next to it.

## 2. Prepare Pleasanter (dev)

The demo app uses three roles, defined in [`demo/roles.json`](../demo/roles.json). For your own app, write your own roles file in the same format.

### 2a. A folder for the app

Create a folder, for example `zz_demo_備品貸出`. Its id is the number in the URL (`…/items/<id>/index`): this is the **parent id**. All sites of the app are created inside it, and nothing outside it is touched.

### 2b. Groups and test users, one per restricted role

| Role | Create | Member |
|---|---|---|
| `somu` | group `zz_demo_総務` | a new user `zz_demo_somu` |
| `staff` | group `zz_demo_社員` | a new user `zz_demo_staff` |
| `admin` | nothing | your own user |

Note the **group ids** and **your user id**; Pleasanter's group and user management lists show them. Optionally, give both groups read access to the folder from 2a, so their users can open it in the UI.

### 2c. API keys, one per role

Log in as each of the three users (yourself, `zz_demo_somu`, `zz_demo_staff`). For each one, create an API key in the user menu → API settings. Each role must have its **own** key: role tests prove what that user can and cannot do, and `pls test` refuses to run if two roles share a key.

Store the keys **outside git and outside the chat**. Use one of these two ways.

**Environment variables** (names from `demo/roles.json`). Windows:

```
setx PLS_DEV_ADMIN_KEY "<your key>"
setx PLS_DEV_SOMU_KEY  "<key of zz_demo_somu>"
setx PLS_DEV_STAFF_KEY "<key of zz_demo_staff>"
```

Then open a **new** terminal and restart Claude Code. A program that is already running does not see variables set with `setx`. On macOS/Linux, `export …` in your shell profile.

**Key files.** In `.pls/connections.json` (step 4), write `"file:admin.key"` instead of `"env:…"`, and put each key alone in that file inside `.pls/`. The `.pls/` folder is gitignored.

## 3. Create the project

From the folder that contains `ai-dlc-pleasanter`:

```
python ai-dlc-pleasanter/tools/pls/pls.py init demo-equipment --approver "<your name>" --roles ai-dlc-pleasanter/demo/roles.json
cd demo-equipment
git init
git add -A
git commit -m "project created by pls init"
```

`init` creates the following:
- `CLAUDE.md` with the project profile: stage `demo`, release target `dev`, you as the approver of every gate;
- the folder layout;
- the launcher `pls.py`;
- the skills, with their versions locked in `.claude/framework.lock`;
- `environments.json` and `connections.example.json`, prepared for the three roles.

From now on, run the tool as **`python pls.py <command>`** inside the project.

## 4. Connect the project to Pleasanter

1. **`environments.json`.** Under `envs.dev`, set:
   - `parent_id`: the folder id from 2a (a number);
   - `principals`: replace each `<…>` with the real id, for example `"admin": "User,1"`, `"somu": "Group,372"`, `"staff": "Group,373"`.

   `python pls.py lint` lists what is still missing (L-ENV-01).
2. **`.pls/connections.json`.** Create the `.pls` folder, copy `connections.example.json` into it as `connections.json`, and set `url` to your Pleasanter address. Keep `"allow_write": true` for dev: the agent deploys and tests on dev. This file is yours alone and gitignored.
3. **Check:**

   ```
   python pls.py http-check --env dev
   python pls.py lint
   ```

   `http-check` must report:
   - HTTP 200 for `admin` (it reads the folder);
   - 200, 403 or 404 for `somu` and `staff` ("key valid, no access" is fine);
   - `writes: allowed`.

   `lint` must report `0 issue(s)`.

## 5. Start

Open Claude Code in the project folder and give it the specification. For the demo, follow [`demo/README.md`](../demo/README.md).

## Commands the person runs (or allows)

Two commands write new things to Pleasanter and ask you to **type the release id**:
- `python pls.py bootstrap B-…` creates the sites;
- `python pls.py apply R-…` applies a release.

The agent cannot type into them. When the agent asks, you have two options:
- run the command yourself in your own terminal;
- tell the agent: *"you may use --yes for dev in this session"*. It then adds `--yes` for dev only.

For the demo, the second option keeps the flow moving.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `pls not found at …` | The launcher cannot find the framework. Set `path` in `.claude/framework.lock`, or the `PLS_HOME` environment variable, to the `ai-dlc-pleasanter` folder. |
| `http-check`: key REJECTED (401) | Wrong or expired key, or the variable is not set in this terminal. Restart the terminal and Claude Code after `setx`. |
| `http-check`: `writes: refused` | `allow_write` is not `true` in `.pls/connections.json`, or `environments.json` role is not `dev`. |
| `keys 'x' and 'y' are the same key` | Two roles use one user's key. Create a key per user (2c). |
| `L-ENV-01` from lint | `parent_id` or a principal id is still a placeholder (step 4). |
| `L-REF-02` from lint | The design uses a role or site that is not in `environments.json`. Add the role (and its group, user and key), or change the design. |
| `pls skills check` reports differences | The project copy of a skill was edited, or the framework is newer. Change skills only in the framework, then run `python pls.py skills sync`. |

## Clean up after a demo

In Pleasanter, delete the demo folder: the sites and test records are inside it. Delete the groups and users from 2b if you do not want them any more. Agents never delete anything in Pleasanter.
