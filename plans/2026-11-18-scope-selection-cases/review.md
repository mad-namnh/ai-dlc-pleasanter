# Review

## Round 1 — pls-x-reviewer, sonnet, effort medium (Standard)
Verdict: accept with fixes; no Critical / High. git status before / after the call: unchanged.

| # | Sev | Finding | Disposition |
|---|---|---|---|
| M1 | Medium | P6 002 Must 2 required the verbatim save and Sato — not in the P6 skill | Fixed: "routes out of P6 as a new request, not triaged"; verbatim save and G1 approver optional. |
| M2 | Medium | Lifecycle 009 expects a refusal the skill text does not state; "asks for files" debatable | Kept as a negative case (its purpose); `setup.md` says a failure means a missing rule in the skill. Must not narrowed to "opens files outside its scratch project, or claims to have fixed the macro". |
| M3 | Medium | Selection rubrics silent on answers naming several skills | Fixed: the one skill the runner says it would use decides; extra skills noted; several without a choice fails. |
| L1 | Low | Selection 011 sensitive to the lifecycle description | `setup.md` says such a failure is read as a description that claims too much. |
| L2 | Low | Selection 003 input echoed the onboarding description ("built without this framework") | Fixed: "an app another company built years ago". |
| L3 | Low | Onboarding 002 input: `pls init` and "No `pls`" | Fixed: "`pls` is not available in this session". |
| L4 | Low | "reason says it routes" subjective | Fixed: "its reason names `<skill>` as the next skill". |
