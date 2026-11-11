# Pleasanter API facts (verified on 1.5.2)

All endpoints are `POST` with a JSON body containing `"ApiVersion": 1.1`. Authentication: `"ApiKey"` in the body, or the browser session of a logged-in user.

## Site configuration

| Operation | Endpoint | Response | Notes |
|---|---|---|---|
| Read site | `/api/items/{siteId}/getsite` | `{StatusCode, Response: {Data: {…site}}}` | Includes `SiteSettings`, scripts, permissions; secret values in scripts are returned verbatim |
| Create site | `/api/items/{parentId}/createsite` | `{Id, Message, StatusCode}` | Top-level folder: `parentId = 0`, `ReferenceType: "Sites"`. Requires tenant admin |
| Update site | `/api/items/{siteId}/updatesite` | `{Message, StatusCode}` | **Full replacement** of SiteSettings (D4) |
| Copy site package | `/api/items/{anchorSiteId}/copysitepackage` | `Response.Data` = JSON string `[{OldSiteId, NewSiteId, ReferenceType, Title}]` | `SelectedSites: [{SiteId, IncludeData}]`; remaps structured references, not script bodies (D3) |

Payload fields for create/update used by `pls pack`: `Title`, `Body`, `ReferenceType`, `SiteSettings`.

## Records

| Operation | Endpoint | Notes |
|---|---|---|
| Create | `/api/items/{siteId}/create` | Fields: `Title`, `Body`, `Status`, `ClassHash`, `NumHash`, `DateHash`, `DescriptionHash`, `CheckHash`; returns `Id`. Server scripts run (`BeforeCreate`…) |
| Read | `/api/items/{recordId}/get` | `Response.Data[0]` |
| Update | `/api/items/{recordId}/update` | Add `"ProcessId": n` to execute a process (spelling in the manual table is `ProccessId`; `ProcessId` works on 1.5.2). Display condition is enforced → HTTP 400 `要求が不正です。` outside it (D10) |

## Bulk, paging, principals (verified 2026-11-05)

| Operation | Endpoint | Notes |
|---|---|---|
| Read records (paged) | `/api/items/{siteId}/get` with `Offset`, `PageSize`, `View` | Response has `Offset`, `PageSize`, `TotalCount`, `Data[]` |
| Bulk upsert | `/api/items/{siteId}/bulkupsert` with `Keys: ["ClassX"]`, `Data: [...]` | Matched by keys → update; otherwise create (D13) |
| Site permissions | `getsite` → `InheritPermission` (site id), `Permissions` (`["User,1,511", "Group,2,…", "Dept,3,…"]`); `updatesite` accepts both (D15) | 511 = all rights (bit flags) |
| Principals | `/api/users/get`, `/api/groups/get`, `/api/depts/get` | IDs are per environment — map to logical names |

## Version of the installed Pleasanter (probe 2026-11-05, MADLAB dev 1.5.2, read-only)

| Source | Result |
|---|---|
| API responses (`getsite`) | No application version. `ApiVersion` (1.1) is the request protocol echoed back; `Ver` is the record version of the site |
| `/api/versions` | HTTP 404 |
| `/versions` (page) | Exists; redirects to `/users/login?ReturnUrl=%2Fversions` without a logged-in session, so an API key cannot read it |
| `/users/login` (no login) | Links `assets/css/style.min.css?v=<token>`: `201520` on MADLAB dev, whose `/versions` page shows **1.5.2** (read by Nam, 2026-11-05). One data point only — the token is used to detect a change, not to derive the version |
| `SiteSettings.Version` in an export | Settings schema version (`1.017` on 1.5.2), not the application version |

`pls version` uses this: build token and schema detected, the application version recorded by a person from `/versions` (ADR-0009).

## Site package exported from the UI (seen 2026-11-05, 1.5.2, site 797)

A JSON file a person exports from the UI (no API key needed — useful for a customer's prod). `pls env-compare` and `pls version --from-package` read it.

| Part | Content |
|---|---|
| `HeaderInfo` | `AssemblyVersion` (e.g. `1.5.2.0` — the application version), `BaseSiteId`, `PackageTime` (UTC), `Server`, `CreatorName`, flags `IncludeNotifications`, `IncludeReminders`, `IncludeSitePermission`, `IncludeColumnPermission`, `IncludeRecordPermission`, `Convertors` |
| `Sites[]` | one entry per site: the getsite fields (`SiteId`, `Title`, `ReferenceType`, `InheritPermission`, …) with `SiteSettings` as an object |
| `Permissions[]` | `{SiteId, Permissions: [{ReferenceId, DeptId, GroupId, UserId, PermissionType}]}` — the same rights as getsite's `"Group,2,511"` entries |
| `PermissionIdList` | `GroupIdList [{GroupId, GroupName}]`, `UserIdList [{UserId, LoginId, Name, UserCode}]`, `DeptIdList` — names for mapping principals across environments |
| `Data` | records, only when exported with data (empty in the seen package) |

Compared with getsite of the same site after mapping ids: 0 differences (settings, scripts, permissions).

**Importing a site package (UI), seen 2026-11-08, 1.5.2, PLAY BOARD (23 sites) imported twice into empty folders:** the folder tree is recreated with new site ids. `Links[].SiteId` and the `"SiteId"` of lookups inside `ChoicesText` are mapped to the new ids. **Script, style and HTML bodies are not changed** (151 of 151 byte-identical): numbers in them still name the source environment's sites. Lookup view filters come back with values as strings (`"Status": 1` → `"1"`). Records are not imported when the package has none, so settings an app keeps in records (e.g. a 共通設定 site) are empty in the copy. Parts left out by the `Include…` flags are missing from `SiteSettings`; whether `IncludeNotifications: false` also strips process-level notifications (`Processes[].Notifications`) is **not verified** — `env-compare` treats them as left out too (safe side).

## Errors seen

| HTTP | Body | Meaning |
|---|---|---|
| 422 | `ServerScriptExecutionFailed` | A server script threw outside a try/catch — e.g. top-level `const` in a shared script (D7) |
| 400 | `要求が不正です。` | Process executed outside its display condition (D10) |

## UI endpoints useful for discovery (read-only)

- `POST /items/{siteId}/SetSiteSettings` with `ControlId=NewProcess` (or `NewProcessDataChange`, …) returns the **dialog HTML** with every field and option for that setting, without saving anything. Use it to learn the schema of a setting on the exact installed version.

## Users and groups (1.5.2; first three rows: read-only probe of 2026-11-05 with an admin session; rows marked "write probe": 2026-11-11, tenant administrator API key, build 201520)

| Call | Result |
|---|---|
| `POST /api/groups/get` `{View: {ColumnFilterHash: {GroupName: "<name>"}}}` | `Response.Data[]` with `GroupId`, `GroupName`, …; page size 200 (`Offset` for more). The filter matched the one group with that name. `pls setup` still compares the name exactly |
| `POST /api/users/get` `{View: {ColumnFilterHash: {LoginId: "<login>"}}}` | `Response.Data[]` with `UserId`, `LoginId`, … (also sensitive fields: never print or store the whole record) |
| Either call with a non-admin user's API key | not verified: `pls setup` asks for the id when the lookup fails |
| Write probe: `POST /api/groups/create` `{GroupName: "<name>", Body: "<text>"}` (no `GroupMembers`, no `GroupChildren`) | HTTP 200, `{"Id": 376, "StatusCode": 200, "Message": "\" <name> \" を作成しました。"}`. A lookup by name then returned GroupId 376: the `Id` of the create answer is the new GroupId |
| Write probe: a second `create` with the **same** `GroupName` | HTTP 200, `{"Id": 377, … "を作成しました。"}`; lookup by name returned both [376, 377]. **The server does not refuse a duplicate group name.** A caller must look up first and refuse an ambiguous name itself |
| Write probe: `POST /api/groups/{id}/delete` (body only `ApiVersion`/`ApiKey`) for both ids | HTTP 200 each, `{"Id": <id>, "StatusCode": 200, "Message": "\" <name> \" を削除しました。"}`; lookup by name afterwards: no group left |
| Write probe: lookup with `ColumnFilterHash.GroupName` | Returned both duplicate groups for the exact name. Exact vs partial match was **not tested**; callers compare the name exactly |
| `create` / `delete` with a non-administrator key | not verified. The Pleasanter manual says these are for the tenant administrator only (https://pleasanter.org/en/manual/developers-guide/api/group-operations/api-group-create/); not observed by us |
| `create` with `GroupMembers` / `GroupChildren`; `POST /api/groups/{id}/update` | not verified |

Write probe limits: group names of the form `zz_probe_group_<timestamp>`, on a dev environment; the probe created and deleted its own groups and the server URL was not recorded.

