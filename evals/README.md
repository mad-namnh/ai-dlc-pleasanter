# Evals

Each skill has cases built from real work (slices). A case is:

- `input.md` — what the skill receives (request, current configuration summary, approved inputs)
- `expected.md` — a **rubric**: must-have properties (pass/fail) and anti-patterns (fail if present). Not a golden text — wording may differ.

## Running (v0.1, manual)

1. Create a scratch project repository (copy of `pls-demo-inquiry` at the stated baseline, or the files listed in `input.md`).
2. Invoke the skill with the input.
3. Grade the output against `expected.md`: every **Must** item passes and no **Must not** item appears → case passes.
4. Record the result in `results/<skill>/<date>.md` with the model and skill version used.

### Cases with a person in the loop (interview)

A case folder that holds an `interviewee.md` needs someone to answer the skill's questions. The answers come from a second subagent that plays the person:

1. The agent under test gets `input.md` only, as always. It must not open `interviewee.md`, `expected.md` or the `plans/` folder, where a proposed rubric may lie (name them in its brief).
2. The person-role subagent gets `interviewee.md` only — not the skill, not `input.md`, not the rubric.
3. Whoever runs the case relays: each message of the agent under test that ends with questions goes to the person-role subagent **unchanged**, and its reply goes back **unchanged**. The relay adds nothing, answers nothing and corrects nothing.
   When the agent under test is a subagent, its turn ends with a report to whoever runs the case, not with a chat message: its brief tells it to put the complete message for the person at the end, under a line `MESSAGE TO <name>:`, and only that part is relayed. Its next message is the person's reply.
   Check every reply of the person-role subagent against `interviewee.md` before passing it on. A reply that leaves the script (a fact given away before it is asked for, an invented fact) is not delivered: tell the role-player which part of the script it broke, take its new reply, and record both replies and the correction in the transcript and the result.
4. Keep the full transcript (both sides, in order) with the result; the rubric is graded against the files **and** the transcript.
5. The result file records both models.

Automated grading is future work (tech debt). Add a case whenever a slice or an incident reveals a behaviour the skill must keep (I9).
