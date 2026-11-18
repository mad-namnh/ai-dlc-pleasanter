# Review — TD-67 (pls-x-reviewer, opus, high)

## Round 1 — staged diff against 8d73ec2

Verdict: **accept with fixes**. Reviewer's git status before / after: identical (33 entries).

| # | Severity | Finding (reviewer) | Disposition |
|---|---|---|---|
| F1 | High | Baseline cut-off used the **latest** G2 decision: a DES approved again after P3's dev releases moved the baseline past them and hid the change (AC2) | Fixed: earliest approved G2 record per DES (latest must still be approved). Test `test_an_edited_design_needs_a_new_g2_and_a_new_g2_keeps_the_first_baseline` |
| F2 | High | The build was compared with the DES file as it is now; editing the DES after G2 silenced the check without a new G2 | Fixed: G2 approval binds each DES's sha256 (`bound_des`, LF line ends); edited → finding; a G2 record without the digest → finding (approve again). Finding texts and P3 / lifecycle text say an edited DES needs G2 again. ADR-0020 amended |
| F3 | Medium | `unverified` entries checked for shape only (any file, any `D<n>`) | Fixed: `probe` must be an entry of the framework KB probe index; `decision` must be a project file that names the key; invalid entries do not satisfy the scope part at G3. Limit stated: a probe id is not proof that it verifies that component |
| F4 | Medium | G3 record did not keep `--env`; nothing ties it to the release target | Fixed: G3 record keeps `env`; `release-plan` on a non-dev target refuses a G3 whose `env` differs (test) |
| F5 | Medium | Silent for a site never released on the target that no named DES mentions | Fixed: one finding per such site (fail closed; accept with a reason) |
| F6 | Low | Baseline test passed through the time filter only; "never a release the G3 names" untested | Fixed: `test_the_baseline_is_never_a_release_the_g3_names` names a release applied before G2 |
| F7 | Low | Untested branches: `--des` without `--env`; G3 with only one of `--env` / `--item`; DES without / with unreadable front matter; G3 rejection; non-dict entry | Fixed: all covered |
| F8 | Low | Usage docstring, `g3-template.md`, P3 text on a new scope component; `check p1/p2` ignored `--env/--des` | Fixed: docstring, g3-template row (P4 0.10), P3 text; `check p1/p2` refuse `--env/--des` |

Reviewer could not verify: parent-commit failure and clean-tree suite (no worktree for agents) — run by Nam, see log.md.

## Round 2 — staged diff against 8d73ec2 (after the round-1 fixes)

Verdict: **accept with fixes**; no Critical or High. All eight round-1 dispositions confirmed done. Reviewer's git status before / after: identical.

| # | Severity | Finding (reviewer) | Disposition |
|---|---|---|---|
| R2-1 | Medium | G3 does not bind the build it compared, and `release-plan` does not compare again: a `config/` change after G3 is planned on the same G3 | Written disposition: stated as a limit in ADR-0029 As built and recorded as **TD-71** (deadline: before the first stg release designed under ADR-0029 B). Not fixed here: it adds logic to `release-plan` and no review round is left (agent-rules §5) |
| R2-2 | Low | Any project file containing the key counted as a decision record (the DES itself, `config/…`, a substring) | Fixed: not a DES, not under `config/`, key matched as a whole name; tests |
| R2-3 | Low | The two new gate-record shape refusals had no test | Fixed: `GateRecordShapeTest` |
| R2-4 | Low | A G3 without `--env` held any target | Fixed: a G3 approval needs `--env` (refusal, tested); test fixtures give `--env stg` |
| R2-5 | Low | `site` of an `unverified` entry compared without `str()`; G3 refusal text named `pls check p3` counts | Fixed: `str()`; G3 text "the build against its designs (pls check p3 --env --des) gives N finding(s)" |

The round-2 fixes are not reviewed again (two rounds is the limit); they are covered by the tests above and both suites.
