# Plan — P2 evals (cases 001, 002) on pls-p2-solution-designer 0.7

- Task (Nam, 2026-11-11): "theo huong so 1" — run the P2 eval cases on the current version (last eval: 0.4).
- Scratch: ../_agent-scratch/p2-case001-v07-run1 (P1 case 001 base + REQ-001..004/index/source from pls-demo-inquiry 539b61f, source note reworded without "slice"), ../_agent-scratch/p2-case002-v07-run1 (P1 case 002 base re-unpacked with fixed pls + requirements at 3cf2c45 + config/responses and environments.json at 021a0d0; KB copy without D19/D20 rows, fact 11, and the D19 history sentence of the probe rule, as the case prescribes). Both: skills P2 0.7 + KB 0.15, pls copy in .pls-fw/ with the pls init launcher (offline commands only).
- Two blind pls-x-eval-case-runner calls (opus) in parallel; grade each against expected.md; results; README/HANDOFF; commit.
