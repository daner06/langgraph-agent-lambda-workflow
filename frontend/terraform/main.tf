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
  region = "eu-west-2"
}

# CloudFront requires ACM certificates in us-east-1 — this alias provider is
# used only for that resource.
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

output "cloudfront_url" {
  description = "HTTPS URL for the React app."
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "s3_bucket_name" {
  description = "S3 bucket that holds the built assets (needed by deploy.sh)."
  value       = aws_s3_bucket.frontend.id
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID (needed by deploy.sh to invalidate cache)."
  value       = aws_cloudfront_distribution.frontend.id
}
