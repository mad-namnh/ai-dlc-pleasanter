# REQ-005 — Existing 「未対応です」 notification and escalated inquiries (derived)

- **Status:** proposed — derived in P2 (DES-001 impact analysis), **awaiting G1**
- **Source:** impact of REQ-001 + REQ-004 on site notification 1 (mail to サポート責任者, condition = view 未完了, monitors 状況 and 優先度)
- **Type (EARS):** unwanted behaviour

## Finding

Once 未完了 includes エスカレーション中 (REQ-004), escalating an inquiry changes 状況 (a monitored column) and the record stays in 未完了, so the サポート責任者 would receive both the escalation mail (REQ-003) and the existing mail 「優先度「高」の問い合わせが未対応です」 — on every escalation and on later status/priority changes of escalated inquiries. (Whether a process save triggers the site notification is confirmed by probe P-001; the design assumes it does.)

## Options for G1

- **A (keeps today's behaviour):** give notification 1 its own condition view with 受付 / 対応中 / 顧客回答待ち only (a new view, not shown to users as a list, or shown as 未対応), so escalated inquiries do not trigger it. Rung 1.
- **B:** accept the second mail.

## Proposed requirement (option A)

If an inquiry is in status エスカレーション中, then the system shall not send the 「未対応です」 notification for it.

## Acceptance criteria (option A)

1. Notification 1's after-condition view does not include status 150.
2. 未完了 still includes 150 (REQ-004 unchanged).
