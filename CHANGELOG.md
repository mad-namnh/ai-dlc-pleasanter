# Changelog

Releases of the framework that project repositories pin (`.claude/framework.lock`, ADR-0022). A team uses tags only,
never a branch. How to upgrade a project and how a hotfix is made: `docs/setup.md`, "Framework versions".

Each entry: what changes for a project, and what a project must do after `pls skills sync`.

## Unreleased

Nothing yet.

## v0.3.1 — 2026-11-20

Team rollout phases 7–9 and the phase 8 eval fixes (`plans/2026-11-18-team-rollout-after-freeze/`). CI green on
GitHub Actions (Ubuntu 3.10 / 3.12, Windows 3.12, node, impact rules).

- **Fixes:** `pls check p1` accepts interview sources written as the REQ template shows (`sources/<interview>.md — A3, A7`; TD-75), so G1 no longer refuses them; `pls refs` lists site ids still written as numbers (RAW, the same as lint L-REF-01). Skills: P1 0.9, onboarding 0.9, P5 0.13, script-engineer 0.8 (evals 2026-11-20). After upgrading: `pls skills sync`.

- **`pls drift-watch`** (read only): a scheduled check on the person's own machine that exports the project's dev /
  sandbox / stg sites and reports UI edits against the last release, with the two ways on; Windows balloon and the
  session-start hook. After upgrading: `pls skills sync`, then once per clone `python pls.py drift-watch install
  --env dev --env dev-<you>` (the owner adds `--env stg`); `docs/setup.md`, "Drift job".

- **`pls status`** (read only): the open items of the project and the next command, from the profile, REQ / DES,
  gate records and releases. The lifecycle skill (0.33) starts from it. After upgrading: `pls skills sync`. A one-page
  team guide: `docs/golden-path.md` in the framework.
- **One model per project (ADR-0031):** `pls init` / `pls hook install` write `"model": "opus"` into the project's
  `.claude/settings.json` when it names none, and a PreModelSwitch hook denies a switch to any other model. After
  upgrading: `pls hook install` in each project (needs Claude Code v2.1.251 or later for the switch check).

## v0.3.0 — 2026-11-18

First release for the team (team rollout, `plans/2026-11-18-team-rollout-after-freeze/`).

- **Gates for a team (ADR-0020 accepted):** every dev approves G1–G3, their own tasks included; G4 has one owner who
  delegates it only with a last day (`G4 until YYYY-MM-DD: <name>`); only the owner changes Approvers, Operators and an
  environment's role; approvals are judged by the profile in force when they were made; the customer approves no gate.
  Fixed: `G1–G3: A, B` used to give A and B all four gates.
- **A role edited by hand** in `environments.json` (differing from its record) refuses the commands that read it.
- **Shared project repository:** the template `.gitignore` leaves out only `ops/xref/`, `ops/adopt/`, `ops/triage/`,
  `ops/env-compare/` and a sandbox's releases; everything `pls` or a gate reads stays in git.
- **Sandboxes (ADR-0011 accepted):** `pls sandbox sync` (refresh + apply, refused while UI edits are not harvested).
- **Pinned framework (ADR-0022):** writes outside dev refuse when the framework running is not the commit the project
  pinned, or has uncommitted changes, or the lock cannot say (resync from this tag); `apply` / `bootstrap` / `migrate` on dev warn; `pls http-check` shows it; a session-start hook tells the
  session about it and about a newer release.

After `pls skills sync` in an existing project:
- `pls hook install` (adds the session-start hook);
- `pls skills check` lists the template files that changed: merge `.gitignore` (and `git rm -r --cached` the four
  folders) and the `CLAUDE.md` profile rows (Approvers, Operators, Stage) by hand;
- the G4 owner records the team's Approvers row: `pls profile set Approvers "G1–G3: …; G4: <owner>" …`.
