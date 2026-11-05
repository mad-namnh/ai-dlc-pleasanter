# REQ-006 — Escalation requires a サポート責任者 (derived)

- **Status:** awaiting G1
- **Source:** derived from REQ-003 impact analysis: サポート責任者 is optional on the site, so the mail could have no recipient
- **Type (EARS):** unwanted behaviour

## Requirement

If 「エスカレーション」 is executed on an inquiry whose サポート責任者 is not set, then the 問い合わせ管理 site shall not escalate the inquiry and shall display the message 「サポート責任者を設定してからエスカレーションしてください。」.

## Acceptance criteria

1. 優先度 = 高, 状況 = 対応中, サポート責任者 empty: API execution is refused (non-2xx) and `get` shows 状況 and エスカレーション日時 unchanged.
2. Same case on the edit screen: the message above is shown and the record is not escalated (UI check).
3. *(Not automatically testable: that no mail is sent; the record being unchanged and the mail being bound to the action is the observable proxy.)*

## Notes

- Behaviour `[assumed]` (Q7), message text `[assumed]`.
- **Unverified mechanism:** `pls-kb-pleasanter` has no verified entry for refusing a process on an empty user column (process `ValidateInputs` is "not yet exercised"). P2 must probe this on dev and add a KB entry before designing it; if not feasible, G1/P2 must revisit this requirement with the customer.
