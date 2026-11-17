# Review

## Round 1 — pls-x-reviewer, opus, effort high (Critical: ADR text)
Verdict: accept with fixes; no Critical / High. git status before / after: unchanged.

| # | Sev | Finding | Disposition |
|---|---|---|---|
| F1 | Medium | Arms now also differ by the framework `docs/`; ADR-0030 Part 2 and `evals/README.md` lift line still said only the skill differs | Fixed in both: the arms differ by the skill with its references **and** the framework `docs/`; lift measures both. Whether to keep the with-skill arm out of `docs/` too → open question for Nam. |
| F2 | Low/Med | "what a customer project gives it" untrue: the framework `CLAUDE.md` stays allowed but a customer project has only the template's | Fixed: the sentence now says a customer project has neither; whether the baseline keeps `CLAUDE.md` → open question for Nam. |
| F3 | Low | `CLAUDE.md` points to `docs/architecture.md`; following it voids a baseline run | Fixed in the brief patch: pointers to `docs/` are not followed. |
| F4 | Low | Patch without a reason header (agent-rules) | Fixed: `Reason:` paragraph before the diff; `git apply --check` clean. |
| F5 | Low | No rule that baseline runs wait for the patch | Fixed in `evals/README.md`: no baseline run before it is applied. |
| F6 | Low | Accepted ADR amended in place | Precedent ADR-0004 (`cfb0e21`); Nam's words recorded; Nam is asked to confirm the amended text in the report. |
| F7 | Low | Haiku: no follow-up item; alias not verified | ADR open question now says a Haiku run uses `model: haiku` and the result records the model the run reports; no tech-debt row (`docs/tech-debt.md` carries other uncommitted work; the eval itself waits for a removal question). |
