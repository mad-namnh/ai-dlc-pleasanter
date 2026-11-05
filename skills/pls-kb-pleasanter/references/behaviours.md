# Behaviours that change designs

Each entry: what happens, why it matters, what to do. IDs refer to `docs/review-findings.md` in the framework repository.

| ID | Behaviour (version) | Consequence | Do this |
|---|---|---|---|
| D3 | SiteIds hard-coded in script strings are not remapped by site packages or the API (1.5.2) | A copied site's script silently reads another environment's data (seen in slice #1: stg read dev) | Use `${site:<name>}` in git; `pls pack` resolves per environment; lint L-REF-01 |
| D4 | `updatesite` replaces SiteSettings entirely (1.5.2) | Partial payloads delete settings; deploys overwrite customer UI edits | Complete payloads only (L-DEP-01); drift check before every deploy |
| D5 | Secrets in scripts are visible through `getsite` | Anyone with site-settings read access gets the key | No secret values in configuration; gateway pattern; L-SEC-01 |
| D7 | Shared server script with top-level `const`/`let` → every save fails `ServerScriptExecutionFailed` when combined with another script (1.5.2) | Whole site unusable for record saves | `var` in shared scripts; L-SCR-01 |
| D8 | Save-time normalisation: defaults added, default values dropped (1.5.2) | False drift if git is not canonical | `pls canon`; after first deploy, export → unpack; L-CAN-01 |
| D9 | Checkbox view filter is 2-state (only "checked") (1.5.2) | Cannot express "not yet done" with a checkbox in a display condition | Model states with **Status** or a choice column |
| D10 | API process execution enforces the display condition (1.5.2) | Display condition is a real guard, not just UI | Rely on it; test it with a negative API test |
| D11 | Removing a choice that records already use is data-impacting | Reverting a customer's added choice can orphan data | Resolve drift via `pls classify`; prefer accept + requirement |
| — | Adding a new status | Every view, notification condition and script that enumerates statuses must be checked (e.g. an "open items" view filtering on the old status list hides records in the new status) | Include a status-impact step in every design that adds a status |
| — | Server script time limit ~10 s | Slow external calls abort the save | Timeouts below 10 s; gateway with its own timeout |
