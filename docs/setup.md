# Setup — run the AI-DLC framework against your Pleasanter

This takes you from a clone of this repository to a project where Claude Code can build a Pleasanter app from a specification. Allow about 15 minutes the first time. Nothing secret goes into git or into the chat.

## 0. What you need

| Item | Notes |
|---|---|
| Pleasanter **1.5.x**, a **dev** environment | The framework is verified on 1.5.2. Never use production; the tool refuses to write to `role: prod`. |
| A Pleasanter user that can create sites in one folder | Usually your own admin user. |
| Rights to create groups | Or ask your Pleasanter administrator to do step 2b for you. |
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

### 2b. Groups for the app's roles

The app gives 総務 and 社員 different rights, so their groups must exist before the permissions can be deployed. Create two groups; they need no members for the demo:

| Role | Group |
|---|---|
| `somu` | `zz_demo_総務` |
| `staff` | `zz_demo_社員` |
| `admin` | none: this is your own user |

Note the two **group ids** and **your user id**. Pleasanter's group and user management lists show them.

**Demo stage:** role tests are deferred (project profile `Role tests: deferred`). The agent proves the 社員 restrictions in the configuration, not by logging in as a 社員 user. Testing per role, with a test user and key for each, comes in a later phase (TD-11).

### 2c. One API key — yours

In Pleasanter's user menu → API settings, create an API key for **your** user. Store it outside git and outside the chat, in one of two ways.

**Environment variable.** Windows: `setx PLS_DEV_ADMIN_KEY "<your key>"`, then open a **new** terminal and restart Claude Code. A program that is already running does not see variables set with `setx`. On macOS/Linux, add `export PLS_DEV_ADMIN_KEY=…` to your shell profile.

**Key file.** In `.pls/connections.json` (step 4), write `"file:admin.key"` instead of `"env:PLS_DEV_ADMIN_KEY"`, and put the key alone in `.pls/admin.key`. The `.pls/` folder is gitignored.

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
- `environments.json` (a principal placeholder per role) and `connections.example.json` (your key).

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

   `http-check` must report HTTP 200 for `admin` (it reads the folder) and `writes: allowed`.

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
| `L-ENV-01` from lint | `parent_id` or a principal id is still a placeholder (step 4). |
| `L-REF-02` from lint | The design uses a role or site that is not in `environments.json`. Add the role (and its group, user and key), or change the design. |
| `pls skills check` reports differences | The project copy of a skill was edited, or the framework is newer. Change skills only in the framework, then run `python pls.py skills sync`. |

## Clean up after a demo

In Pleasanter, delete the demo folder: the sites and test records are inside it. Delete the groups from 2b if you do not want them any more. Agents never delete anything in Pleasanter.
