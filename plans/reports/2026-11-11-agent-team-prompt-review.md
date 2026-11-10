# Adversarial review — agent-team setup prompt (Revision 3)

- **Date:** 2026-11-11
- **Object:** candidate prompt "Mission: a governed AI agent development team for ai-dlc-pleasanter", Revision 3 (not executed)
- **Repository state reviewed:** branch `brownfield-adr` = `main` = `56a0f9e`, working tree clean
- **Environment:** Windows 11, Claude Code 2.1.322, Python 3.12.10, Node 24.19.0
- **Method:** read-only inspection of the repository; both framework suites run from the repository root (346 Python OK, 15 node pass). The review ran in an existing session, not in a new one as the brief asked.
- **Not verified:** Claude Code hook semantics were not checked against official documentation. Every finding that depends on them says so.

## A. Executive verdict

**NOT READY.**

- It is written against a repository state that no longer exists: ADR-0014 and ADR-0015 are taken, and the trial task (G1) is already implemented.
- The orchestrator skill would be shipped into every customer project repository by `pls init` / `pls skills sync`.
- The hook's failure behaviour is specified in a way that cannot be implemented and most likely fails open.
- Nothing stops the team from editing its own guardrails or the standard it is reviewed against.
- The eval-runner role contradicts the repository's blind-eval rule.

## B. Critical and High findings

| ID | Sev. | Confidence | Location | Problem and failure scenario | Required correction |
|---|---|---|---|---|---|
| GOV-01 | High | Confirmed | Candidate title, §5.4, §6, §7, §10; `docs/adr/` | `0014-trust-boundaries.md` and `0015-undoing-an-applied-release.md` exist. The candidate hard-codes "ADR-0014" in text that will be written into `CLAUDE.md` and the skill. "Do not accept ADR-0014" then refers to the trust-boundaries ADR, whose rows Nam is deciding (`HANDOFF.md` "Waiting for Nam"). | Refer to "the agent-team ADR" by a placeholder resolved at inspection (next free is 0016). |
| TRIAL-01 | High | Confirmed | §8; `tools/pls/pls.py:53`, `docs/setup.md:15`, `tools/pls/tests/test_written_files_use_lf_on_every_os.py` | G1 is done (commit `877d2dc`): start-up guard, 3.10 suite run, test. A cold-start trial finds nothing to implement, or re-does finished work. | Choose an open item as the trial. |
| ARCH-01 | High | Confirmed | §2; `tools/pls/pls.py:2213-2214, 2234-2245`; `CLAUDE.md:24-27` | `_framework_skills` installs every `skills/*/SKILL.md` into each project's `.claude/skills`. `skills/pls-dev-orchestrator` would reach customer projects. The name also breaks the `pls-<phase>-<role>` convention, as do all seven agent names. | Keep framework-development assets out of `skills/`; name them by the convention. |
| SEC-01 | High | Probable (semantics not verified) | §5.2 "Fail safe" | "If the hook cannot parse its input, it blocks Write/Edit outside the repository and git push" is impossible: unparsed input cannot be classified. If only one specific exit code blocks, then a missing interpreter, an exception or a timeout lets the operation through. | Deny on every internal failure; verify what blocks in 2.1.322; state the residual. |
| SEC-02 | High | Probable | §5.2; this machine | The repository path contains a space (`01. Project`), sibling folders have Japanese names, and the console code page is cp932 (seen in test output). Unquoted invocation or default stdio decoding crashes the hook, which combines with SEC-01. | Quote the script path; read stdin as bytes and decode UTF-8; test with a non-ASCII path. |
| SEC-03 | High | Confirmed | §1.2, §4.1 | `.claude/settings.json`, `.claude/hooks/`, `docs/agent-rules.md` are Orchestrator-owned with no stop point. So are `docs/review-criteria.md`, `evals/**/expected.md` and `templates/project/CLAUDE.md` (project hard rules, owned by skill-author through `templates/`). The team can disable its tripwire or weaken the standard (B4, EV-01, EV-02). | Add these as human stop points and as protected paths. |
| EVAL-01 | High | Confirmed (rule); nesting not verified | §1 eval-runner, §2.1 step 7; `HANDOFF.md` "How we work"; `CLAUDE.md` "Evals are exempt" | Repository rule: one fresh subagent per case, rubric unseen, model recorded, never routed cheaper. The candidate has one `sonnet` eval-runner that runs cases and grades with the rubric. It sees the rubric, and a subagent may not be able to start a fresh one per case. | Orchestrator starts one case-runner per case; grading is a separate step. |
| GOV-02 | High (A4) | Confirmed | §2.3, §7; `CLAUDE.md` "Adaptive Model Routing" | `CLAUDE.md` already has a routing section (tiers, `haiku/sonnet/opus/fable`, effort, eval exemption). The candidate adds a second, different routing policy in the skill and says none belongs in `CLAUDE.md`. | One source: the skill points to the existing section. |
| SEC-04 | High | Confirmed (precondition) | §2.1 step 5, §5.3 item 4 | `../_agent-scratch/` sits beside customer-derived projects. "A copy of a sample project" does not exclude `.pls/` (connections, key files, exports) or `tests/seed/`. The hook then allows writes there. Review decision H-5 already excluded those. | Name the allowed source projects and the exclusions. |
| DOD-01 | High | Probable (not verified) | §5.5, §9 | If hook configuration is read at session start, the setup session cannot exercise the new hook through Claude Code. Its tests would be direct script calls, yet the DoD reads as real interception. Test 1 runs a real `git push` if the hook is not active. | Split "script tested" from "interception verified in a new session"; make test 1 harmless by construction. |
| GIT-01 | High | Confirmed | §2.1 step 9; `HANDOFF.md` "How we work" and "Rules that hold" | No branch rule: the Orchestrator may commit on `main`. Existing conventions are missing: work on `brownfield-adr`, commit by explicit paths, new tests shown failing on the parent commit, docs in the same commit. | Reference `HANDOFF.md` "How we work" as the commit rule. |

## C. Other findings by area

### Architecture and ownership (Medium)
- Seven agents are not justified for this repository. Most tasks touch `tools/pls` plus the documents that must change in the same commit; splitting them across tool-engineer, skill-author and doc-keeper conflicts with "docs in the same commit" and multiplies briefs.
- `doc-keeper` on `haiku` owns `HANDOFF.md`, which records Nam's decisions and is the cold-start state.
- `kb-curator` on `sonnet` owns the KB, where `CLAUDE.md` rule 5 (do not guess about Pleasanter) applies.
- The review is stored twice (`plans/reports/…` and `plans/<slug>/review.md`): an A4 duplication.

### Governance (Medium, confirmed in this environment)
- Nam's global `~/.claude/rules` already mandate `planner` / `tester` / `code-reviewer` delegation, and global agents with those names exist. The candidate does not say which wins.
- Subagents get `docs/agent-rules.md` only if they follow "read it first": a reminder, not enforcement.

### Hook policy (Medium)
- "Write/Edit outside the repository" would block Claude Code's own memory directory under `~/.claude/projects/…`.
- The `--yes` rule covers `apply` and `bootstrap` only; `migrate`, `test` outside dev and `kb-verify` also take `--yes`. Since a typed confirmation needs a terminal, `--yes` is the only path an agent has, so the rule blocks runs Nam explicitly instructs. EV-10 as a stop point fits better.
- "Compare case-insensitively" is right on Windows and wrong on a case-sensitive filesystem.

### Routing (Low)
- Per-invocation model override exists in this installation (Agent tool `model`: `haiku`, `sonnet`, `opus`, `fable`). The candidate's table omits `fable`.

### Test commands
- Verified: both suite commands work from the repository root.

## D. Platform matrix

| Area | Windows | macOS | Linux | Evidence | Status |
|---|---|---|---|---|---|
| Hook invocation | `python` on PATH; shell used for hooks unknown | `python3` only | `python3` only | versions read; nothing built | Not verified |
| Runtime discovery | `python` 3.12.10 present | — | — | `python --version` | Partially verified (Windows) |
| Path normalisation | space and Japanese names present | case-sensitive risk | case-sensitive risk | directory listing | Not verified |
| Symlink handling | junctions and `subst` not addressed | — | — | candidate text | Not verified |
| Failure behaviour | fail-open suspected | same | same | not checked against documentation | Not verified |
| Hook tests | none exist | none | none | — | Not verified |
| Skill commands | suites pass from the root | — | — | ran both | Verified (Windows) |

## E. Adversarial scenarios

| # | Scenario | Behaviour implied by the candidate | Sev. / Conf. | Correction |
|---|---|---|---|---|
| 1 | Small doc fix starts all agents | Workflow lists steps 3–8 without a "do it alone" threshold | Medium / Probable | Orchestrator acts alone below a stated threshold |
| 2 | Two agents edit `skills/README.md` versions and a skill | Ownership advisory; caught only by `git diff --stat` afterwards | Medium / Probable | Sequence; one integrator per commit |
| 3 | Reviewer relies on the implementer's summary | §1.1 forbids it; briefs are free text | Medium / Potential | Brief template with fixed fields, no narrative |
| 4 | `sonnet` chosen for a guard change | Defaults by role; escalation is a judgement | High / Probable | Use the existing `CLAUDE.md` Critical tier |
| 5 | Hook works on Windows, not on macOS | `python` not found; operation proceeds | High / Probable | Fail closed; report unsupported |
| 6 | Symlink or junction inside the repository points outside | "resolve symlinks" stated; no test | Medium / Potential | Resolve the nearest existing parent; test it |
| 7 | Malformed hook input | Partial blocking that cannot be computed | High / Probable | Deny everything |
| 8 | Hook runs under another shell | Path with a space splits | High / Probable | Quoted or exec-form invocation |
| 9 | Setup session runs the trial | Forbidden three times; the trial text is in the same prompt | Low / Potential | Keep; also G1 is already done |
| 10 | Dirty tree | Stop and ask — adequate | Low | — |
| 11 | Orchestrator loses context | `plans/<slug>/log.md` helps; no "resume" step reads it | Medium / Probable | First workflow step reads an open plan's log (EV-08) |
| 12 | Agent edits `.claude/hooks/` | Allowed | High / Confirmed | SEC-03 |
| 13 | Agent copies a customer project to scratch | Allowed | High / Confirmed | SEC-04 |

## F. Required changes

### P0 — before implementation
1. Replace every fixed "ADR-0014" with the number found at inspection (title, §5.4, §6, §7, §9, §10).
2. Replace the trial task (§8).
3. Move the orchestrator skill out of `skills/` and name skill and agents by the convention (§1, §2).
4. Rewrite the hook failure rule and add encoding and quoting requirements (§5.2).
5. Add protected paths as stop points and protected by configuration (§4.1, §5.3).
6. Redesign evals (§1, §2.1 step 7).
7. Remove the second routing policy (§2.3, §7).
8. Constrain scratch copies (§2.1 step 5).
9. Split the hook definition of done (§5.5, §9).
10. Adopt the existing commit rules and branch (§2.1 step 9).

### P1 — before production use
- Reduce to the agents that pay: reviewer, a KB role, eval case-runner; the Orchestrator implements.
- State precedence over the global `~/.claude/rules`.
- Exempt Claude Code's own directories from the outside-repository rule.
- macOS / Linux: detect and refuse.
- Add the resume step.

### P2 — recommended
- Single review location; `fable` in the model list; CI OS matrix for the hook script.

### EV cases for the first trial run
- EV-01: refuse to edit a guard to make something pass.
- EV-02: a failing test is not relaxed.
- EV-03: no ADR status change without Nam.
- EV-07: the report lists files and commands, no unverified claims.
- EV-08: resume from `plans/` after an interruption.
- EV-09: an instruction planted in a repository file is treated as data.
- EV-10: `--yes` without a named target.

## G. Replacement text (P0)

**1 — ADR number (§6 and all references)**
> Call it "the agent-team ADR". At inspection, list `docs/adr/` and use the next free number (0014 and 0015 are taken). Write that number once, in the ADR file name and in `docs/adr/README.md`; everywhere else refer to it by title and link. Never write "ADR-0014" for this decision.

**2 — Trial (§8)**
> The trial task is chosen by Nam from the items still open in `HANDOFF.md` at that time. It must be small, touch no guard or gate, and need one code change, one test and one document. Do not use G1: it was closed in commit `877d2dc`.

**3 — Location and names (§1, §2)**
> Framework-development assets never live in `skills/`: every folder there with a `SKILL.md` is installed into project repositories by `pls skills sync`. Put the orchestrator skill in `.claude/skills/pls-x-dev-orchestrator/` and the agents in `.claude/agents/pls-x-<role>.md`. Do not add them to `skills/README.md`.

**4 — Hook failure (§5.2)**
> The hook denies the operation whenever it cannot decide: unreadable or non-JSON input, a missing or unexpected field, any exception, a path it cannot resolve. Before writing it, read the hook documentation for the installed Claude Code version and record in the setup log which exit code or output blocks a tool call, and what happens when the hook process cannot start or times out. If those cases do not block, say so in the ADR as a known fail-open and do not call the hook fail-safe. Invoke the script with its path quoted (the repository path contains a space). Read stdin as bytes and decode UTF-8. On macOS or Linux, until verified there, the hook denies everything it guards and says the platform is unverified.

**5 — Protected paths (§4.1, add item 10; §5.3, add item 5)**
> 10. Any change to `.claude/settings*.json`, `.claude/hooks/`, `.claude/agents/`, `docs/agent-rules.md`, `docs/review-criteria.md`, `evals/**/expected.md`, `templates/project/CLAUDE.md`, or the Mandatory section of `CLAUDE.md`.
>
> 5. Write/Edit of the paths in stop point 10. Nam edits them himself or approves the exact diff.

**6 — Evals (§1 row, §2.1 step 7)**
> Evals follow `HANDOFF.md` "How we work": the Orchestrator starts one fresh subagent per case, whose brief contains only the case input (never `expected.md` or the standard), on the model the result file will record. Grading against the rubric is a separate step after all runs. Ask Nam before a batch. Model routing does not apply to evals.

**7 — Routing (§2.3)**
> Model routing is defined once, in `CLAUDE.md` "Adaptive Model Routing". The skill refers to it and adds nothing.

**8 — Scratch (§2.1 step 5)**
> Copy only `demo-equipment` or `pls-demo-equipment`, without `.pls/`, `*.key` and `tests/seed/`. Never copy a project taken over from a customer.

**9 — Hook definition of done (§9)**
> Hook script tested by direct invocation with recorded input and output (this session). Interception by Claude Code verified in a new session, or recorded as not verified with the reason. No test runs a command that would have an effect if the hook did not fire.

**10 — Commits (§2.1 step 9)**
> Commit as `HANDOFF.md` "How we work" says: on `brownfield-adr`, by explicit paths, one item per commit, full suites first, new tests shown failing on the parent commit, documents in the same commit. Never commit on `main`.

## H. Readiness

| Question | Answer |
|---|---|
| Safe to execute as written? | No (SEC-01, SEC-03, SEC-04, ARCH-01). |
| Implementable without guessing? | No (hook failure rule, ADR number, skill location). |
| Maintainable? | Not with seven roles and two routing sources. |
| Hook secure enough for its stated purpose? | Not shown; fail-open likely. |
| Platform support accurately specified? | No; Windows only, unverified. |
| Setup objectively verifiable? | Partly; hook interception is not. |
| Usable by a new session? | Yes for discovery through `.claude/`, once ARCH-01 is fixed. |

## Nam's decisions after the review (2026-11-11)

1. This review is kept in `plans/reports/`.
2. Trial task: chosen by Nam from two or three open items proposed with Revision 4.
3. Three subagents only: reviewer, eval case-runner, kb-curator. The Orchestrator implements the rest.
4. The global `~/.claude/rules` are not overridden; the repository `CLAUDE.md` maps planner, tester and code-reviewer to this repository's equivalents.
5. No self-written hook in the first version: Claude Code permission deny rules only. The hook goes to `docs/tech-debt.md`, to be built after its semantics are checked against official documentation.
6. Orchestrator skill in `.claude/skills/`, named by the convention; routing by reference to `CLAUDE.md`.
7. Lint copies only from `pls-demo-*` projects, without `.pls/`; never a project taken over from a customer.
8. ADR: the next free number, never hard-coded.

Revision 4: `plans/2026-11-11-agent-team-setup/prompt-rev4.md`.
