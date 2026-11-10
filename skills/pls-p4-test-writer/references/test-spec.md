# Test spec format (`tests/api/*.json`)

`pls test` (HTTP) and the browser runner `runTests` read the same format. Before running, `${site:x}` and `${principal:x}` are resolved for the environment.

A file holds a JSON **list of tests**:

```json
[
  {
    "id": "T-101",
    "reqs": ["REQ-001"],
    "title": "short description",
    "as_key": "admin",
    "run_on": "${site:<name>}",
    "vars": {"e": "<item id>"},
    "steps": [ … ]
  }
]
```

| Field | Meaning |
|---|---|
| `id`, `reqs`, `title` | test id, the requirements it proves, a label |
| `as_key` | **key name** in `.pls/connections.json` (e.g. `admin`, `staff`). This is not a principal name; ask which user each key belongs to. The key is used for every step (default: the connection's `default_key`). `pls test` refuses to run if two roles resolve to the same key |
| `run_on` | site whose configuration is read for `exec` (process ids) and `siteConfig`; default is the `--site` of the command |
| step `site` | site a `create` writes to; always `${site:<name>}` of a site of this environment — `pls test` refuses a site id that `environments.json` does not list for the env, and a sandbox's shared site |
| `vars` | fixtures. A value starting with `<` is a placeholder that `--var name=value` must fill. Steps add more with `save`. Dates relative to today (overdue tests) are passed as `--var`. `pls test` refuses to run while a placeholder is unfilled; list the needed `--var`s in the hand-over message |

## Steps

Every step has `op`. A step may set its own `as_key`, for example to create a fixture as an authorised role inside a test for a read-only role.

| `op` | Fields | Checks |
|---|---|---|
| `create` | `site`, `data`, `save` (variable name) | stores the new record id in `$<save>`; with `expectHttp` it expects a refusal instead (no id saved) |
| `get` | `record` (`"$e"`), `expect` {path: value} | each path of the record equals the value; or `expectHttp` (e.g. 404 = not visible to this role) |
| `update` / `delete` | `record`, `data` (update) | HTTP 200, or `expectHttp` |
| `exec` | `record`, `process` (process `Name`), `data`? | runs the process through the API (D10: display condition enforced → 400 outside it); `expectHttp`, default 200 (any other status fails the step). The process id is read from the site configuration with the default key, so a role that cannot see the site gets its real refusal (404/403) |
| `list` | `site`, `view` (e.g. `{"ColumnFilterHash": {...}}`, `{"Overdue": true}`), `contains` / `excludes` (lists of `$var`) | record ids in or out of the filtered list; or `expectHttp` |
| `siteConfig` | `expect` {path in SiteSettings: value} | configuration check for screen-only behaviour; a value `{"contains": "text"}` checks a substring. Columns are addressed by position (`Columns.3.…`), so also assert `Columns.3.ColumnName` (TD-14). `$vars` are **not** substituted here (TD-14h): `"$x"` is compared as the literal string |
| `editPage` | `record`, `button`, `present` | button shown or not on the edit screen — **browser runner only**; over HTTP it is skipped and the test becomes `pass-api-only` |

### Values

- Paths use dots and list indexes: `ClassHash.ClassA`, `Columns.0.ValidateRequired`.
- A whole-string `"$name"` is replaced by the variable, in `data` and in `get` expectations. It is not replaced inside a longer string, in `exec` data, or in `siteConfig` expectations (TD-14h).
- Environment-specific ids in the configuration (process `Groups`/`Users`, links, summaries) are not asserted with `siteConfig`: `${principal:x}` resolves to `"Group,374"` while the setting stores `374`. Assert `"!empty"` and rely on the 0-difference round trip / `pls drift` for the exact id (equipment-loan demo T-007).
- `"!empty"` = any value that is not empty and not Pleasanter's empty date (`1899-12-30…`).
- Numbers compare by value (`1` = `1.0`). Dates come back as `"YYYY-MM-DDT00:00:00"`.
- Record data uses the API shape: `Title`, `Body`, `Status`, `StartTime`, `CompletionTime`, `ClassHash`, `NumHash`, `DateHash`, `DescriptionHash`, `CheckHash`.

## Test data

Tests leave their records on dev. Titles start with `テスト` so a person can find and delete them. `list` reads one page only, so on a site with many test records, filter the view (`view`) so the records under test are on the first page.

## Mail safety (ADR-0010)

`pls test` refuses a spec that creates, updates, deletes or executes a process on a site with notifications or reminders while `envs.<env>.side_effects.mail` is not `sink` or `disabled`. Do not split or rewrite tests to avoid the check: report the refusal and ask the person to record the environment's mail state. Read-only specs (`get`, `list`, `siteConfig`) always run, so notification settings can still be checked by configuration.

## Typical HTTP codes (1.5.2, see KB)

| Code | When |
|---|---|
| 400 | process run outside its display condition (D10) |
| 403 | read-only role writes or runs a process (D19, D20) |
| 404 | role cannot see the site or record at all |
| 500 | `context.Error` from a server script (D25); process without access for a writer (D20); process without a display condition (D21) |

## Example (illustrative, from another domain)

```json
{"id": "T-201", "reqs": ["REQ-004"], "title": "督促 only while overdue", "as_key": "somu",
 "steps": [
  {"op": "create", "site": "${site:loans}", "save": "l", "data": {"Title": "テスト 督促", "CompletionTime": "2026-01-01"}},
  {"op": "exec", "record": "$l", "process": "remind", "expectHttp": 200},
  {"op": "get", "record": "$l", "expect": {"Status": 150, "DateHash.DateC": "!empty"}},
  {"op": "exec", "record": "$l", "process": "remind", "expectHttp": 400}]}
```
