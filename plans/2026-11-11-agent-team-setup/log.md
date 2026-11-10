# Setup log — agent team for framework development

- **Date:** 2026-11-11
- **Prompt executed:** `prompt-rev4.md` (Revision 4, approved by Nam with five amendments), sections 0–7. The trial (section 8) was **not** run.
- **Session:** Claude Code 2.1.322 on Windows 11; Python 3.12.10; Node 24.19.0.

## 0. State at the start

- Branch `brownfield-adr`, HEAD `56a0f9e` (= `main` = `origin/main`).
- Uncommitted: only `plans/2026-11-11-agent-team-setup/` and `plans/reports/2026-11-11-agent-team-prompt-review.md` (this mission's files).
- `.gitignore` already covers `__pycache__/` and `*.pyc`. After both suites, `git status` shows no other new file, so nothing was added to `.gitignore`.
- `.claude/settings.local.json` exists (Nam's, ignored by his global git ignore): an allow list of 6 rules. Not edited.
- Next free ADR number: 0016 (0014 = trust boundaries, 0015 = undoing an applied release).
- Skills under `skills/` are installed into project repositories (`tools/pls/pls.py` `_framework_skills`, `sync_skills`): the team's skill is therefore under `.claude/skills/`.

## 0.4 What the official documentation says (fetched 2026-11-11)

Source pages: `code.claude.com/docs/en/sub-agents.md`, `skills.md`, `permissions.md`, `settings.md`, `settings-reference.md`. Looked up by a research subagent; quotations as it returned them.

| Question | Answer | Quotation |
|---|---|---|
| Where project subagents live | `.claude/agents/` | "Project subagents (`.claude/agents/`) are ideal for subagents specific to a codebase." |
| Frontmatter fields | `name`, `description` required; also `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory`, `background`, `effort`, `isolation`, `color`, `initialPrompt` and others | "must match the table exactly" |
| `model` values | aliases, a full id, or `inherit` | "`sonnet`, `opus`, `haiku`, `fable`, a full model ID … or `inherit`" |
| `tools` | comma-separated string or YAML list | "as a comma-separated string such as `Read, Grep, Bash` or a YAML list" |
| Model per call | yes, alias only; it wins over the frontmatter | "that parameter takes a model alias: `sonnet`, `opus`, `haiku`, or `fable`" |
| Can a subagent start a subagent | **yes, by default** | "By default, a subagent can spawn subagents of its own, up to three layers below the main conversation." Off with `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1` |
| Project skills | found in `.claude/skills/` | "Claude Code loads project skills from `.claude/skills/` in the directory where you start it and in every parent directory up to the repository root." |
| Skill added during a session | picked up, except a new top-level skills folder | "If you create a top-level skills directory that didn't exist when the session started, run `/reload-skills`." |
| Bash rule | `Bash(git push *)` | "Put the `*` after the subcommand." Limit: "A push written another way, such as `git -C . push`, isn't matched." |
| Edit / Write rule | one `Edit(...)` rule covers every editing tool | "`Edit` rules apply to all built-in tools that edit files." |
| Read rule | `Read(...)`; also covers recognised Bash file commands | "apply to Claude's built-in file tools, to file commands Claude Code recognizes in Bash, such as `cat`, `head`, `tail`, `sed`, and `tee`" — not a script that opens files itself |
| Path anchors | `/path` = relative to the settings source (project root for project settings); `path` or `./path` = current directory; `~/path` = home; `//path` = absolute | "A pattern like `/Users/alice/file` isn't an absolute path." |
| Outside the project | absolute form only; Windows drive `C:\` is written `//c/…`; all drives `//**/…` | "To match across all drives, use `//**/.env`." **`../…` is not documented.** |
| `deny` vs `allow` | deny first, from every scope | "deny rules from any scope are evaluated before allow rules"; "An allow rule can't carve an exception out of a deny rule." |
| When a settings edit applies | in the running session | "Claude Code watches your settings files and reloads them when they change" |
| Rules and subagents | apply to both | "The rule applies to the main conversation and to subagents." |

Not documented (so not relied on): a `../` relative rule form; a literal `C:\` rule form.

## Decisions taken while setting up

- Subagent frontmatter uses `model: inherit`; the Orchestrator passes the model per call (aliases), as `CLAUDE.md` "Adaptive Model Routing" says.
- `.pls/**` is denied with the absolute all-drives form `//**/.pls/**`, the only documented way to reach a sibling folder such as `../_agent-scratch/`. No machine-specific path is written into the repository.
- `Bash(git push)` (exact) is listed next to `Bash(git push *)`, because the documentation does not say that the wildcard form matches the bare command.
- `.claude/settings.local.json` is in the deny list for Edit (Nam's decision: the list equals stop point 3). Claude Code's own "always allow" choices are written by the application, not by the Edit tool.
- Nesting is on by default, so "a subagent never starts a subagent" is an instruction in each agent file, not an enforced limit. ADR-0016 lists switching it off as an open question.
- The reference forms live next to the skill (`.claude/skills/pls-x-dev-orchestrator/references/`), not under `templates/`, which holds what `pls init` copies into projects.

## Files written

| File | What |
|---|---|
| `.claude/agents/pls-x-reviewer.md`, `pls-x-eval-case-runner.md`, `pls-kb-curator.md` | the three subagents |
| `.claude/skills/pls-x-dev-orchestrator/SKILL.md` + `references/` (`task.md`, `plan.md`, `report.md`, `reviewer-brief.md`, `eval-case-brief.md`) | the Orchestrator's workflow and forms |
| `docs/agent-rules.md` | stop points, who writes what, scratch space, briefs, budget, limits |
| `.claude/settings.json` | 12 deny rules (written last) |
| `docs/adr/0016-agent-team-for-framework-development.md`, `docs/adr/README.md` | the ADR (Proposed) |
| `docs/tech-debt.md` | TD-21 (hook) |
| `CLAUDE.md` | section "Working as an agent team" (appended; nothing else changed) |
| `HANDOFF.md` | paragraph "Agent team" in "Resume here" |
| `plans/2026-11-11-agent-team-setup/permission-checks.md` | the checks for a new session |

## Checks in this session

| Check | Result |
|---|---|
| `.claude/settings.json` is valid JSON, 12 deny rules, syntax as documented | ok |
| Deny list vs stop point 3 of `docs/agent-rules.md` | equal, except "the Mandatory section of `CLAUDE.md`" (a rule matches files, not sections) — by rule only |
| `.claude/settings.local.json` unchanged | ok (not touched) |
| `python -m unittest discover -s tools/pls/tests` from the repository root | Ran 346, OK |
| `node --test tools/pls/tests/test_runner.mjs` | 15 pass, 0 fail |
| Python 3.10 suite | not run: no Python under `tools/pls` changed |
| `git push --dry-run agent-team-no-such-remote`, after the settings file was written | **denied** by the permission system in this session, before execution. Consistent with the rule firing and with settings being applied to a running session; the denial message does not name the rule, so this is an observation, not proof. |

## Verified / not verified

| Control or claim | Status |
|---|---|
| Rule syntax, precedence, live reload, rules apply to subagents | verified against the documentation (table above) |
| Suites pass after the setup | verified (run) |
| A push in the plain spelling is denied | observed once in this session |
| The Edit / Read rules fire (rows 3–13 of `permission-checks.md`) | **not verified** — new session |
| The `.pls` rule fires outside the project | **not verified** — new session (row 12) |
| A cold-start session finds the skill and the subagents | **not verified** — new session (row 0). In this session `.claude/skills/` was a new top-level folder, which needs `/reload-skills` or a restart. |
| Rules stop a subagent | documented; **not verified** here (row 15) |
| Reviewer makes no change; case-runner does not open the rubric | by instruction only — not enforceable |
| Anything on macOS or Linux | **not verified**, not claimed |

## Not done, on purpose

- The trial (section 8).
- A hook (TD-21).
- No change to `skills/`, `skills/README.md`, `templates/`, `tools/`, `evals/`.
- No push; `main` untouched.

## Prompt for the trial session (task A, chosen by Nam)

Paste into a NEW Claude Code session started in the repository:

```
Chạy task framework sau bằng skill pls-x-dev-orchestrator (đội agent của repo này).

Trước khi làm task: chạy các kiểm tra trong plans/2026-11-11-agent-team-setup/permission-checks.md,
ghi kết quả vào bảng, commit file đó, và báo cho tôi dòng nào failed hoặc not verified. Chỉ làm task
sau khi tôi trả lời.

Task (roadmap P3-1, tiêu chí review A1): thêm test trong tools/pls/tests để test FAIL khi
docs/architecture.md mục 7.1 (bảng lệnh của pls) hoặc mục 7.2 (danh mục lint rule) nêu một lệnh / một
lint rule mà pls không có, hoặc thiếu một lệnh / lint rule mà pls có. Nguồn sự thật là parser của
tools/pls/pls.py và các mã rule mà lint thực sự phát ra. Sửa docs/architecture.md cho khớp nếu test
chỉ ra lệch.

Ràng buộc: không đụng guard, gate, quyền hay protected path nào; không đổi hành vi của lệnh nào;
không push; commit local trên brownfield-adr theo "How we work" trong HANDOFF.md.

Definition of done: test mới fail trên commit cha (hoặc fail khi cố ý làm lệch bảng) và pass sau thay
đổi; hai bộ test pass; có review độc lập của pls-x-reviewer; báo cáo tiếng Việt theo mẫu của skill,
nêu rõ đã kiểm chứng gì và chưa kiểm chứng gì.
```
