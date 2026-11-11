# Review — eval runner local pls (patch) and P2 case 002 input

- **Reviewer:** `pls-x-reviewer`, claude-sonnet-5-5, effort medium; working tree against `e421c4d`. Changed nothing in either round (git status before/after: `evals/README.md`, case-002 `input.md`, the plan folder).

## Round 1 — accept with fixes (1 High, 3 Medium, 1 Low)

| # | Sev | Finding | Disposition |
|---|---|---|---|
| F1 | High | The relay would run `python pls.py` from the scratch folder, where the runner can write: a runner-written `pls.py`, `json.py` or edited `tools/pls` copy would run with the relayer's shell, network and credentials | Fixed: the relayer runs the framework's own `tools/pls/pls.py` with `python -I`, cwd = scratch; no `pls` copy or launcher in scratch; the runner writes `pls <command> …` |
| F2 | Medium | Scratch layout underspecified; `skills check` breaks with a copied `pls` (FRAMEWORK = scratch) | Fixed by F1 (framework's own `pls.py`); checked: `skills check` from a scratch folder lists the real framework skills |
| F3 | Medium | `pack --out` and `canon`/`xref` write files; only redirection was restricted | Fixed: every path argument must resolve inside scratch |
| F4 | Low/Medium | `skills sync` shares the `skills` subcommand | Fixed: `skills sync` refused (README, patch) |
| F5 | Low | Orchestrator skill file not updated | No change: the brief form (in the patch) and `evals/README.md` carry the relay rule; the skill's step 9 points to both |

## Round 2 — accept with fixes (1 Medium, 2 Low)

| # | Sev | Finding | Disposition |
|---|---|---|---|
| N1 | Medium | `root()` walks up to the first `environments.json`; a scratch folder without one would act on a project above | Fixed: run only when the scratch folder itself holds `environments.json` |
| N2 | Low | `--site` is a path component (`xref --site ../../x`) | Fixed: `--site` a single name, no `/`, `\`, `..` |
| N3 | Low | Patch header cited a `review.md` that did not exist yet | Fixed: this file |

**Verified by the Orchestrator (reviewer could not, it would write files):** from `../_agent-scratch/p2-case002-v07-run1/`, `python -I "<framework>/tools/pls/pls.py"` ran `xref --site inquiries` (exit 0), `lint` (20 issues listed) and `skills check` (names framework skills not installed) — the framework's tool works with the scratch folder as cwd. `lint`'s node check compiles only (`vm.Script`, `pls_scripts.py` `NODE_CHECK`). HTTP is imported only by `adopt`, `sandbox`, `setup`, `principals` and the HTTP commands (`pls.py` 1534, 1986, 2329, 2429, 2459, 3275).

**Note on the P2 eval runs of 2026-11-11:** those scratch folders held a `pls` copy and launcher; the Orchestrator ran `python pls.py lint` there only before the runners started, never after they had written — no runner-written code was executed.
