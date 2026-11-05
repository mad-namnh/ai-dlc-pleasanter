#!/usr/bin/env bash
# CloudShell bootstrap for the AI gateway: install Terraform, copy code,
# discover network settings from the Pleasanter EC2 instance, find a Claude Haiku
# inference profile, smoke-test Bedrock, and run terraform plan. NO apply.
#
# Usage (in CloudShell, with this repo's patterns/ai-gateway/ copied to ~/bs/gateway):
#   bash cloudshell-bootstrap.sh <pleasanter-ec2-instance-id>
# Then review the plan and run:  cd ~/ai-dlc-pleasanter/gateway/terraform && terraform apply tfplan
set -uo pipefail
REGION=ap-northeast-1
INSTANCE=${1:?usage: cloudshell-bootstrap.sh <instance-id>}
WORK=$HOME/ai-dlc-pleasanter
TFV=1.9.8
OUT=$WORK/bootstrap-summary.txt
mkdir -p "$WORK" "$HOME/bin"; export PATH="$HOME/bin:$PATH"
cd "$WORK"
rm -rf "$WORK/gateway/lambda" && mkdir -p "$WORK/gateway" && cp -r "$HOME/bs/gateway/lambda" "$HOME/bs/gateway/terraform" "$WORK/gateway/"
: > "$OUT"
log(){ echo "$*" | tee -a "$OUT"; }

log "== identity"
aws sts get-caller-identity --query Arn --output text 2>&1 | tee -a "$OUT"

log "== terraform"
if ! command -v terraform >/dev/null || [ "$(terraform version -json 2>/dev/null | python3 -c 'import sys,json;print(json.load(sys.stdin)["terraform_version"])')" != "$TFV" ]; then
  ARCH=amd64; [ "$(uname -m)" = "aarch64" ] && ARCH=arm64
  curl -sSLo /tmp/tf.zip "https://releases.hashicorp.com/terraform/${TFV}/terraform_${TFV}_linux_${ARCH}.zip" && unzip -oq /tmp/tf.zip -d "$HOME/bin"
fi
terraform version | head -1 | tee -a "$OUT"

log "== network (from $INSTANCE)"
read -r VPC SUBNET AZ <<<"$(aws ec2 describe-instances --region $REGION --instance-ids $INSTANCE \
  --query 'Reservations[0].Instances[0].[VpcId,SubnetId,Placement.AvailabilityZone]' --output text)"
SGS=$(aws ec2 describe-instances --region $REGION --instance-ids $INSTANCE \
  --query 'Reservations[0].Instances[0].SecurityGroups[].GroupId' --output text)
SG=$(echo "$SGS" | awk '{print $1}')
log "vpc=$VPC instance_subnet=$SUBNET az=$AZ instance_sgs=[$SGS] -> using sg=$SG"
aws ec2 describe-subnets --region $REGION --filters Name=vpc-id,Values=$VPC \
  --query 'Subnets[].[SubnetId,AvailabilityZone,CidrBlock,MapPublicIpOnLaunch,Tags[?Key==`Name`]|[0].Value]' --output text | sort -k2 | tee -a "$OUT"
# one subnet per AZ, instance's own subnet first
SUBNETS=$(python3 - "$VPC" "$SUBNET" "$REGION" <<'PY'
import json,subprocess,sys
vpc,inst,region=sys.argv[1:4]
s=json.loads(subprocess.check_output(["aws","ec2","describe-subnets","--region",region,"--filters",f"Name=vpc-id,Values={vpc}","--output","json"]))["Subnets"]
s.sort(key=lambda x:(x["SubnetId"]!=inst, x["AvailabilityZone"]))
seen,pick=set(),[]
for x in s:
    if x["AvailabilityZone"] not in seen: seen.add(x["AvailabilityZone"]); pick.append(x["SubnetId"])
print(" ".join(pick[:2]))
PY
)
log "alb_subnets=[$SUBNETS]"

log "== bedrock inference profiles (haiku)"
aws bedrock list-inference-profiles --region $REGION --query 'inferenceProfileSummaries[].[inferenceProfileId,status]' --output text 2>&1 \
  | grep -i haiku | sort | tee -a "$OUT"
MODEL=$(aws bedrock list-inference-profiles --region $REGION --query 'inferenceProfileSummaries[?status==`ACTIVE`].inferenceProfileId' --output text 2>/dev/null \
  | tr '\t' '\n' | grep -i 'anthropic.*haiku' | grep -E '^(jp|apac)\.' | sort -V | tail -1)
[ -z "$MODEL" ] && MODEL=$(aws bedrock list-inference-profiles --region $REGION --query 'inferenceProfileSummaries[?status==`ACTIVE`].inferenceProfileId' --output text 2>/dev/null | tr '\t' '\n' | grep -i 'anthropic.*haiku' | sort -V | tail -1)
log "model=$MODEL"

log "== bedrock smoke test"
aws bedrock-runtime converse --region $REGION --model-id "$MODEL" \
  --messages '[{"role":"user","content":[{"text":"Reply with exactly: OK"}]}]' \
  --inference-config '{"maxTokens":10}' --query 'output.message.content[0].text' --output text 2>&1 | tail -3 | tee -a "$OUT"

log "== terraform plan"
cd "$WORK/gateway/terraform"
SUB_HCL=$(echo $SUBNETS | python3 -c 'import sys,json;print(json.dumps(sys.stdin.read().split()))')
cat > terraform.tfvars <<EOF
env    = "dev"
region = "$REGION"
vpc_id                       = "$VPC"
alb_subnet_ids               = $SUB_HCL
pleasanter_security_group_id = "$SG"
model_map = {
  fast = "$MODEL"
}
EOF
cat terraform.tfvars | tee -a "$OUT"
terraform init -input=false -no-color > init.log 2>&1 && log "init: ok" || { log "init: FAILED"; tail -20 init.log | tee -a "$OUT"; }
terraform validate -no-color 2>&1 | tail -3 | tee -a "$OUT"
terraform plan -input=false -no-color -out=tfplan > plan.log 2>&1; RC=$?
grep -E "will be created|will be updated|will be destroyed|^Plan:|Error" plan.log | tee -a "$OUT"
[ $RC -ne 0 ] && tail -25 plan.log | tee -a "$OUT"
log "== DONE (summary: $OUT)"
