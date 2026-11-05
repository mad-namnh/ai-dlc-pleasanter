# Gates — what to present, what to record

At a gate, send the person **one short message**:
- what was done;
- the evidence (file paths and the key numbers);
- the decisions or assumptions they are approving (list them);
- the question: approve / approve with changes / reject.

Then wait. Do not continue to the next phase in the same turn.

When they decide, record it exactly as said, with the approver's name and the date. Then commit (`docs(gN): …`). For "approve with changes", make the changes first, show them, and ask again if they alter what was approved.

| Gate | Present | Approver (demo stage: the project owner for all) | Record in |
|---|---|---|---|
| **G1** requirements | the REQ table (ID, title, type, derived?); the open questions with their `[assumed]` defaults; anything out of scope | customer owner + MADLAB PM | `Status` line of each `REQ-*.md` (`G1 approved (<name>, <date>)`, or `withdrawn at G1`); header and table in `requirements/index.md`; decisions on questions in the questions table |
| **G2** design | the design table (element → setting → REQ, ladder rung); rejected alternatives; classification (config-only / data-impacting / permission-impacting); probes run and their results; slots allocated; open points | MADLAB tech lead | `Status` line of `DES-*.md`; slot ledger entries `allocated` |
| **G3** build verified | `pls lint` = 0 issues; `pls coverage` = 100 % in scope; test results (pass / pass-api-only, the result file); round trip 0 on dev; open items | MADLAB tech lead | `releases/<release>/g3-verification.md` (`Status: G3 approved (<name>, <date>)`) and `approvals.md` |
| **G4** release | the Japanese diff report summary; classification; target; for stg/prod: the plan (sites, order, rollback), drift result and migrations; for dev: drift 0 since the tests | customer owner + operator | `releases/<release>/approvals.md`; after apply/verification: `Released:` line in each REQ, `released (<release>)` in `index.md` |

## Customer questions at G1

The approver decides at G1 how open questions are handled:
- **Send them to the customer first:** G1 waits for the answers.
- **Approve with the `[assumed]` defaults:** record "Qn as assumed".

In stage `demo`, propose the second option. Record the choice in `requirements/index.md`.

## `approvals.md` shape

```markdown
# <release> — approvals

| Gate | Decision | Approver | Date | Evidence |
|---|---|---|---|---|
| G1 | REQ-001…007 approved (Q1–Q10 as assumed) | <name> | YYYY-MM-DD | `requirements/index.md` |
| G2 | DES-001 approved | <name> | YYYY-MM-DD | `design/decisions/DES-001-….md` |
| G3 | approved | <name> | YYYY-MM-DD | `g3-verification.md` |
| G4 | approved — <target>, round trip 0 | <name> | YYYY-MM-DD | `diff-report.md` |
```

## Reject or loop back

- A rejection at G1 or G2 returns to that phase. Change only what was rejected.
- A failure in P4 that changes a requirement or the design reopens G1 or G2 first:
  - write the reason in the REQ/DES `Status` line (`G2 reopened: …`);
  - get the gate approved again;
  - only then continue.
