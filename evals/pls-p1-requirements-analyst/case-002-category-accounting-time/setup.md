# Setup — P1 case 002 (from slice #2)

For whoever runs the case; the runner never opens this file.

Run against a scratch project holding the configuration **before** R-20261105-05: unpack `pls-demo-inquiry/releases/R-20261105-05/rollback-inquiries.json` and `rollback-responses.json` (the pre-release stg configuration of both sites) with `pls unpack`. Use the slot ledger and `requirements/index.md` as of commit `b510417^` (REQ-001…006 only), with no `permissions.json` and no `design/decisions/DES-003`. Give the agent only the skills and the request. It must never see `evals/`, slice #2 outputs or `requirements/REQ-007…`.

## Request (customer mail, Japanese)

Copy into `customer-mail.md` at the root of the scratch folder, verbatim: the `## Mail (verbatim)` section **only** of `pls-demo-inquiry/requirements/sources/2026-11-05-customer-mail-category-accounting-time.md`. Do not pass the file header: it names the requirements slice #2 derived (contaminated run 1 on 2026-11-05). It asks for three things:
- split カテゴリ 契約・請求;
- give 経理チーム read access to inquiries and their 対応履歴;
- record 対応時間 per 対応履歴 and show a total per inquiry.

## What the agent must find in `config/` (not stated in the request)

- 対応履歴 already has a numeric column 作業時間 that is filled on existing records.
- The `ai1` script holds its own list of カテゴリ values (推定カテゴリ).
- 対応回数 on 問い合わせ is a Summary (Count) from 対応履歴.
- The process `escalate` exists (slice #1).

Known deviation (2026-11-11, same result file as P1 case 001): `b510417^` already holds REQ-007…015, so the runs used `b70c810` (the commit before slice #2 began) for `requirements/`, `design/` and `traceability.json`.
