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

## Site package exported from the UI (seen 2026-11-05, 1.5.2, an adopted brownfield site)

A JSON file a person exports from the UI (no API key needed — useful for a customer's prod). `pls env-compare` and `pls version --from-package` read it.

| Part | Content |
|---|---|
| `HeaderInfo` | `AssemblyVersion` (e.g. `1.5.2.0` — the application version), `BaseSiteId`, `PackageTime` (UTC), `Server`, `CreatorName`, flags `IncludeNotifications`, `IncludeReminders`, `IncludeSitePermission`, `IncludeColumnPermission`, `IncludeRecordPermission`, `Convertors` |
| `Sites[]` | one entry per site: the getsite fields (`SiteId`, `Title`, `ReferenceType`, `InheritPermission`, …) with `SiteSettings` as an object |
| `Permissions[]` | `{SiteId, Permissions: [{ReferenceId, DeptId, GroupId, UserId, PermissionType}]}` — the same rights as getsite's `"Group,2,511"` entries |
| `PermissionIdList` | `GroupIdList [{GroupId, GroupName}]`, `UserIdList [{UserId, LoginId, Name, UserCode}]`, `DeptIdList` — names for mapping principals across environments |
| `Data` | records, only when exported with data (empty in the seen package) |

Compared with getsite of the same site after mapping ids: 0 differences (settings, scripts, permissions).

**Importing a site package (UI), seen 2026-11-08, 1.5.2, a brownfield app (23 sites) imported twice into empty folders:** the folder tree is recreated with new site ids. `Links[].SiteId` and the `"SiteId"` of lookups inside `ChoicesText` are mapped to the new ids. **Script, style and HTML bodies are not changed** (151 of 151 byte-identical): numbers in them still name the source environment's sites. Lookup view filters come back with values as strings (`"Status": 1` → `"1"`). Records are not imported when the package has none, so settings an app keeps in records (e.g. a 共通設定 site) are empty in the copy. Parts left out by the `Include…` flags are missing from `SiteSettings`; whether `IncludeNotifications: false` also strips process-level notifications (`Processes[].Notifications`) is **not verified** — `env-compare` treats them as left out too (safe side).

## Errors seen

| HTTP | Body | Meaning |
|---|---|---|
| 422 | `ServerScriptExecutionFailed` | A server script threw outside a try/catch — e.g. top-level `const` in a shared script (D7) |
| 400 | `要求が不正です。` | Process executed outside its display condition (D10) |

## UI endpoints useful for discovery (read-only)

- `POST /items/{siteId}/SetSiteSettings` with `ControlId=NewProcess` (or `NewProcessDataChange`, …) returns the **dialog HTML** with every field and option for that setting, without saving anything. Use it to learn the schema of a setting on the exact installed version.

## Users and groups (1.5.2; first three rows: read-only probe of 2026-11-05 with an admin session; rows marked "write probe": 2026-11-11 (including the `GroupMembers` probe), tenant administrator API key, build 201520; rows marked "user probe": 2026-11-11 19:03 and 19:05 +09:00, MADLAB dev 1.5.2, build 201520, tenant administrator API key, script `plans/2026-11-11-au5-role-test-users/probe-user-create.py`; rows marked "group-members probe": 2026-11-11 19:42 +09:00, MADLAB dev 1.5.2, build 201520, tenant administrator API key, script `plans/2026-11-11-test-users-in-groups/probe-group-members.py`)

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
| Write probe (2026-11-11 18:25 +09:00): `POST /api/groups/create` `{GroupName, Body, GroupMembers: ["User,<user id>,False"]}`, three groups, tenant administrator key | Each answered HTTP 200 with a new GroupId; the read-back by exact name found exactly that id. A person checked in the Pleasanter UI that the user is a member of each created group. **Not observed on create:** the third field `True` (group administrator; observed on update, see the group-members probe rows) and `Dept,<id>` members |
| `create` with `GroupChildren` | not verified (`GroupChildren` on update is also not verified) |
| Group-members probe: `POST /api/groups/get` `{View: {ColumnFilterHash: {GroupName: "<name>"}}}` | The group record has the fields: ApiVersion, AttachmentsHash, Body, CheckHash, ClassHash, Comments, CreatedTime, Creator, DateHash, DescriptionHash, Disabled, GroupChildren, GroupId, GroupMembers, GroupName, LdapGuid, LdapSearchRoot, LdapSync, NumHash, SynchronizedTime, TenantId, UpdatedTime, Updator, Ver. **The members are readable:** `GroupMembers` is an array of strings `"User,<id>,<True|False>"` (after a create with `["User,<operator>,False"]` it read `["User,<operator>,False"]`); `GroupChildren` is an array (`[]` here) |
| Group-members probe: `POST /api/groups/{id}/update` `{GroupName, Body, GroupMembers: ["User,<operator>,False", "User,<probe user>,True"]}` | HTTP 200, `{"Id": <group id>, "StatusCode": 200, "Message": "\" <name> \" を更新しました。"}`. Read-back: `GroupMembers` exactly those two strings. **The third field `True` (group administrator) is kept and shown by the read** (also after the next two rows) |
| Group-members probe: `update` with only `{Body: "<new text>"}` | HTTP 200; read-back: `GroupName` and `GroupMembers` unchanged, `Body` changed. Leaving out `GroupName` and `GroupMembers` keeps them |
| Group-members probe: `update` with `{GroupName: "<same name>", GroupMembers: ["User,<probe user>,True"]}` (no `Body`) | HTTP 200; read-back: `GroupMembers` = `["User,<probe user>,True"]`, the operator was removed: **`GroupMembers` on update replaces the whole member list** (a caller that wants to add a member must send the full list). `Body` unchanged: leaving out `Body` keeps it |
| Group-members probe: `POST /api/users/{probe user}/delete`, then read the group | HTTP 200; `GroupMembers` read `[]`, and the operator saw no user in the group in the Pleasanter UI: **deleting a user removes it from its groups** |
| Group-members probe: `/api/groups/{id}/delete` of the probe group | HTTP 200, nothing left (same as the write probe above) |
| Group-members probe, not verified | Whether an `update` honours `UpdatedTime` / `Ver` (optimistic concurrency); `Dept,<id>` members; `GroupChildren` on create or update |
| User probe (2026-11-11 19:03 and 19:05 +09:00, two runs): `POST /api/users/create` `{LoginId: "zz_probe_user_<timestamp>", Name: "<text>", Password: "<random, 28 chars: upper, lower, digit, '!'>"}`, tenant administrator key | HTTP 200, `{"Id": 10064, "StatusCode": 200, "Message": "\" <name> \" を作成しました。"}` (run 1: Id 10062, same shape). `POST /api/users/get` by `LoginId` returned exactly that UserId: the `Id` of the create answer is the new UserId. `TenantManager` was not sent |
| User probe: read-back record of a new user | Field names: ApiVersion, AttachmentsHash, Body, CheckHash, ClassHash, Comments, CreatedTime, Creator, DateHash, DeptCode, DeptId, DescriptionHash, Disabled, EnableSecondaryAuthentication, EnableSecretKey, GlobalId, Language, LastLoginTime, LdapSearchRoot, Lockout, LockoutCounter, LoginExpirationLimit, LoginExpirationPeriod, LoginId, Manager, Name, NumHash, NumberOfDenial, NumberOfLogins, PasswordChangeTime, PasswordExpirationTime, SecondaryAuthenticationCode, SecondaryAuthenticationCodeExpirationTime, SecretKey, SynchronizedTime, TenantId, TenantManager, Theme, TimeZone, UpdatedTime, Updator, UserCode, UserId, UserSettings, Ver. Values seen: Disabled false, Lockout false, TenantManager false, LockoutCounter 0. The record holds secret fields (SecretKey, SecondaryAuthenticationCode): never print or store the whole record |
| User probe: a second `create` with the **same** `LoginId` | HTTP 500, `{"Id": 0, "StatusCode": 500, "Message": "このログインIDは既に使用中です"}`; lookup still returned one user. **The server refuses a duplicate LoginId** (unlike group names) |
| User probe: `POST /api/users/{id}/delete` | HTTP 200, `{"Id": <id>, "StatusCode": 200, "Message": "\" <name> \" を削除しました。"}`; lookup by `LoginId` afterwards returned no user. **Not verified:** whether the user is kept in a trash box and its LoginId stays taken |
| User probe, screens (not a documented API): `GET /users/login` of the new user | Form fields include `Users_LoginId` (text), `Users_Password` (password), `Users_RememberMe`, `Users_ChangedPassword`, `Users_ChangedPasswordValidator` (password), hidden `ReturnUrl`, and page-level hidden fields including another `LoginId`. Run 1 picked fields by suffix and matched two fields: callers must use the exact names |
| User probe, screens: `POST /users/authenticate?ReturnUrl=%2F`, form-urlencoded with only `Users_LoginId`, `Users_Password`, `ReturnUrl` (empty), header `X-Requested-With: XMLHttpRequest` | HTTP 200, JSON command list `[{Method:"Log"}, {Method:"Message", Target:"#LoginMessage", …"ログインしています …" alert-success}, {Method:"Href", Value:"/"}]`; cookies `.AspNetCore.Cookies` and `.AspNetCore.Session` set. The new user logged in with the password given at creation; no password change was asked. No anti-forgery token was sent |
| User probe: with that session cookie and **no ApiKey**, `POST /api/users/get` `{ApiVersion: 1.1, View: {ColumnFilterHash: {LoginId: "<own login>"}}}` | HTTP 200, StatusCode 200: the API accepted the session instead of a key. **Not verified:** other API calls with a session; the rows returned (not printed) |
| User probe: with the session, `POST /users/createapikey` (empty body, header `X-Requested-With`) | HTTP 200, command list [Log, ReplaceAll "#EditorTabsContainer", Message]. One new key-shaped string appeared (in the answer or in `GET /users/editapi`; which was not distinguished). `POST /api/users/get` with it as ApiKey → HTTP 200, StatusCode 200: a key issued this way is accepted by the API, and a plain (non tenant-manager) user's key may call `/api/users/get` |
| User probe: the same key after the user was deleted | HTTP 401, `{"Id":0,"StatusCode":401,"Message":"Unable to authorize."}`: a key does not outlive its user |

Write probe limits: group names of the form `zz_probe_group_<timestamp>`, on a dev environment; the probe created and deleted its own groups and the server URL was not recorded.

