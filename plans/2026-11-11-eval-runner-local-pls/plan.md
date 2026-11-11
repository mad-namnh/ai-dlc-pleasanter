# Plan — eval runner may use local pls; P2 case 002 input

- Task (Nam, 2026-11-11): "1. co, viet patch, 2. sua input.md".
- Tier: Standard (eval method; no permission granted — the runner keeps its tools). Review: pls-x-reviewer.
- (1) Proposed patch (protected paths, Nam applies): runner definition + eval-case brief form — `COMMAND TO RUN:` relay of local-only pls commands; no Bash (docs: tools takes bare names; deny rules are no security boundary; TD-21 hook missing). evals/README.md: Orchestrator-side allowlist and relay rules.
- (2) evals/pls-p2-solution-designer/case-002 input.md: full KB; history of the D19/D20 removal.

## Acceptance criteria
1. Patch passes `git apply --check`; reason at the top; no tool added to the runner.
2. The local-only list is the same in the patch and in evals/README.md, and holds only commands that read or write local files (no HTTP, no decision records).
3. README says how the Orchestrator checks, runs, refuses and records commands.
4. case-002 input.md no longer asks for a KB without D19/D20 and says why; expected.md unchanged and still consistent.
