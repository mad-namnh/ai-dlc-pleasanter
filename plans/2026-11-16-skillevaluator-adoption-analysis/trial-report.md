# Trial report — SkillEvaluator 0.9.0 Tier 1 keyless checks on `skills/`

- **Date:** 2026-11-16. **Scope (Nam, D3):** `quality-check` and `pii-scan` only.
- **Setup:** `uv tool install --python 3.12 "skillevaluator==0.9.0"` into `../_agent-scratch/skillevaluator-trial/uvtools` (not the project, not on PATH). Target: a copy of `skills/` (11 skills, 461 KB, no `.pls/`) in the same scratch folder. Commands run with `SKILL_EVAL_LLM_PROVIDER`, `NVIDIA_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` unset; no `--llm-verify`; `--help` read first (neither command calls an external scanner).
- **Repository integrity:** `git status --porcelain` before and after identical. Network used: PyPI download only.
- Exit codes: both 1 (findings).

## quality-check — average 84.9 / 100 (B), every skill B (81.5–88.5)

| Finding | Skills | Assessment |
|---|---|---|
| Description contains XML tags (high, −15) | `pls-p3-config-builder` (`config/<site>/` in the description) | **Candidate real issue.** The Agent Skills spec forbids XML tags in `description`; Claude Code loads the skill today, but another harness or an upload may refuse it. To verify against the spec before any change. |
| No negative triggers in a broad description | KB, P6, lifecycle, onboarding | **Useful.** Same concern as the activation cases of the planned ADR (negative bucket). |
| Large skill (~5.6k tokens, limit 5k) | `pls-x-lifecycle` | **Known.** ADR-0029 moves rules out of skill text. |
| Description very long (300–480 chars, recommends 50–150) | most | Not adopted: our descriptions carry phase and gate context on purpose. |
| Missing `version`, `metadata.author`, `metadata.tags` | all | Not adopted: versions live in `skills/README.md` (one source). |
| No Purpose / Troubleshooting / Limitations / Prerequisites / Examples sections | all | Generic template; not adopted. Examples are avoided on purpose where they could leak a case answer (`skills/README.md` rule 4). |
| Vague words in description | P6 | Low value; not investigated further. |

## pii-scan — 1 error, 3 warnings, all false positives

| Finding | Where | Assessment |
|---|---|---|
| Hardcoded secret (critical) | KB `references/api.md:98` | False positive: a placeholder `<random, 28 chars …>` in a probe description; no value present. |
| Non-RFC1918 IP address | KB `api.md`, `behaviours.md` (`1.5.2.0`, `1.5.7.0`) | False positive: Pleasanter version numbers. |
| International phone number | KB `behaviours.md:51` | False positive: version text. |

No customer name, address or real credential found. The scan is noisy on the KB (version strings) and does not replace L-SEC-01 or Mandatory 3.

## Conclusion

- One candidate real finding (XML tag in P3 description) and one useful signal (negative triggers), both reachable without the tool now that they are known.
- Not worth adding to the suite or CI: most findings are generic conventions that conflict with ours, and the PII scan would need a waiver file for version strings.
- Reports kept in `../_agent-scratch/skillevaluator-trial/out/` until the task ends; the tool and the skills copy are removed.
