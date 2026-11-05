---
name: pls-p3-script-engineer
description: Phase P3 for changes that touch Pleasanter server scripts or client scripts/HTML/CSS. Rules for editing existing (often large, legacy) scripts safely — references instead of ids, shared-script pitfalls, timeouts, Japanese error messages, minimal diffs, syntax lint, impact through xref — and how to deploy them through a sandbox. Use together with pls-p3-config-builder whenever a design element is at ladder rung 3 or an existing script must change.
---

# pls-p3-script-engineer — scripts that survive environments and reviews

**Goal:** the script change the design asks for, nothing more, in a form that deploys to every environment and reads well as a diff.

## Before you edit

1. The design (DES) names the script and the rung-3 reason (I5). An adopted script's purpose is in `design/as-is/<site>.md` / DES-000. No reason → back to P2.
2. Impact: `pls xref --site <s>` → which other scripts use the columns and sites you touch. List them in your hand-over; changes in their behaviour are P2's business.

## Rules

| Topic | Rule | Source |
|---|---|---|
| Ids | Never a numeric site, group or user id in a body: `${site:x}`, `${principal:x}`, `${env:x}`. `pls refs --site <s>` shows every site reference | D3, L-REF-01 |
| Numbers that look like ids | Decimals are never replaced. Any other number that must stay literal is the person's decision (`pls refs --keep`) — tell them, never record it | BR7 |
| Shared server scripts | No top-level `const`/`let` (`var` only): shared scripts are concatenated | D7, L-SCR-01 |
| Time | A server script is cut off at ~10 s; external calls need a shorter timeout | KB fact 8 |
| Errors to users | `context.Error('…')` with a short Japanese message rejects the save | D25 |
| Secrets | None in any script; call external services through a gateway | D5, L-SEC-01 |
| Client scripts | They run as written in the browser: no top-level `return` | L-SCR-02 |
| Syntax | `pls lint` compiles every script with node (nothing runs) | L-SCR-02 |

## Editing legacy scripts

- Edit the files in `config/<site>/server-scripts/`, `scripts/`, `htmls/`, `styles/` — never the Pleasanter text box. Keep the file's line endings (CRLF stays CRLF).
- **Minimal diff:** change only the lines the design needs. No reformatting, renaming or "cleanup" in the same change — reviewers must see the behaviour change, and a reformat hides it.
- A large minified library inside a script: do not edit it; put new code in a separate script item if the design allows.
- New logic gets a comment in Japanese or English saying *why* (the rule), not which ticket.

## Deploy and try

- With sandboxes (ADR-0011): `pls sandbox refresh --name <you>` then `pls apply R-…` (the person or `--yes` for that sandbox). Without: the normal dev release of `pls-p3-config-builder`.
- Settings changed in the sandbox UI along the way: `pls harvest --env dev-<you> --site <s>`, review `git diff`, commit.
- Behaviour is proven in P4 by API tests (`pls test`): a server script's effect on a record, a `context.Error` refusal (expect HTTP 500 with the message), never by reading the code alone.

## Hand-over to P4

Scripts changed, the rule each implements, the xref impact list, lint 0 for L-SCR-01/02 and L-REF-01, and which acceptance criteria exercise each change.
