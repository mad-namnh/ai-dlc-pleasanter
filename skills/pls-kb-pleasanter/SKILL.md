---
name: pls-kb-pleasanter
description: Verified knowledge of how Pleasanter 1.5.x actually behaves (configuration schema, API, save-time normalisation, filter and process limits, script pitfalls). Read it before designing, building, testing or reviewing anything in a Pleasanter project, and before trusting any assumption about Pleasanter.
---

# pls-kb-pleasanter — Pleasanter knowledge base

Every entry here was **observed on a real environment** (version and evidence given). Use it to avoid re-discovering behaviour by trial and error, and to avoid designs that Pleasanter cannot support.

## How to use

1. Before proposing a design or writing configuration, check the relevant topic below and in `references/`.
2. If you need behaviour that is **not** listed, do not assume it. Probe it on **dev** (never stg/prod), record the result, and add an entry here (with version + evidence) as part of your work.
3. When an entry and the official manual disagree, trust the entry for the stated version and flag the conflict.

## Topics

| Topic | File |
|---|---|
| Site configuration API (getsite / createsite / updatesite / copysitepackage), record API, process execution via API | `references/api.md` |
| SiteSettings schema facts (columns, processes, data changes, notifications, views) | `references/schema.md` |
| Behaviours that change designs (limits, pitfalls, defaults) | `references/behaviours.md` |

## The ten facts to remember

1. `updatesite` **replaces SiteSettings entirely**. Anything missing from the payload is deleted. Always send the complete configuration. *(1.5.2, D4)*
2. Pleasanter **canonicalises configuration on save**: it adds default fields and drops default-valued ones. Git must hold the canonical form (`pls canon`, or deploy to dev → export → unpack). *(1.5.2, D8)*
3. Site packages (`copysitepackage`) remap SiteIds in structured fields (`ChoicesText [[id]]`, `Links`, `Summaries`) but **not inside script bodies**. *(1.5.2, D3, D6)*
4. Never hard-code SiteIds in scripts — use `${site:<logical-name>}` and let `pls pack` resolve them per environment. *(D3)*
5. A **shared** server script must not declare top-level `const`/`let`; use `var`. Otherwise every record save fails with `ServerScriptExecutionFailed`. *(1.5.2, D7)*
6. **Checkbox view filters are 2-state**: you can filter "checked" but not "unchecked". Do not base a display condition on "checkbox is off" — use a status or choice column. *(1.5.2, D9)*
7. Executing a process through the API (`ProcessId` on record update) **enforces the process display condition** (HTTP 400 outside it). Display conditions are a server-side guard. *(1.5.2, D10)*
8. Server scripts are cut off at about 10 seconds. External calls need a timeout shorter than that. *(Script.json `ServerScriptTimeOut`)*
9. Secrets in server scripts are returned verbatim by `getsite` to anyone who can read site settings. Never put secret values in configuration; call external services through a gateway. *(D5, ADR-0005, `patterns/ai-gateway/`)*
10. API calls from a logged-in browser session work without an API key (same permissions as the user). *(1.5.2)*
