# CLAUDE.md — rules for agents working in ai-dlc-pleasanter

Current phase: **architecture v0.1 adopted; next is vertical slice #1 through P1–P6**. Framework skills/agents/hooks are not built yet.

**Read `docs/architecture.md` first.** Every skill, agent, hook, check or tool you build must map to a phase (P1–P6), an artifact or an invariant (I1–I9) defined there. If it does not fit, propose an ADR instead of building it. Customer-application solutions go to `patterns/`, not into the framework core.

## Mandatory

1. **Write only to dev environments.** Write operations (create/update) may run only when the target is localhost, or an environment declared with `role: "dev"` **and** `allow_write: true` in `config.json`. Never set `role: "dev"` on a customer stg/production environment. Do not modify or loosen `assert_writable` in `scripts/common.py`. Agents must not add `--yes` unless the user asks for it.
2. **Never hold production API keys.** Exports from customer environments are run by the customer's operator or an authorized person. Agents work only on exported files.
3. **Never commit customer data.** Everything under `spike/round-trip/data/` is gitignored. Do not copy customer configuration, site names, person names or internal URLs into any other file in the repo. Spike reports must be sanitized.
4. **Never commit secrets.** `.env`, API keys, webhook URLs and tokens stay out of git. Plain-text secrets inside Pleasanter configuration are a blocking defect (ADR-0005).
5. **Do not guess about Pleasanter.** When unsure how an API or configuration field behaves on 1.5.x, record it under "Open questions" in the relevant ADR or spike report instead of assuming.

## Conventions

- **Language: English for everything in the repository**, even though day-to-day discussion with the project owner is in Vietnamese. This applies to every new or updated file for the whole framework build:
  - documents (`*.md`);
  - code comments, docstrings, CLI help, log messages, error messages, generated reports, config comments and Terraform descriptions.
  - Exceptions:
    - Messages shown to **Pleasanter end users** (e.g. `context.AddMessage`, errors thrown from server scripts) stay in **Japanese**.
    - Pleasanter-specific Japanese terms that are UI or product labels stay in Japanese, optionally with an English gloss on first use (e.g. プロセス (process), 期限付きテーブル (time-limited table)).
- **Naming of skills and agents:** `pls-<phase>-<role>`, kebab-case, English, max 64 characters.
  - `<phase>` = `p1`…`p6` (lifecycle phase in `docs/architecture.md`); `kb` for knowledge bases; `x` for cross-phase assets.
  - Examples: `pls-p1-requirements-analyst`, `pls-p2-solution-designer`, `pls-kb-pleasanter`.
  - Skills and agents share the convention; they are told apart by folder (`skills/` vs `agents/`), not by name.
- Every architecture decision is an ADR in `docs/adr/`. No implicit decisions in code.
- New findings from spikes → update `docs/review-findings.md` (add an item or change its severity).
- Deferred work goes into `docs/tech-debt.md` with a deadline.
