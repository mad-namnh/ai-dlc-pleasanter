# ADR-0027: KB probes that change their own site's settings, name principals in them, and hold disabled notifications

- **Status:** Proposed (2026-11-16)
- **Date:** 2026-11-16
- **Deciders:** Nam
- **Related:** I5, I9 (`docs/architecture.md` §2); ADR-0009 (`kb-verify` safety), ADR-0010 (mail and jobs outside production), ADR-0023 (shapes the KB does not cover), ADR-0025 and ADR-0026 (guarded probes, several sites, `update`, group variables — this ADR amends both); settings coverage plan `plans/2026-11-15-settings-coverage/plan.md` WS3b, WS3c

## Context

The settings coverage plan needs evidence that today's probe surface cannot produce. A probe saves its site's settings once (`updatesite`) before its steps and once more at teardown; steps act on records only.

- **WS3c-1** — does `updatesitesettings` (partial update, `ItemsController` `{id}/updatesitesettings`, Pleasanter_1.5.2.0, source-derived) make a JSON link list its master on the screen without a screen save (KB D40 (C), TD-50)? A probe must call `updatesitesettings` on its own site.
- **WS3c-2** — does a change of `Formulas[]` recompute the stored values of existing records? A probe must create records, **save changed settings**, then read the records again.
- **WS3c-3** — what `Views[].Groups` does for a role, and whether `ColumnFilterHash` of `Owner` / `Manager` stores user ids (WS1.6 needs this before mapping them). A probe must write a role's group id, or the administrator's user id, **into its site settings**; today `$group_<role>` is allowed in step data only (ADR-0026 option B item 2).
- **WS3b notifications and reminders** — Nam (2026-11-15, verbatim): "2. sửa ADR-0025 để kb-verify được tạo notification ở trạng thái tắt". Probe sites may hold no notification or reminder at any depth (ADR-0009, ADR-0025), so their stored shape (types other than mail, `Disabled`, address fields after the out-of-git decision for mail address settings) has no evidence.

Source of the routes: `Controllers/Api/ItemsController.cs` l.293 (`SynchronizeSummaries`), l.318 (`updatesitesettings`), read-only clone of tag `Pleasanter_1.5.2.0`. The request body of `updatesitesettings` and what it replaces are **not read** (the item models are not in the clone).

## Options

### Option A — Keep the probe surface; these questions stay with a person's screen checks
- Pros: nothing to build; the reviewed surface does not grow.
- Cons: WS3c-1 to 3c-3 and the notification shapes stay source-derived; WS1.6 (ids in view filters) cannot start; the plan's M3 and M5 milestones stop.

### Option B — Four additions, each confined to the probe's own sites (recommended)
1. **`settings` step** — `{"op": "settings", "site": "<key>|main", "SiteSettings": {…}}` saves new settings on one of the probe's own sites through `updatesite`, with the same own-site proof as the first save, the same forbidden content (no server script outside the main site's top-level settings, ADR-0025) and `expectHttp`. The site's teardown still runs at the end.
2. **`settings_partial` step** — `{"op": "settings_partial", "site": …, "body": {…}}` calls `updatesitesettings` on one of the probe's own sites. Same own-site proof and refusals; the body is checked by the same content rules as a full save. `expect_stored` after it is read with `getsite` as today.
3. **Variables in probe site settings** — `$group_<role>` (a role declared in the probe's `roles` and bound, ADR-0026) and `$admin_uid` (the operator's user id, already a kb-verify variable) may appear as a whole value in a probe site's settings and in a `settings` step. They are replaced before the save; an undeclared role refuses the probe file. No other principal can be named.
4. **Disabled notifications and reminders** — a probe site's settings may hold `Notifications` and `Reminders` only when **every** item has `"Disabled": true`, every address is a `example.invalid` address or a `[Owner]`-style placeholder, no `Token`, no webhook URL and no `Headers` (L-SEC-01 by path, `pls_secret_fields`), and the environment declares `side_effects.mail` `sink` or `disabled` (ADR-0010). A probe never enables one. A `settings` step may not change `Disabled`. The stored shape is all such a probe checks.
- Pros: WS3c-1 to 3c-3 and the notification shapes get evidence per version; WS1.6 and the 4.3 / 4.4 decisions can be taken on evidence.
- Cons: more code in `kb-verify`; a `settings` step makes a probe longer to review; a disabled notification that a server enables (none known) would send to `example.invalid` only.

### Option C — B without disabled notifications
- Pros: the safety rule "no notification at any depth" stays as it is.
- Cons: Nam's 2026-11-15 decision is not carried out; the notification shapes stay without evidence.

## Decision

*(not decided — Nam)* Recommendation: option B.

## Consequences

- With B: `pls_kbverify.py` gains two ops and two variable places; the file checks and the guarded runner (`pls_kbverify_guarded.py`) gain the refusals above, each with a test that fails on the parent; ADR-0009's safety list and the KB probe format (`skills/pls-kb-pleasanter/references/probes/`) are updated in the same commit.
- Probes that use them (WS3c-1, WS3c-2, WS3c-3, notification shapes) are written after the build and run on dev by a person, as before.

## Open questions

- [ ] The request body of `updatesitesettings` on 1.5.2.0 and whether it replaces or merges `Columns` — *source read of the item model, then the WS3c-1 probe*
- [ ] Whether `Disabled: true` on a notification is honoured for every type on 1.5.2 (source shows the flag; not probed) — *first notification probe, with mail `sink`*
