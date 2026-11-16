# Review round 1 — console spec and ADRs (working tree against af17854)

Reviewer: `pls-x-reviewer`, model opus, effort high. Verdict: **accept with fixes**. `git status` identical before and after the call.

## Findings

- **H-1 (High)** — a segment can still forge guard inputs, so ADR-0029:48, spec:110 and ADR-0028:57 claim more than the controls give. Deny list misses `--yes` (pls.py:3630-3651, 3762, 3766), `pls refs --keep/--ref --by --quote` (pls.py:3664-3672, TB-2), non-dev `--env`, Edit/Write on `gates/**` and `environments.json`. A hand-written `dev-writes on` record counts (pls_profile_records.py:220-224; TB-3); the role comes from `environments.json` (pls_http.py:138-143). Check 2 omits `environments.json` and `gates/` and runs only before the segment. Scenario: a worker machine with a writable stg connection; the session relabels stg as dev, writes role and `dev-writes` records, and `pls apply` writes to stg. Fix: refuse to start with a writable non-dev connection; deny `--yes`, non-dev `--env`, `refs --keep/--ref`, edits of `gates/**`, `environments.json`, `.pls/**`, `.claude/**`, `CLAUDE.md`, `pls.py`; add `environments.json` and `gates/**` to check 2 and repeat it on the pushed result; word the claims as guardrails linked to option C.
- **M-1** — approver set and FR-18 scope changeable by CR-branch content (`pls gate` reads the checked-out branch's profile, pls_gate.py:86-96; latest Approvers record wins, pls_profile_records.py:101-119). Fix: profile from main at the CR's base commit; FR-18 covers all of `gates/**`.
- **M-2** — checks by commit author are forgeable. Fix: the console identifies its own records from its store (path + content hash); signed commits / host push identity optional.
- **M-3** — the console would run the branch's launcher `pls.py` (ADR-0022). Fix: the console runs its own pinned framework `pls`.
- **M-4** — ADR-0028 drops Q6's "confirmations"; `principals --create`, `test-users`, `kb-verify` keep a typed confirmation on dev (pls.py:2705, 2777, 3353; refuse without a terminal, 2873-2876). Fix: define how a person's confirmation is given (never a session's `--yes`), or "engineer runs it in a terminal" as a resolution; raise the departure from Q6.
- **M-5** — "unfinished" CR undefined (no Released / Merged end state); TB-14 tenant resources, `${site:x}` links and customer edits on stg missing from spec §11.
- **Low:** L-1 traceability of NF-08, NF-09 (discovery §6 does not say it), FR-06 and FR-14 self-referential; L-2 standing permission is per project and environment, not per machine; L-3 architecture §7.5 vs ADR-0026 "once accepted"; L-4 ADR-0029 amends ADR-0022 (FC-4) but lists it only as related; L-5 no transitions out of Blocked / Failed, `project_id` readiness (Q7) missing, G1–G4 → G1–G3 change not noted; L-6 ADR-0027 open question 2 vs FR-18; L-7 no structured source of designed sites at G2.

## Not verified by the reviewer

External Claude Code docs (no web tool); whether user / local Claude settings add allow rules to the worker's permission set; suite on Python 3.10; H-1 end to end.

## Disposition

Pending — Nam stopped commit 2 (2026-11-13) and asked to move the files to a new repository; fixes to be applied there.
