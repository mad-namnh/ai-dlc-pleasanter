# Evidence — summary synchronisation on the screen (person's check, MADLAB dev 1.5.2.0, 2026-11-17)

Procedure given by the Orchestrator (chat, 2026-11-17): two 記録テーブル sites 親 (数値A) and 子 (分類A linked to 親, 数値A); parent record P with 数値A empty; two child records linked to P with 数値A 10 and 20; on 子, サイトの管理 → tab **サマリ** → new summary: 合計 of 数値A over link 分類A into 親 / 数値A; save the site; open P; then on the サマリ tab tick the summary and press the synchronise button; open P again.

Nam's reports (chat, verbatim):
1. "tab 集計 khong co 新規作成 ban co nham khong" — the Orchestrator had named the tab 集計 (from KB D16); 集計 is the Aggregations tab.
2. "tab 集計 chi co chon 分類 o cot ben phai 追加 sang ben trai" — the 集計 tab holds the grid aggregation (choose 分類 columns, 追加).
3. "tab サマリ co roi, dang thu" — Summaries are on the tab サマリ.
4. "Buoc 4: van hien thi 0, Buoc 6: da thanh 30" — after adding the summary and saving the site, P's 数値A still showed 0; after the synchronise button it showed 30.

5. "nhan nut dong bo la 同期, user phai la admin moi bam duoc" — the button's label is 同期; only an administrator can press it.

6. "user co quyen quan lý site do" — "admin" here means a user with the manage permission of that site (サイト管理), not necessarily the tenant administrator.

Not recorded: the text of the confirmation.

Reading: on 1.5.2.0, a summary added by a site save does not recalculate an existing parent (KB D16, now also seen on the screen); the サマリ tab's synchronise button recalculates it (observed once, one parent, two children, 合計).
