# Tech debt

Work that has been deliberately deferred. Each row has a **deadline** — the milestone after which it can no longer be postponed.

| ID | Item | Interim assumption (safest default) | Deadline | Related |
|---|---|---|---|---|
| TD-01 | Will the customer accept ownership zones / column-slot ranges? | The customer can edit anything → always run drift + slot-collision checks before deploy | Before the first customer production deploy | ADR-0002 |
| TD-02 | Production deployment method: runner inside the customer network or manual import; is there a staging environment? | No runner → every deploy goes through the same deploy package, imported by an operator | Before the first customer production deploy | ADR-0003 |
| TD-03 | Where project repositories live; how much offshore members may see | Configuration is sensitive → always strip secrets; repository location is a parameter | Before receiving real customer configuration | ADR-0005 |
| TD-04 | The gateway uses HTTP inside the VPC | Only the Pleasanter security group can reach it; internal ALB | Before production | `patterns/ai-gateway/` |
| TD-05 | No Bedrock cost alerting (budget / CloudWatch alarm) | `reserved_concurrency` + token caps | Before opening to real users | `patterns/ai-gateway/` |
| TD-06 | Terraform state and `terraform.tfvars` live only in the CloudShell home directory of `namnh` (ap-northeast-1); CloudShell deletes home data after 120 days of inactivity | Single operator; resources can be re-imported if state is lost | When a second person runs Terraform | `patterns/ai-gateway/terraform` |
| TD-07 | Gateway variant for customer on-prem (container + customer secret store) | Only the AWS variant exists, for dev | When the first customer uses AI features | ADR-0005 |
| TD-08 | Clean up the `zz_spike_roundtrip` folder (44562) on dev — copies contain the old key and still point to the original sites | Do not enter records into the copies | After spike round 2 | report-20261105 |
| TD-09 | AWS dev account was operated with the root user | Dedicated IAM user `namnh` with least-privilege policy `pls-ai-gateway-deployer` (`patterns/ai-gateway/iam/`); root no longer used. Confirm MFA on both root and `namnh` | Immediately | `patterns/ai-gateway/iam/` |
| TD-10 | Mail is out of scope for the current stage: no mail sink on dev (slice gap S5), mail delivery not tested, and the known defect is not fixed — in R-20261105-01 notification #1 also mails [Manager] on every escalation (view 未完了 now includes status 150) | Mail is verified at configuration level only; no real users receive mail from dev/stg; the defect is documented in `evals/results/` and `HANDOFF.md` | Before any environment sends mail to real users, or before slice #2 if it depends on notifications | slice-01 S5, `pls-demo-inquiry` REQ-003 |
