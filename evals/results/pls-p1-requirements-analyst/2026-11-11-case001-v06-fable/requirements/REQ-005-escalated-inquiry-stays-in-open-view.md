# REQ-005 — An escalated inquiry stays in the view 未完了 (derived)

- **Status:** awaiting G1
- **Source:** derived from REQ-001/REQ-003 impact analysis: the view 未完了 enumerates statuses (受付, 対応中, 顧客回答待ち) and is the condition of notification #1 (mail to サポート責任者 on 状況/優先度 change) and of reminder #1 (「対応期限が3日以内の問い合わせ」 to 対応担当). An escalation that takes an inquiry out of that list — for example through a new status, should Q7 be answered that way — would silently stop both for escalated inquiries.
- **Type (EARS):** state-driven

## Requirement

While an escalated inquiry is neither 解決 nor クローズ（対応不要）, the view 未完了 shall list it.

## Acceptance criteria

1. An inquiry in 受付, 対応中 or 顧客回答待ち that is escalated is returned by the view 未完了 before and after the escalation (API list with that view).
2. An escalated inquiry that is then set to 解決 or クローズ（対応不要） leaves the view, as any other inquiry does.
3. For an escalated inquiry in the view, a change of 状況 or 優先度 still triggers the existing notice to the サポート責任者, and the existing reminder on 対応期限 still includes it. *(Not automatically testable: mail delivery; a person checks it on dev. The condition of both — the view 未完了 — is testable by criterion 1.)*
4. The view 状況×チャネル and the count by 状況 still include escalated inquiries.

## Notes for P2

- With the assumption of Q7 (状況 is not changed by the escalation) criteria 1, 2 and 4 hold without a configuration change; they become work only if the design or the customer's answer introduces a status for escalated inquiries (KB `behaviours.md`, "Adding a new status").
