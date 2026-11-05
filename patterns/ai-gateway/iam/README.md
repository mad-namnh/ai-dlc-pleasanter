# Deployer IAM user for the AI gateway

Do not deploy with the root account. Create a dedicated IAM user with only the permissions needed to deploy and operate `patterns/ai-gateway/`.

## Permissions

| Policy | Type | Purpose |
|---|---|---|
| `AWSCloudShellFullAccess` | AWS managed | Run Terraform in CloudShell (no access keys needed) |
| `deployer-policy.json` | **Customer managed** (not inline — user inline policies are limited to 2,048 characters; this policy is ~3,300) | Least privilege for the gateway, scoped to resources named `pls-ai-gateway-*` in ap-northeast-1 |

`deployer-policy.json` grants:

| Statement | Scope |
|---|---|
| Read-only discovery | `ec2:Describe*`, `elasticloadbalancing:Describe*`, Lambda/Logs/IAM listing — to find the Pleasanter VPC, subnets and security group |
| Security group for the ALB | Create/modify/delete security groups, ap-northeast-1 only (EC2 cannot be scoped by name) |
| ALB | `elasticloadbalancing:*` on `pls-ai-gateway-*` load balancers, target groups, listeners, rules |
| Lambda | Lifecycle of `pls-ai-gateway-*` functions only |
| IAM role | Create/manage `pls-ai-gateway-*` roles; `iam:PassRole` only to `lambda.amazonaws.com` |
| Logs | `/aws/lambda/pls-ai-gateway-*` log groups only |
| Bedrock | List models/profiles, model access (use-case form, agreements, Marketplace subscription), `InvokeModel` for smoke tests |

Not granted: other IAM users/policies, EC2 instances, VPC changes, any other Lambda/ALB, S3, billing.

## Setup (console, as root — one time)

1. IAM → Users → Create user, e.g. `madlab-deployer`; enable **console access**.
2. Permissions → Attach policies directly → `AWSCloudShellFullAccess`.
3. IAM → Policies → Create policy → JSON → paste `deployer-policy.json` → name `pls-ai-gateway-deployer` → Create.
   Then IAM → Users → `madlab-deployer` → Add permissions → Attach policies directly → select `pls-ai-gateway-deployer`.
4. Enable **MFA** for the user. Also enable MFA on root if not already, and stop using root for daily work.
5. Do not create access keys — CloudShell uses the console session.

## Known gaps

- `ec2:CreateSecurityGroup` and related actions cannot be restricted by resource name; they are limited to the region.
- Bedrock model-access action names have changed over time on AWS; if the console reports a missing permission during model access, add exactly the action it names.
