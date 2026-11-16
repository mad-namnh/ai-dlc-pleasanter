# ADR-0030: Skill evals with repeated runs, a no-skill baseline, scope and selection cases and recorded cost

- **Status:** Accepted (Nam, 2026-11-16: "chap nhan" before review round 2, and "ADR-0030 chap nhan" for the text revised after it) — option B; partly built 2026-11-17 (Nam: "Ghi 'partly built'"): `evals/README.md`, HANDOFF evals line, test `test_skills_hold_no_eval_data.py`; patches for protected paths (brief form, runner, `docs/agent-rules.md`, orchestrator skill) pending Nam in `plans/2026-11-17-adr-0030-build/`; scope / selection cases not built (later task)
- **Date:** 2026-11-16
- **Deciders:** Nam
- **Related:** I6, I9 (`docs/architecture.md` §2); ADR-0016 (agent team, eval case-runner); ADR-0022 (skills installed into project repositories); **amends ADR-0029** (its eval approval: what it covers under this ADR, Consequences); `evals/README.md`; HANDOFF "How we work" (evals line); TD-37 (skills without a current-version eval); plan `plans/2026-11-16-skillevaluator-adoption-analysis/` (risk analysis, Tier 1 trial, review)

## Context

A skill eval today is one blind run of one case by `pls-x-eval-case-runner`, graded by hand against `expected.md` (Must / Must not). Cases per skill on 2026-11-16: lifecycle 8, P1 3, P2 2, P4 2, P5 2, every other skill with cases 1 (the KB has none). This leaves three questions without an answer:

1. **Is a pass reliable?** A model answers differently from run to run. P1 case 001 on 0.6 missed the same rubric item in runs 1 and 3; that the miss was systematic was found only because the case happened to be run again (`skills/README.md`, P1 row).
2. **Does the skill add anything?** No run is made without the skill, so a skill whose procedure the model already follows by itself cannot be told from one that carries the result. Skill text costs tokens on every use and must be kept in step with the code (ADR-0029, Context point 2).
3. **Is the skill used only when it should be?** The cases test what a skill does once started; none tests a request the skill must leave alone, a request at the edge of its scope, or whether its description leads to it being chosen.

NVIDIA SkillEvaluator (`https://github.com/NVIDIA/SkillEvaluator`, 0.9.0, read 2026-11-16) answers these with repeated attempts (pass@k), a with-skill / without-skill comparison ("skill lift") and activation buckets (explicit, implicit, negative, edge). Its runtime (Harbor sandbox, Docker, LLM judge, a provider key) does not fit our evals: the person-role relay of interview cases, the relay of local `pls` commands, grading against a hand-written rubric, and the rule that evals run on the model their result records. A keyless trial of its Tier 1 checks on `skills/` found one candidate real issue and otherwise generic or false findings (`plans/2026-11-16-skillevaluator-adoption-analysis/trial-report.md`). This ADR takes the **method**, not the tool.

Its dataset layout puts `evals/` with expected outputs **inside** the skill folder. In this framework skill folders are installed into customer project repositories (ADR-0022) and are read by the runner under test; a rubric there would break blindness and the rule "never put a case's answer into a skill" (`skills/README.md`).

Nam's choices (2026-11-16, AskUserQuestion, verbatim, with an English gloss): baseline "Bỏ skill, giữ KB (Recommended)" (*drop the skill, keep the KB*); repeats "k=3 cho P1, P2, lifecycle (Recommended)" (*k = 3 for P1, P2, lifecycle*); trial "quality-check + pii-scan (Recommended)"; order "Thử trước, ADR sau (Recommended)" (*trial first, ADR after*). On the decision rule and cost recording: "ok dua vao ADR luon, viet ADR di" (*ok, put it in the ADR, write the ADR*).

## Options

### Option A — Keep one run per case
- Pros: no extra cost; no change to the eval contract.
- Cons: the three questions above stay open; a flaky pass counts as a pass.

### Option B — Repeats, a no-skill baseline on demand, scope and selection cases, recorded cost, a decision rule (recommended)
Parts 1–6 below, run by the existing case-runner with changed briefs.
- Pros: answers the three questions with the tools we have; keeps blindness, the relays and hand grading; cost is bounded (repeats only for three skills, baseline only when triggered).
- Cons: about three times the eval runs for P1, P2 and lifecycle; the separation of runs and arms rests on instructions and a self-reported file list, as blindness already does; with few cases the numbers stay indicative; selection by the real harness is not measured.

### Option C — Adopt SkillEvaluator Tier 3 (Harbor, Docker, LLM judge)
- Pros: automated, sandboxed (a real isolation of the arms), standard metrics.
- Cons: no person-role or `pls` relay; an LLM judge replaces our graded rubric; a provider key and skill text leave the machine; Docker on the operator's machine; a third-party "Experimental" dependency in the evaluation contract.

## Decision

Option B.

### 1. Repeated runs
- `pls-p1-requirements-analyst`, `pls-p2-solution-designer` and `pls-x-lifecycle`: every case is run **k = 3** times, each in a fresh case-runner and a fresh scratch folder. Other skills: k = 1 (more on Nam's request).
- **Runs do not see each other.** A run may open no folder under `../_agent-scratch/` other than its own. Before the next run of the same case starts, the folders of its earlier runs (both arms) are moved to `../_agent-scratch-held/` and moved back after grading; this holding place is the one exception to the single scratch place of `docs/agent-rules.md` §3 and ADR-0016, and the runner is never told about it. The opened-files check of Part 2 applies to every run.
- A run is one runner call (resumed after each relayed command or message); a case at k = 3 is three calls. `docs/agent-rules.md` §4 and §5 ("one call per case") change accordingly (Consequences).
- The result file records each run's grade and the count `x / k`. A case passes on a skill version only with **k / k**. A run that fails is a finding: the failing rubric items are named, and the skill, the case input or the rubric is changed through the usual path before the version is called passed.
- Interview cases (an `interviewee.md` in the case folder) are run k times like any other; each run has its own person-role subagent and transcript.

### 2. No-skill baseline arm
- **Definition:** the same case input, the same model and the same scratch setup except the skill: the brief names no skill; in a scratch copy of a project, every folder under `.claude/skills/` other than `pls-kb-pleasanter` is removed before the run (and the result says so).
- **Allow-list.** A baseline run may open only: its own scratch folder; its case `input.md`; the framework's `skills/pls-kb-pleasanter/`, `CLAUDE.md`, `docs/` except `docs/review-criteria.md`, and `templates/`. Any other path — another run's folder, `skills/README.md` (its rows summarise each skill's procedure), any other skill, and copies of skills in sibling project repositories — voids the run.
- **What differs between the arms:** the skill under test **and everything it references** (other skills' references such as `pls-x-lifecycle/references/kb-gaps.md`, and generated references such as P2's `impact-rules.md` of ADR-0029 Part A). What both arms share: the KB, including its design-rule rows, and the framework's rule files the runner reads by its definition (`CLAUDE.md`, `docs/agent-rules.md`) or may read (`docs/`, `templates/`). Lift therefore measures the skill with its references against a model that already has the framework's rules and Pleasanter knowledge.
- The runner lists every file it opened; a run that opened a path outside its allow-list is void and is rerun. The result states that the separation rests on the brief and on that list (as blindness does, `docs/agent-rules.md` §4).
- **When:** not on every eval. (a) Once per skill, to establish its lift on its current cases; (b) before trimming or removing skill text under Part 5; (c) on Nam's request. The baseline arm uses the same k as the skill's with-skill arm.
- **Lift** per case = Must items passed with the skill − Must items passed without it, each averaged over the k runs, reported together with the Must-not hits of each arm (averaged the same way). Interview cases get a baseline only when Nam asks.

### 3. Scope and selection cases
Each skill gets, over time, besides its normal cases:
- **Scope cases** (the skill is loaded, as in a normal case): *negative* — a request outside the skill's scope; the rubric expects the skill not to act (lifecycle: not to route it into P1–P6) and to say where it belongs; *edge* — a request at the boundary, with the expected stop, refusal or route written in the rubric before any run. They show what a skill does with a request it has been given; they do **not** show whether the harness would pick the skill.
- **Selection cases** (approximation of triggering): the runner receives the request and only the `name` and `description` of every framework skill (copied into the brief), no skill body, and answers which skill it would use, or none, and why. It may open only its own scratch folder and its case `input.md`; any other path voids the run. The rubric names the expected skill or "none". This tests whether the descriptions separate the skills; it is not Claude Code's own selection (open question).
New rubrics are protected paths: the agent proposes them as patches, Nam applies them (`docs/agent-rules.md` stop point 3). First targets: lifecycle (routing), P6 and onboarding (broad descriptions without negative triggers, trial report).

### 4. Cost recorded per run
Every run, in both arms, records the subagent's total tokens, tool calls and duration as the Agent tool's completion notice reports them (observed on 2026-11-16: `subagent_tokens`, `tool_uses`, `duration_ms`), and the count of `pls` commands relayed. A run resumed several times sums every completion notice of its runner; the person-role subagent of an interview case is recorded separately. A value the harness does not report is written "not reported", never estimated.

### 5. When the baseline does as well as the skill
"Does as well" means: on every case, averaged over the k runs, the baseline passes as many Must items **and** has no more Must-not hits than the skill. That alone does not justify removing skill text. In order:
1. **Check the evidence.** Do the cases exercise what the skill protects (gate stops, refusals, EV-01…EV-10 behaviours)? If not, add scope cases that do and run again. With fewer than 3 cases or a 1-item difference, record "no measured difference", not "no lift".
2. **Keep guard text.** Gate stops, refusals and safety rules stay in the skill even with zero measured lift. They leave skill text only when a deterministic check holds them (ADR-0029: `pls check`, hooks).
3. **Trim what the model does by itself.** Generic guidance with no lift on any case is removed or shortened; the trimmed version is evaluated (both arms) like any skill change. Generated references (ADR-0029 Part A) are never trimmed here: they change only through their generator and its sources.
4. **Remove a whole skill** only when all hold: it carries no guard text; no measured lift and no more Must-not hits in the baseline, over at least 3 cases at k = 3; the same on the weakest model the framework is meant to support (Nam names it); and the cost of Part 4 shows the baseline does not spend more (tokens, tool calls, relayed commands) to reach the result. Removal is Nam's decision.

### 6. Limits and layout
- Eval results are evidence for people. No pass count, lift or cost figure blocks a commit, a gate or a release (I6: deterministic checks decide). A result with fewer than 10 cases for the skill, or with no negative scope case, is labelled **provisional**.
- Cases and rubrics stay under `evals/<skill>/`. No eval dataset, rubric or expected output is placed inside `skills/` (no `evals.json`, `EVAL.md`, `expected.md` or `evals/` folder there); a test asserts it.
- SkillEvaluator is not a dependency. A later trial needs Nam's approval again.

## Consequences

- **Changes when accepted** (each in its own commit, with review):
  - `evals/README.md`: repeats and run separation, baseline arm and its scratch setup, scope and selection cases, cost columns, Part 5, the provisional label; result file template with `x / k`, per-run cost and the arm.
  - HANDOFF "How we work", evals line: k and the baseline.
  - Protected paths, as patches for Nam: `.claude/skills/pls-x-dev-orchestrator/references/eval-case-brief.md` (baseline and selection variants with their allow-lists; "list every file you opened"; no other run's folder; `skills/README.md` forbidden in **both** arms, because its rows describe what earlier runs missed — a blindness leak that exists today; cost lines), `.claude/agents/pls-x-eval-case-runner.md` (the allow-lists of baseline and selection runs), `docs/agent-rules.md` (§3 the holding place `../_agent-scratch-held/`; §4 and §5 "one call per run, k runs per case"), new `expected.md` files for scope and selection cases.
  - A test under `tools/pls/tests/` that fails when `skills/` holds an eval dataset or rubric file.
- **Cost:** with-skill runs of the current cases of P1, P2 and lifecycle go from 13 to 39 per full evaluation. The first baseline sweep (Part 2 a) is 36 runs for P1 (its two non-interview cases), P2 and lifecycle at k = 3, plus 9 for the other skills at k = 1 — 45 runs, once; later baselines only when triggered.
- **Amendment of ADR-0029:** ADR-0029's approval of the P1, P2 and lifecycle evals when their text changes covers, under this ADR, the k = 3 with-skill runs of their cases. Baseline runs and selection cases are not covered: each batch of them is asked of Nam with its k and number of runs.
- **Easier:** telling a flaky pass from a stable one; deciding with numbers whether skill text earns its tokens; seeing whether descriptions separate the skills.
- **Unchanged:** blindness rules, person-role and `pls` relays, hand grading, the model rule for evals (both arms and every run on the model the result records), ADR-0029's rule that a generated reference needs no eval.
- **Follow-up outside this ADR:** the description of `pls-p3-config-builder` contains `<site>`; whether the Agent Skills specification forbids that in a description is checked before any change (trial report).

## Open questions

- [ ] Does a subagent started with the Agent tool also receive the repository `CLAUDE.md` from the harness? The runner reads it by its definition in both arms anyway, so this changes only what the result states, not the design — *Claude Code documentation, before the first baseline run*
- [ ] Can the Orchestrator check a run's opened files from its transcript instead of trusting the runner's list? — *Claude Code documentation or the first runs*
- [ ] How close selection cases come to Claude Code's own choice of a skill from its description, and whether that choice can be observed directly — *Claude Code documentation*
- [ ] The weakest model the framework is meant to support (Part 5 step 4) — *Nam, after evals on Sonnet* (Nam 2026-11-16: "để câu hỏi mở vì cần đánh giá thêm" — *leave it open, needs more evaluation*). Facts: `templates/project/CLAUDE.md` sets no model, so projects may run any model today; every skill eval so far ran on Opus; the write path is held by code whatever the model (ADR-0029 Context). Options analysed: A — Opus / Fable only (cheapest evals; needs a model rule in the project template); B — per phase: Opus for P2, P3, P5 and lifecycle (the Critical tier of the framework's own routing: permissions, migrations, data integrity), Sonnet as the floor for P1, P4, P6, onboarding, spec-recovery (lifecycle then asks the person to switch `/model`) — recommended by the agent; C — Sonnet as the floor for every skill; D — Haiku (not recommended). Whatever is chosen, support is "intended" until an eval on that model passes.
- [ ] Whether interview cases should get a baseline by default — *Nam, after the first baselines of non-interview cases*
- [x] Which cost figures the Agent tool reports for a subagent run — total tokens, tool uses and duration: the completion notices of the two review subagents of this ADR on 2026-11-16 carried `subagent_tokens`, `tool_uses`, `duration_ms` (figures in the plan folder's `log.md`)
