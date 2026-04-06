data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "lambda_execution" {
  name               = "${var.prefix}-langgraph-agent-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy" "cloudwatch_logs" {
  name = "${var.prefix}-cloudwatch-logs"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:*:*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "bedrock_access" {
  name = "${var.prefix}-bedrock-access"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        # EU inference profiles route across multiple EU regions, so foundation-model must allow any region (*).
        # The inference-profile resource is scoped to the account.
        Resource = [
          "arn:aws:bedrock:*::foundation-model/*",
          "arn:aws:bedrock:${var.aws_region}:*:inference-profile/*"
        ]
      }
    ]
  })
}

# The deployer IAM user (cd-langgraph-bedrock-agent) is created manually — see README Step 1.
# Its permissions are also attached manually using terraform/deployer-iam-policy.example.json.
# Managing the deployer user via Terraform creates a circular dependency: the user would need
# iam:GetUser to run Terraform, but only Terraform grants that permission.
