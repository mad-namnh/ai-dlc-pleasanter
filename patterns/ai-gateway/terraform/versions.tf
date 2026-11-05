terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }

  # TODO(tech-debt TD-06): move state to an S3 backend + DynamoDB lock once more than one person runs Terraform.
  # backend "s3" {}
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project   = "ai-dlc-pleasanter"
      Component = "ai-gateway"
      Env       = var.env
      ManagedBy = "terraform"
    }
  }
}
