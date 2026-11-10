# ADR-0005: Configuration storage and secrets policy

- **Status:** Partially accepted (2026-11-05: runtime secrets). Project-repository storage — waiting for the customer (TD-03)
- **Date:** 2026-11-04
- **Related:** review-findings B1, C4, D5

## Context

Projects are on-prem; part of the team works from Vietnam. Configuration may contain sensitive information: notification webhook URLs, tokens/URLs in server scripts, mail addresses, person/department names in permissions, internal hostnames. Business data almost certainly may not leave the customer network.

Spike round 1 found a real external-service API key in plain text inside a shared server script; `getsite` returns it verbatim (D5).

## Open questions

- [ ] May configuration (without data) live in git managed by MADLAB? Where (MADLAB GitHub org / customer Git server)? — *Contract/customer (TD-03)*
- [ ] How much configuration may members in Vietnam see? — *Contract/customer (TD-03)*
- [ ] Which SiteSettings fields on 1.5.x can hold secrets — *Spike (round 1: `ServerScripts[].Body`; notifications to be checked with webhooks)*

## Options (storage)

### Option A — Project repositories on the customer's Git server
- Pros: data never leaves the customer; easy to audit
- Cons: MADLAB depends on the customer's infrastructure and access

### Option B — Project repositories in MADLAB's GitHub org, with secrets stripped
- Pros: convenient operations; CI/agents work easily
- Cons: needs written customer consent; secret scanning must be proven effective

## Decision

*(Storage: not decided — TD-03)*

Regardless of the storage option, the following principles are **mandatory**:
1. Secrets never enter git: on unpack they are replaced with references; values live in each environment's secret store.
2. Secret scanning is a mandatory CI step (blocks merge on detection).
3. Business data never leaves the customer network; tests use synthetic data.
4. Reports/examples committed to the framework repository must be sanitized.
5. **Plain-text secrets in configuration are a blocking defect** (D5 — seen for real in the spike: an API key in a shared server script). The framework must detect them at unpack, in CI and in the pre-deploy check; only references to secrets are allowed, never values.

## Accepted decision (2026-11-05): runtime secrets

**Three layers:**

| Layer | Where | Content |
|---|---|---|
| Declaration | Repository (committed) | Configuration contains references only: `${secret:NAME}` (secret) or `${env:NAME}` (environment setting, not secret). Secret catalogue: name, environments, owner — no values |
| Value | Per-environment secret store | Dev (AWS): IAM role / Secrets Manager. On-prem production: the customer's secret store |
| Runtime | Where Pleasanter reads it | The deploy step resolves references |

**Allowed runtime locations, in order of preference:**
1. **Pleasanter holds no secret** — external services are called through an internal gateway that authenticates with IAM / a secret store. Reference implementation for AI: `patterns/ai-gateway/` (internal ALB → Lambda → Bedrock, no API key anywhere).
2. 拡張サーバスクリプト (extended server scripts: files on the server, not exposed via the API) — when a gateway cannot be deployed.
3. ~~Injecting values into server scripts / SiteSettings~~ — **forbidden**. Secret scanning blocks it at unpack, in CI and before deploy.

**Pleasanter → gateway authentication:** network-based (internal ALB + security group), no token — avoids re-creating a secret inside Pleasanter.

## Environment values: how `${env:NAME}` maps back at unpack (2026-11-10, design review WS4-F4 / F5, WS3-F12; rule chosen by Nam)

`pack` / `release-plan` replace `${env:NAME}` with `envs.<env>.values.NAME`; `unpack`, `drift` and the read-back replace the value with the reference again. That reverse step used to replace every substring equal to a value, so a value `12` turned the label `Item 4123` into `Item 4773` on the next environment.

- A string that **is** a value (the whole string) always becomes the reference.
- Inside longer text (a URL in a script body, one address in a list) a value becomes the reference only when it is **distinctive** — text of at least 6 characters that is not all digits — and stands as a **whole token** (no letter, digit or `_` directly before or after it).
- A number in `values` is never mapped back (it resolves as text when packed).
- Lint **L-REF-04**: `${env:NAME}` written inside longer text whose value in some environment is a number or shorter than 6 characters — every export of that site would differ from git. Make the reference the whole value of its field, or put the surrounding text into the value.
- `values` are checked when an environment is loaded: text, a number or null (not set yet). A list, an object or true/false is refused with the name of the value, before any command reads or writes with it.
- Limits, stated: a field whose whole content happens to equal a value (a count `12` next to a value `12`) becomes the reference; an occurrence followed by `.` or `-` still counts as a whole token (`dev.example` inside `dev.example.com`). Choose values that do not occur as other configuration text.

## Consequences

- CLI unpack needs a secret scanner + replacement; pack needs per-environment reference resolution.
- Project repositories need a per-environment secret catalogue (names only, no values).
