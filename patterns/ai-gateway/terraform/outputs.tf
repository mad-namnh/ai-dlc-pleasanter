output "gateway_url" {
  description = "Value for AI_GATEWAY_URL in Pleasanter (reachable from inside the VPC only)"
  value       = "http://${aws_lb.gateway.dns_name}"
}

output "lambda_function_name" {
  value = aws_lambda_function.gateway.function_name
}

output "log_group" {
  value = aws_cloudwatch_log_group.lambda.name
}
