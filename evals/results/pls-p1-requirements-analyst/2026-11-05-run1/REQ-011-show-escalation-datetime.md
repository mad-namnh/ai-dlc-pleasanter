# REQ-011 — エスカレーション日時 is visible and read-only (derived)

- **Status:** awaiting G1
- **Source:** derived from REQ-002 impact analysis: a new item affects the edit screen, list, filters and exports
- **Type (EARS):** ubiquitous

## Requirement

The 問い合わせ管理 site shall display 「エスカレーション日時」 as a read-only item on the inquiry edit screen and in the inquiry list.

## Acceptance criteria

1. Edit screen: 「エスカレーション日時」 is shown (date and time) and cannot be edited by users (UI check; `getsite` shows the item as read-only).
2. List: 「エスカレーション日時」 is a column of the list and can be used as a filter `[assumed]` (Q13) — `getsite` grid and filter settings contain it.
3. CSV export of the list contains 「エスカレーション日時」 `[assumed]` (Q13).

## Notes

- Position on the edit screen (proposed: after サポート責任者) is a P2 layout decision.
