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
| Numbers that look like ids | Only numbers written as site ids (`…SiteId`/`SITE_ID` names, `items.X(`, `$p.api…({ id:`, `/items/`, `[[`, `~`) become `${site:x}`; every other number stays as the customer wrote it and `pls refs` lists it as POSSIBLE. Whether a POSSIBLE number is a site id (`pls refs --ref`) or a recognised one must stay literal (`--keep`) is the person's decision — tell them, never record it | BR7 |
| Shared server scripts | No top-level `const`/`let` (`var` only): shared scripts are concatenated | D7, L-SCR-01 |
| Time | A server script is cut off at ~10 s; external calls need a shorter timeout | KB fact 8 |
| Errors to users | `context.Error('…')` with a short Japanese message rejects the save | D25 |
| Secrets | None in any script; call external services through a gateway | D5, L-SEC-01 |
| Client scripts | They run as written in the browser: no top-level `return` | L-SCR-02 |
| Syntax | `pls lint` compiles every script with node (nothing runs) | L-SCR-02 |

## Values and old ids

- A new `${env:x}` needs a value in `values` of **every** environment, sandboxes included (a sandbox copies dev's values when it is created; add it there too). The person supplies the values; lint L-REF-02 and `pack` fail without them.
- `${env:x}` is replaced as raw text: write `'${env:x}'` where the code needs a string, bare `${env:x}` only for a number the person confirmed.
- An old hard-coded id the design does not cover: do not mix its fix into this change. Ask the person — a separate reviewed change to `${site:x}`, a literal decision (`pls refs --keep`, theirs), or a ticket for later. L-REF-01 then stays listed in the hand-over, and a release to another environment is blocked until it is settled.

## Editing legacy scripts

- Edit the files in `config/<site>/server-scripts/`, `scripts/`, `htmls/`, `styles/` — never the Pleasanter text box. Keep the file's line endings (CRLF stays CRLF).
- **Minimal diff:** change only the lines the design needs. No reformatting, renaming or "cleanup" in the same change — reviewers must see the behaviour change, and a reformat hides it.
- A large minified library inside a script: do not edit it; put new code in a separate script item if the design allows.
- New logic gets a comment in Japanese or English saying *why* (the rule), not which ticket.

## Deploy and try

- First the steps of `pls-p3-config-builder`: `pls canon`, `pls lint`, `pls coverage`, review `git diff`, commit on the ticket branch.
- With sandboxes (ADR-0011): `pls sandbox refresh --name <you>` then `pls apply R-…` (the person or `--yes` for that sandbox), and check the round trip (0 differences, otherwise fold back). Without: the normal dev release of `pls-p3-config-builder`.
- A sandbox plan is refused (`SHARED <site>: may write to <shared site> …`) when a server script references, or a summary aggregates into, a site the sandbox did not copy: saving a record in the copy would change shared dev data. Do not pass `--allow-shared-writes` yourself: report the place to the person, who removes it, copies that site into the sandbox, or accepts it with `pls sandbox refresh --name <you> --allow-shared-writes`.
- A trigger that runs only on update (`BeforeUpdate`) does not run on create: if the requirement needs both, it is a design point — say so, do not add triggers silently.
- Settings changed in the sandbox UI along the way: `pls harvest --env dev-<you> --site <s>`, review `git diff`, commit.
- Behaviour is proven in P4 by API tests (`pls test`): a server script's effect on a record, a `context.Error` refusal (expect HTTP 500 with the message), never by reading the code alone.

## Hand-over to P4

Scripts changed, the rule each implements, the xref impact list, lint 0 for L-SCR-01/02 and L-REF-01, and which acceptance criteria exercise each change.
