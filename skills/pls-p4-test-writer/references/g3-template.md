# `releases/<release>/g3-verification.md` — template

```markdown
# G3 verification — <release> (<app or change in a few words>)

- **Scope:** REQ-… (G1), DES-… (G2). Sites: `<site>`, …
- **Classification:** config-only / data-impacting / permission-impacting — reason
- **Status:** awaiting test run → awaiting G3 (once all tests have run)

## Evidence (dev)

| Check | Result |
|---|---|
| Build | dev releases R-…-dev applied; round trip **0 differences** (after canonicalisation: list what was folded back, if anything) |
| `pls lint` | 0 issues |
| `pls coverage` (dev) | n/n in-scope REQs with design, config and passing tests; api-only: n (UI step not checked over HTTP) |
| API tests as <role> | T-… pass — `tests/results/<file>` |
| Role tests as <role> | T-… pass / pass-api-only — `tests/results/<file>`; or **deferred** (project profile): restrictions verified in the configuration by T-… (`siteConfig`) |
| Manual checks | what was checked on the screen, by whom (pending until the person confirms) |
| Probes / KB changes | PRB-… / D… added, if any |

## Open items (state them at G4)

- …
```

Fill it in from command output and result files. Do not copy whole logs. Write `Status: G3 approved (<name>, <date>)` only after the person approves.
