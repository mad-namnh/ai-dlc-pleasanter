# Input — onboarding case 001 (fictional)

A project in 運用保守 asks MADLAB to take over its order app. Facts given to the agent:

- Environments: dev (reachable, `role: dev`, MADLAB connection), stg (not reachable), prod (not reachable).
- Sites on dev: 受注一覧 (id 1201, Issues), 顧客マスタ (id 1202, Results, standard screens). 受注一覧 links to 顧客マスタ and has 6 server scripts and 20 client scripts.
- The customer sends a site package of 受注一覧 exported from prod (`.pls/packages/prod-orders.json`, AssemblyVersion 1.5.1.0, IncludeNotifications false).
- Nobody knows whether dev sends real mail.
- `pls adopt` on 1201 reports: `Tabs`, `StatusControls` without round-trip evidence; unmanaged reference 1202; 4 unmapped groups; 2 SUSPICIOUS id uses in scripts.

The person says: "Take it over. We start changes next week."
