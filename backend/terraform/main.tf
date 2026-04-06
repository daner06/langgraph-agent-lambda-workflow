# terraform/main.tf
terraform {
  required_version = ">= 1.9"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.0, < 7.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Outputs
output "lambda_function_name" {
  value = aws_lambda_function.langgraph_agent.function_name
}

output "ecr_repository_url" {
  value = aws_ecr_repository.langgraph_agent.repository_url
}

output "checkpoints_table_name" {
  value = aws_dynamodb_table.checkpoints_table.name
}

output "writes_table_name" {
  value = aws_dynamodb_table.writes_table.name
}

output "api_url" {
  description = "Public HTTPS endpoint — POST to {api_url}/query from your React app."
  value       = "${trimsuffix(aws_apigatewayv2_stage.default.invoke_url, "/")}/query"
}
