# Manual probe D38 — `items.Create` from a server script into another site (a person runs it on dev)

`kb-verify` cannot run this probe: ADR-0025 forbids `items` in a probe's server script (Nam, 2026-11-14: manual probe, guard unchanged). A person runs it on the dev environment only, then hands the observations to the framework (KB curator records D38).

- **Where:** MADLAB dev (1.5.2.0, build 201520), inside the probe folder (`kb_probe_parent`) — never in an app folder.
- **Guards (as ADR-0025):** mail of the environment is disabled or goes to a sink; the script names no `notifications` or `httpClient`; the two sites are deleted afterwards.
- **Users:** the operator (administrator) and one test user whose group has **Read + Update (5)** on the parent site and **Read (1)** on the notices site (e.g. the trial's `promo` test user, logged in through the screen or its key).

## Set-up (administrator, in the UI)

1. In the probe folder create a Results site `zz_kbprobe_D38-notices` with columns `ClassA` (parent id, text), `DescriptionA`; note its site id `<N>`.
2. Create an Issues site `zz_kbprobe_D38-parent` with Status choices `100 未処理`, `150 差戻し`, `900 完了`, and a process `差戻し` (`CurrentStatus` 100 → `ChangedStatus` 150, display condition Status = 100).
3. On the parent site add a server script, condition **after update** (`AfterUpdate`), body (replace `<N>`):

   ```javascript
   if (model.Status === 150 && saved.Status !== 150) {
     var ok = items.Create(<N>, { Title: 'D38 notice', ClassHash: { ClassA: String(model.IssueId) }, DescriptionHash: { DescriptionA: 'probe' } });
     context.Log('D38 items.Create returned ' + ok);
   }
   ```
   (Use `saved.Status` only if the version offers it; otherwise drop the second condition and note it.)
4. Site permissions: parent — test user's group 5; notices — test user's group 1.

## Steps and what to record

| # | Who | Action | Record |
|---|---|---|---|
| 1 | administrator | create a parent record, run 差戻し | notices: a record created? (count), what the log line says |
| 2 | test user (Read on notices) | create a parent record (or have one created), run 差戻し | parent status 150? notices: a new record? any error shown to the user? |
| 3 | administrator | give the test user's group **Create (3 = Read + Create)** on notices; repeat step 2 | a record created this time? |
| 4 | administrator | run 差戻し a second time on the same record (back to 100 by editing Status, then 差戻し) | a second notice record? |

**Expected from the source (`Pleasanter_1.5.2.0`, not verified):** step 1 creates a record; step 2 creates **none** — `items.Create` runs as the executing user and returns false without Create on the target site (`ServerScriptUtilities.Create` → `CreateContext` with the same user → `IssueUtilities.CreateByServerScript` → `IssueValidators.OnCreating` `CanCreate`; read for Issues only — the Results path, used by this notices site, is assumed to be the same and was not read), the parent's status change itself is kept; step 3 creates one; step 4 creates a second record (nothing deduplicates).

## Afterwards

Delete both sites (or remove the script and the test group's permissions). Send the table with the version, build and date to the framework session; the KB curator updates D38 from it.
