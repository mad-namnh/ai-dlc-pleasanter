# REQ-016 — 対応回数 keeps counting 対応履歴 (derived)

- **Status:** awaiting G1
- **Source:** derived from REQ-014 impact analysis: 対応回数 on 問い合わせ管理 is computed from the 対応履歴 site's existing aggregation (count of linked 対応履歴). REQ-014 changes that site's aggregation settings, and the 対応履歴 site is deployed from git for the first time (EP-1); a full-replacement deploy (KB D4) must not lose or alter the existing count.
- **Type (EARS):** ubiquitous

## Requirement

The 問い合わせ管理 site shall show as **対応回数** of each inquiry the number of 対応履歴 records linked to it.

## Acceptance criteria

1. After the release, adding a 対応履歴 to an inquiry increases 対応回数 by 1 and 合計作業時間 by its 作業時間 (both aggregations work together — EP-6).
2. Deleting that 対応履歴 decreases 対応回数 by 1.
3. For every existing inquiry, 対応回数 after the release equals its value before the release (backup comparison).
