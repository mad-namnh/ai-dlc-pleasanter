variable "region" {
  description = "AWS region of Pleasanter and the gateway"
  type        = string
  default     = "ap-northeast-1"
}

variable "env" {
  description = "Environment name (dev, stg, …)"
  type        = string
  default     = "dev"
}

variable "name_prefix" {
  description = "Resource name prefix"
  type        = string
  default     = "pls-ai-gateway"
}

variable "vpc_id" {
  description = "VPC containing the Pleasanter EC2 instance"
  type        = string
}

variable "alb_subnet_ids" {
  description = "Subnets for the internal ALB — at least 2 subnets in 2 different AZs, same VPC as Pleasanter"
  type        = list(string)

  validation {
    condition     = length(var.alb_subnet_ids) >= 2
    error_message = "The ALB needs at least 2 subnets in 2 AZs."
  }
}

variable "pleasanter_security_group_id" {
  description = "Security group of the Pleasanter EC2 instance — only this SG may call the gateway"
  type        = string
}

variable "model_map" {
  description = <<-EOT
    Alias → Bedrock model id or inference profile id.
    Get the exact id from the Bedrock console (ap-northeast-1) after enabling Model access.
    E.g. { fast = "<Claude Haiku inference profile id>" }
  EOT
  type        = map(string)

  validation {
    condition     = length(var.model_map) > 0
    error_message = "At least one model alias is required."
  }
}

variable "default_model" {
  description = "Default alias when a request does not specify a model"
  type        = string
  default     = "fast"
}

variable "max_tokens_cap" {
  description = "Upper bound for max_tokens per request"
  type        = number
  default     = 2000
}

variable "max_prompt_chars" {
  description = "Upper bound for system + prompt length (characters)"
  type        = number
  default     = 20000
}

variable "lambda_timeout_seconds" {
  description = "Lambda timeout. Pleasanter server scripts are cut off at ~10 s, so keep it below that."
  type        = number
  default     = 9
}

variable "bedrock_read_timeout_seconds" {
  description = "Read timeout when calling Bedrock (smaller than lambda_timeout_seconds)"
  type        = number
  default     = 8
}

variable "reserved_concurrency" {
  description = "Maximum concurrent executions — caps cost on loops/failures. -1 = unlimited"
  type        = number
  default     = 5
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "bedrock_resource_arns" {
  description = <<-EOT
    ARNs that may be invoked. Default: all Anthropic models + all inference profiles in the account.
    Narrow this down to the model_map entries once the model is decided.
  EOT
  type        = list(string)
  default     = []
}
