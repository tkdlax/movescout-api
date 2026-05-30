terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Stub module — expand when migrating to AWS.
# See deploy/terraform/README.md for migration runbook.

variable "environment" {
  type        = string
  description = "Deployment environment (staging, production)"
  default     = "staging"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

provider "aws" {
  region = var.aws_region
}

# TODO: VPC, ECS Fargate cluster, RDS PostgreSQL, ALB, Secrets Manager,
# ECR repository, CloudWatch log group, security groups.

output "migration_status" {
  value = "Terraform stubs only — see deploy/terraform/README.md"
}
