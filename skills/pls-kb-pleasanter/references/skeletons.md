# New-site skeletons (1.5.2) — what `createsite` gives you

Use this in P2 for a new app instead of creating a probe site (decision B3, 2026-11-05). Evidence: `createsite` with `SiteSettings {}` on MADLAB dev 1.5.2, equipment demo (bootstrap B-20261105-dev/stg), D26.

## Stored settings right after `createsite` (both types)

```json
{"Version": 1.017, "ReferenceType": "<Results|Issues>", "NoDisplayIfReadOnly": false, "NotInheritPermissionsWhenCreatingSite": false}
```

- Nothing else is stored. Every built-in column exists with Pleasanter's defaults, so it does not appear in the export until you change it (D8: only non-default attributes are stored).
- Permissions are inherited from the parent folder: `InheritPermission` = parent id, `Permissions` = `[]` (D26).

## Built-in columns verified in use (equipment demo, slice #3)

| Type | Column | Verified behaviour |
|---|---|---|
| both | `Title` | editable text column, relabelled through `LabelText` (備品名, 借用者) |
| both | `Comments` | can be placed in `EditorColumnHash.General` |
| Results (記録テーブル) | `ResultId` | key column, first in `EditorColumnHash.General` |
| Issues (期限付きテーブル) | `IssueId` | key column, first in the editor and grid |
| Issues | `StartTime`, `CompletionTime` | date columns (relabelled 貸出日 / 返却予定日). `CompletionTime` drives the `Overdue` view (D24). API returns them as `YYYY-MM-DDT00:00:00` |
| Issues | `Status` | default status list; records created through the API had `Status` 100 (equipment demo T-103). `CurrentStatus`/`ChangedStatus` in processes |
| Issues | defaults dropped on save | `Columns[CompletionTime].ValidateRequired: true` and `Columns[Status].DefaultInput: "100"` — do not keep them in git (D8). Also `Columns[Title].ValidateRequired: true` was dropped in one project round trip (`updatesite` → export, MADLAB dev 1.5.2, 2026-11-11; one observation, not a probe) |

## Rules for P2

- A column a design uses must be placed in `EditorColumnHash.General`, or it does nothing (D22). This applies to built-in and custom columns alike.
- Anything about built-in columns that is not in this table (e.g. whether `Title` is required by default on Results — on Issues there is only the single round-trip observation above, `Body`, `WorkValue`, `ProgressRate`, `Manager`, `Owner` on Issues) is **not verified**. Design with custom slots instead, or carry it as an open point that the dev round trip in P3 confirms.
