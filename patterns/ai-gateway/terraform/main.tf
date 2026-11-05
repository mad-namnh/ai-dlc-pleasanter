data "aws_caller_identity" "current" {}

locals {
  name = "${var.name_prefix}-${var.env}"

  bedrock_arns = length(var.bedrock_resource_arns) > 0 ? var.bedrock_resource_arns : [
    "arn:aws:bedrock:*::foundation-model/anthropic.*",
    "arn:aws:bedrock:*:${data.aws_caller_identity.current.account_id}:inference-profile/*",
  ]
}

# ---------------------------------------------------------------------------
# Lambda — NOT in the VPC: the ALB invokes it through the Lambda service,
# and it calls Bedrock via AWS's public endpoint → no NAT / VPC endpoint needed.
# The security boundary is the internal ALB + security group.
# ---------------------------------------------------------------------------

data "archive_file" "lambda" {
  type        = "zip"
  source_file = "${path.module}/../lambda/handler.py"
  output_path = "${path.module}/build/handler.zip"
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.name}"
  retention_in_days = var.log_retention_days
}

resource "aws_iam_role" "lambda" {
  name = "${local.name}-lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "lambda" {
  name = "${local.name}-lambda"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "InvokeBedrock"
        Effect   = "Allow"
        Action   = ["bedrock:InvokeModel"]
        Resource = local.bedrock_arns
      },
      {
        Sid      = "WriteLogs"
        Effect   = "Allow"
        Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "${aws_cloudwatch_log_group.lambda.arn}:*"
      },
    ]
  })
}

resource "aws_lambda_function" "gateway" {
  function_name    = local.name
  role             = aws_iam_role.lambda.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256
  timeout          = var.lambda_timeout_seconds
  memory_size      = 256
  architectures    = ["arm64"]

  reserved_concurrent_executions = var.reserved_concurrency

  environment {
    variables = {
      MODEL_MAP            = jsonencode(var.model_map)
      DEFAULT_MODEL        = var.default_model
      MAX_TOKENS_CAP       = tostring(var.max_tokens_cap)
      MAX_PROMPT_CHARS     = tostring(var.max_prompt_chars)
      BEDROCK_READ_TIMEOUT = tostring(var.bedrock_read_timeout_seconds)
    }
  }

  depends_on = [aws_cloudwatch_log_group.lambda, aws_iam_role_policy.lambda]
}

# ---------------------------------------------------------------------------
# Internal ALB — only the Pleasanter EC2 instance (by security group) may connect.
# ---------------------------------------------------------------------------

resource "aws_security_group" "alb" {
  name        = "${local.name}-alb"
  description = "AI gateway ALB - chi nhan tu Pleasanter"
  vpc_id      = var.vpc_id
}

resource "aws_vpc_security_group_ingress_rule" "from_pleasanter" {
  security_group_id            = aws_security_group.alb.id
  description                  = "HTTP tu EC2 Pleasanter"
  referenced_security_group_id = var.pleasanter_security_group_id
  ip_protocol                  = "tcp"
  from_port                    = 80
  to_port                      = 80
}

resource "aws_vpc_security_group_egress_rule" "alb_all" {
  security_group_id = aws_security_group.alb.id
  description       = "ALB goi Lambda"
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_lb" "gateway" {
  name               = substr(local.name, 0, 32)
  internal           = true
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.alb_subnet_ids
  idle_timeout       = 30

  drop_invalid_header_fields = true
}

resource "aws_lb_target_group" "lambda" {
  name        = substr("${local.name}-tg", 0, 32)
  target_type = "lambda"

  health_check {
    enabled  = true
    path     = "/health"
    interval = 300
    timeout  = 10
  }
}

resource "aws_lambda_permission" "alb" {
  statement_id  = "AllowInvokeFromALB"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.gateway.function_name
  principal     = "elasticloadbalancing.amazonaws.com"
  source_arn    = aws_lb_target_group.lambda.arn
}

resource "aws_lb_target_group_attachment" "lambda" {
  target_group_arn = aws_lb_target_group.lambda.arn
  target_id        = aws_lambda_function.gateway.arn
  depends_on       = [aws_lambda_permission.alb]
}

# TODO(tech-debt TD-04): plain HTTP inside the VPC. Move to HTTPS once an internal certificate exists (ACM + private domain).
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.gateway.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "application/json"
      message_body = "{\"error\":{\"code\":\"not_found\",\"message\":\"no route\"}}"
      status_code  = "404"
    }
  }
}

resource "aws_lb_listener_rule" "api" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 10

  condition {
    path_pattern {
      values = ["/v1/generate", "/health"]
    }
  }

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.lambda.arn
  }
}
