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

## Errors seen

| HTTP | Body | Meaning |
|---|---|---|
| 422 | `ServerScriptExecutionFailed` | A server script threw outside a try/catch — e.g. top-level `const` in a shared script (D7) |
| 400 | `要求が不正です。` | Process executed outside its display condition (D10) |

## UI endpoints useful for discovery (read-only)

- `POST /items/{siteId}/SetSiteSettings` with `ControlId=NewProcess` (or `NewProcessDataChange`, …) returns the **dialog HTML** with every field and option for that setting, without saving anything. Use it to learn the schema of a setting on the exact installed version.
