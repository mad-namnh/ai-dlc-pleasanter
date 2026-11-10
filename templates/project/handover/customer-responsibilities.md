# Customer responsibilities — <project name>

Fill in every `<…>` with the customer before the first release to a customer environment (cstg or prod), and have both sides sign at the end. MADLAB's AI agents and machines never hold production keys and have no network path to production (invariant I3, ADR-0003); every step below that touches production is done by the customer.

## 1. Approval

| Gate | What is approved | Customer approver | Deputy |
|---|---|---|---|
| G1 | requirements and assumptions | `<name>` | `<name>` |
| G4 | the release as packaged: its **release digest** (printed by `pls package` and `verify.py`, written in `approvals.md`) | `<name>` | `<name>` |

- An approval counts only in the approver's own words, sent by `<channel: mail / ticket system>`. MADLAB records it with `pls gate`; a relayed or paraphrased approval is not recorded.
- A release whose digest differs from the approved one is a different release and needs a new G4.

## 2. Execution (each release)

| Step | Who | How |
|---|---|---|
| Receive the package `<R>-<env>.zip` and its digest | `<operator>` | `<channel>`; the digest also arrives with the G4 request |
| Verify | `<operator>` | `python verify.py --env <env> --release <R>` must end `VERIFIED`; compare the printed digest with the approved one. Keep a reviewed copy of `verify.py` and run that copy |
| Backup | `<operator>` | §4, before anything changes |
| Migrations (if any) | `<operator>` | in the order of `CHECKLIST.md`, before the configuration |
| Apply | `<operator>` | method agreed in ADR-0003: `<runner inside the customer network / manual import>`, sites in the package's order |
| Manual steps (scheduled scripts) | `<operator>` | copy and compare as `CHECKLIST.md` says; report it in your own words |
| Report back | `<operator>` | result (applied / rolled back / unknown) and an export of each site, within `<n>` working days |

Release windows: `<days / hours>`. Users are told by `<who, how, how long before>`.

## 3. Incidents

- First contact for a failed or uncertain release: `<name, phone, mail>`; MADLAB contact: `<name>`.
- Who decides a rollback: `<name>`. Outcome unknown (a write got no answer): nothing is retried; the operator exports every site of the release and sends the exports before anything else is done.
- Inquiries about the running app go to `<channel>`; MADLAB answers from exports and site packages only.

## 4. Backup

- Before every release: every site of the release (site package export) and, for a migration, every record of its site. Taken by `<operator>`, kept `<where>` for `<how long>`.
- Backups hold business data. They stay inside the customer network and are never sent to MADLAB.

## 5. Recovery

- Configuration: the package's `rollback-*.json` files, restored in reverse order (`CHECKLIST.md`). Data: the backup of §4, restored by `<operator>` with `<method>`.
- After any recovery, the operator exports every site and sends the exports, so the recorded state matches the environment.

## 6. Keys, network and environments

- API keys for customer environments are issued and held by `<customer IT>`, for a user with only the rights the release needs (ADR-0014 TB-15). They are never sent to MADLAB, never pasted into a chat and never stored in a repository.
- No network path from MADLAB machines or AI services to production: enforced by `<customer IT: firewall / VPN policy>`.
- Mail and scheduled scripts on each environment: `<real / sink / disabled>`, owner `<name>` (ADR-0010). Changes made in the Pleasanter UI outside a release are reported to MADLAB, or they are found as drift at the next release.

## Sign-off

| Side | Name | Role | Date |
|---|---|---|---|
| Customer | `<name>` | `<role>` | `<date>` |
| MADLAB | `<name>` | `<role>` | `<date>` |
