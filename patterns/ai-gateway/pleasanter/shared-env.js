// Server script (shared: Shared = true). Suggested title: 「共通設定（環境）」
// Contains NO secrets — environment settings only.
// In project repositories the value is written as the reference  ${env:AI_GATEWAY_URL}  and resolved by the framework at deploy time.
// Dev value = the "gateway_url" output of patterns/ai-gateway/terraform.
// Use `var`, NOT const/let: Pleasanter re-runs shared scripts in the same engine, and a top-level
// const/let redeclaration makes every record save fail with ServerScriptExecutionFailed (review D7).
var AI_GATEWAY_URL = '${env:AI_GATEWAY_URL}';
