# Unpacked configuration — layout and references

`pls unpack` writes one folder per site, and `pls pack` / `release-plan` build the complete payload from it (I2). Edit these files; never edit an export or a payload.

```
config/<site>/
├─ meta.json              # {"ReferenceType": "Results"|"Issues"|…, "Body": "", "SiteName": "", "SiteGroupName": ""}
├─ site.json              # SiteSettings without volatile fields and without script bodies
├─ server-scripts/
│  ├─ _index.json         # [{"Id", "Name", "Title", "File", "BeforeCreate"?, "BeforeUpdate"?, "Shared"?, …}]
│  └─ <name>.js           # the Body of each script
├─ scripts/ , styles/     # client scripts / CSS, same _index.json pattern (only if the design needs them)
└─ permissions.json       # optional (ADR-0006): own permissions of the site
```

## `site.json`

The top-level keys are `SiteSettings` properties: `Columns`, `EditorColumnHash`, `GridColumns`, `FilterColumns`, `Views`, `Processes`, `Summaries`, `Links`, `Notifications`, `Reminders`, …

- Only non-default attributes are stored. Pleasanter drops default-valued fields on save, which is why `pls canon` exists (D8).
- Lists are matched by stable keys in diffs: `Columns` by `ColumnName`, `Processes` by `Name`, `Views` by `Id`, scripts by `Name`. Never change a stable key of an element that exists on an environment. To rename it, add a new one and remove the old one, and tell P2 (D12).
- Multi-value filters are JSON strings: `"ColumnFilterHash": {"Status": "[\"100\",\"200\"]"}`.
- A choice list that links to another site is `"ChoicesText": "[[${site:<name>}]]"`.

## References

| Reference | Resolved by `pack` from `environments.json` | Use for |
|---|---|---|
| `${site:<name>}` | `envs.<env>.sites.<name>.id` | links, `[[…]]` choices, `Summaries[].SiteId`, script bodies, `permissions.inherit` |
| `${principal:<name>}` | `envs.<env>.principals.<name>` (`"Group,372"` or `"User,1"`) | `permissions.json` entries, process `Groups` / `Users` / `Depts` |
| `${env:<name>}` | `envs.<env>.values.<name>` | environment-specific values (not secrets) |

A reference that `pack` cannot resolve fails the plan. That is intended, not something to work around.

## `permissions.json`

```json
{"inherit": "${site:<this site>}", "entries": ["${principal:admin},511", "${principal:<role>},1"]}
```

- `inherit` = this site → the site has its own permissions. `inherit` = parent → inherited.
- An entry is `<principal>,<value>`. Values are bit flags: 511 = all rights; 127 = read, create, update, delete, mail, export, import without site management (used for the operating role in slice #3); 1 = read only (D19).
- Read-only users still see process buttons; restrict the process with access control (D20).
- Without the file, `pls` leaves permissions untouched (D15).

## Process access control

`"Groups": ["${principal:<role>}"]` (and `Users` / `Depts`) on a process. Only those principals see the button and can run the process. Others get 403 (read-only users) or 500 (D20).
