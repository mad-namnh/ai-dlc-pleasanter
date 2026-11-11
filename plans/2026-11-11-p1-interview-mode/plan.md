# Plan — interview mode for pls-p1-requirements-analyst

- **Date / branch / parent commit:** 2026-11-11 / `brownfield-adr` / `8fbb8bb`
- **Objective:** When the input of P1 is a rough idea instead of a specification, the skill interviews the person first and writes requirements only from the answers. An eval case shows it.
- **Tier:** Standard — skill text, a new reference, a new eval case and documents. No code of `pls`, no guard, gate or permission.
- **Task statement:** Nam's nine points of 2026-11-11 (reference file, verbatim record under `requirements/sources/`, every REQ points to its source answer, open questions first, AI proposals marked, coverage checklist ordered by design impact, questions grounded in the KB, at most 3 rounds of 5–8 questions with a confirmed summary, the person's language, an eval case with a person-role subagent and a rubric).
- **Scope:**
  - `skills/pls-p1-requirements-analyst/references/interview.md` (new); `SKILL.md`: when to use it, the output, a checklist line, the description; `references/req-template.md`: the Source line; version 0.5 in `skills/README.md`.
  - `docs/architecture.md` P1: the interview and its record.
  - Eval case `evals/pls-p1-requirements-analyst/case-003-interview-rough-idea/`: `input.md`, `interviewee.md` (script of the person-role subagent); `evals/README.md`: how a case with a person in the loop is run.
  - `expected.md` of the case is a protected path: proposed as `proposed-case-003-expected-md.patch` in this folder for Nam to apply.
- **Out of scope:** `pls-x-lifecycle` (its P1 step already hands the request to this skill; not changed, so its evals are not affected); running the eval (needs the rubric applied by Nam and his go-ahead: several subagent calls); re-running P1 cases 001 and 002 on version 0.5 (a batch: Nam is asked); a fourth kind of subagent in `.claude/agents/` for the person role (protected path; the role is played by a general-purpose subagent briefed with `interviewee.md`).
- **Files:** as in Scope, plus `HANDOFF.md` and this folder.
- **Invariants and ADRs touched:** I4 (the person's confirmation of a summary is not G1; an unaccepted proposal is never a requirement), I8 (a requirement traces to its source answer). No ADR: the interview is a way of working inside phase P1 and adds no artifact kind beyond a source file.
- **Stop points expected:** item 3 (protected path `evals/**/expected.md`) — handled by the patch procedure.
- **Acceptance criteria:**
  1. `references/interview.md` exists; `SKILL.md` says when interview mode is used and when not; the version is bumped in `skills/README.md`.
  2. The skill requires the verbatim record at `requirements/sources/<date>-interview-<slug>.md`, a source answer on every REQ, and turns anything without a source answer into an assumption / open question.
  3. Open questions come first, choices only close a point; AI proposals are recorded apart, with the person's reply; only an explicit acceptance makes one a source.
  4. The coverage checklist has the eight areas and an order by design impact.
  5. Questions are grounded in the KB: what the KB says Pleasanter cannot do becomes a constraint; what the KB does not cover is marked unverified, never guessed (CLAUDE.md Mandatory 5).
  6. At most 3 rounds of 5–8 questions, a summary the person confirms, the rest as `[assumed]` questions, then the normal P1 procedure and a stop at G1.
  7. The interview is in the person's language; end-user labels and messages stay Japanese; repository documents stay English.
  8. The eval case exists with an input, a fixed script for the person-role subagent that the agent under test never sees, and a rubric (as a patch) that checks: every REQ has a source answer; no REQ rests only on an unconfirmed suggestion of the AI.
  9. No example in the skill gives away the eval case (skills/README.md rule 4).
  10. Both suites pass (the skills are copied by `pls init` / `skills sync`, and the suite checks that).
- **Tests:** both framework suites. No new unit test: nothing executable changed. The behaviour is measured by eval case 003, which is not run in this task.
- **Subagents planned:** `pls-x-reviewer` on `sonnet`, effort `medium`.
- **Documents to update in the same commit:** `skills/README.md`, `docs/architecture.md`, `evals/README.md`, `HANDOFF.md`.
