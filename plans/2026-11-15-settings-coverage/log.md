# Log — settings coverage inventory and plan

- 2026-11-15 Asked by Nam (after the Role tests task). Tier: analysis / plan (no code).
- Source: sparse checkout of GitHub Implem/Implem.Pleasanter tag `Pleasanter_1.5.2.0` into `../_agent-scratch/pleasanter-1.5.2.0` (Settings, Controllers/Api, Models/Sites; read only). Kept for the WS1/WS3 source reads of this plan; remove when the plan's source reads are done.
- Extraction: `SiteSettings.RecordingData` (l.762–1908) → 130 keys; item-class recording methods → table B; API controllers → 53 routes / 12 controllers. Framework scan at 2168ca4: VERIFIED_KEYS 30; KB names 29 keys; 94 keys with no evidence, KB entry or pls code.
- Findings checked in source / code: `classify` checks `Columns[x].Formula` (not recorded in 1.5.2) and nothing for `Formulas[]`; `acl_to_refs` covers `Processes[]` only; address tokens only in mail elements; `SynchronizeSummaries` → `Summaries.Synchronize` (SiteUtilities l.17352); `SynchronizeFormulas` screen-only (l.9799, l.17394); `updatesitesettings` partial update (l.2358).
- Output: `inventory.md`, `plan.md`. No subagents (budget 0/6). No review (plan document; each implementation task gets its own review).
