# AI Gateway for Pleasanter (Bedrock) — reference pattern

> **Status: parked (2026-11-05).** This is a reusable pattern for *customer applications* that include AI features. It is **not part of the AI-DLC framework core** (which is about AI assisting the development lifecycle). It exists because the round-trip spike found a plain-text API key in a sample site (D5); it is the reference implementation of ADR-0005's runtime-secret rule. No further work is planned unless a project needs it.

Reference pattern so that AI features in Pleasanter **keep no secrets in site configuration** (review D5, ADR-0005).

```
Pleasanter (server script)
   │  internal VPC HTTP — no key sent. Only the Pleasanter EC2 security group may connect.
   ▼
Internal ALB  ──►  Lambda (outside the VPC)  ──►  Amazon Bedrock (Claude)
                     IAM role: bedrock:InvokeModel — no API key anywhere
```

| Path | Content |
|---|---|
| `lambda/handler.py` | Gateway: `POST /v1/generate`, `GET /health`. Model aliases, token/length caps, error classification, metadata-only logging (no content) |
| `tests/` | Unit tests, no AWS needed: `python -m unittest discover -s patterns/ai-gateway/tests -v` |
| `terraform/` | Internal ALB + Lambda + IAM + logs (ap-northeast-1) |
| `pleasanter/shared-env.js` | Shared script: `AI_GATEWAY_URL` (environment setting, not a secret) |
| `pleasanter/call-gateway.js` | Replaces `apiKey()` + `callClaude()` in the existing AI script |

## Deploying to dev

### 1. Enable the model on Bedrock
Bedrock console (ap-northeast-1) → **Model access** → enable the Claude model you need (first-time Anthropic access requires a use-case form). Note the **model id / inference profile id** for `model_map`.

### 2. Terraform
```bash
cd patterns/ai-gateway/terraform
cp terraform.tfvars.example terraform.tfvars   # fill in VPC, subnets, Pleasanter EC2 SG, model id
terraform init
terraform validate
terraform plan
terraform apply
terraform output gateway_url
```
- The Lambda is not in the VPC → **no NAT gateway or VPC endpoint needed**.
- Make sure the Pleasanter EC2 security group allows **outbound** port 80 to the ALB (usually open by default).

### 3. Test from the Pleasanter EC2 instance
```bash
curl -s http://<gateway_url>/health
curl -s -X POST http://<gateway_url>/v1/generate -H 'Content-Type: application/json' \
  -d '{"model":"fast","prompt":"「こんにちは」と返してください","max_tokens":50}'
```

### 4. Configure Pleasanter
1. Add a **shared** server script 「共通設定（環境）」 with the content of `shared-env.js`, replacing `${env:AI_GATEWAY_URL}` with `gateway_url`. Keep `var` — `const`/`let` in shared scripts breaks record saves (D7).
2. In the AI script: remove `apiKey()` and `callClaude()`, paste `call-gateway.js`. Change `CONF.model` to an alias (e.g. `'fast'`).
3. **Delete** the 「共通設定（APIキー）」 script.
4. Save a record with the AI trigger enabled → check the result + CloudWatch logs.

### 5. Revoke the old Anthropic key
Once step 4 works, no Anthropic key is used anywhere → **revoke** it.

## Deployment record

| Date | Env | Result |
|---|---|---|
| 2026-11-05 | dev (ap-northeast-1) | 13 resources created. Model `jp.anthropic.claude-haiku-5-5` (Bedrock model access was already enabled; no form needed). Smoke tests: direct Lambda invoke with an ALB-shaped event → 200; unknown alias → 400 `unknown_model`; ALB target health → `healthy`; CloudWatch log line contains metadata only. Cold-start latency ≈ 4 s |
| 2026-11-05 | dev (ap-northeast-1) | **Destroyed** (`terraform destroy`, 13 resources, by `namnh` from CloudShell) to stop cost while the pattern is parked. Verified: no ALB / target group / Lambda / log group / security group / IAM role `pls-ai-gateway-*` remains; state empty. Pre-destroy state backed up as `~/terraform.tfstate.before-destroy-20261105` in CloudShell. Redeploy = `terraform apply` (new `gateway_url` → update `AI_GATEWAY_URL` in the project's `environments.json`) |

Run from CloudShell with `scripts/cloudshell-bootstrap.sh` (discovery + plan, no apply). The gateway URL is an environment value: it belongs in the project repository's environment config, not in this repository.

Open points:
- Terraform printed a deprecation notice ("This will be an error in a future release") during apply — identify and fix before the next apply.
- ~~End-to-end call from the Pleasanter EC2 instance through the ALB not yet tested~~ — **passed 2026-11-05** on spike copy site 44565: record created with the AI trigger → category, priority and reply draft filled by Claude via the gateway; no API key anywhere in the site configuration; ~4.6 s end to end.

## Controls in place

- Only aliases in `model_map` can be called; `max_tokens` and prompt length are capped.
- `reserved_concurrency` (default 5) limits cost when something loops or fails.
- CloudWatch logs in JSON: caller (site/record/feature), model, tokens, latency, error code. **No** prompt/response content.
- Timeouts: Bedrock 8 s < Lambda 9 s < server script ~10 s.

## Not yet in place (see `docs/tech-debt.md`)

Internal HTTPS, Bedrock cost alerting, Terraform remote state, container variant for customer on-prem.
