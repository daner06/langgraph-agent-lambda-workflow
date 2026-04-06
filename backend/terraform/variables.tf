variable "prefix" {
  description = "Prefix for all resource names"
  type        = string
  default     = "cd"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "eu-west-2"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "langgraph-agent"
}

variable "tavily_api_key" {
  description = "Tavily API key for web search"
  type        = string
  sensitive   = true
}

variable "api_key" {
  description = "Secret key the React frontend must send in the X-Api-Key header. Leave empty to disable auth (not recommended)."
  type        = string
  sensitive   = true
  default     = ""
}

variable "allowed_origins" {
  description = "CORS allowed origins for the Lambda Function URL (e.g. your React app domain). Use [\"*\"] during local development."
  type        = list(string)
  default     = ["*"]
}
