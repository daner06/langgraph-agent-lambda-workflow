# Checkpoints Table - stores snapshots of agent state
resource "aws_dynamodb_table" "checkpoints_table" {
  name         = "${var.prefix}-langgraph-checkpoints"
  billing_mode = "PAY_PER_REQUEST"

  hash_key  = "thread_id"
  range_key = "checkpoint_id"

  attribute {
    name = "thread_id"
    type = "S"
  }

  attribute {
    name = "checkpoint_id"
    type = "S"
  }

  ttl {
    attribute_name = "expireAt"
    enabled        = true
  }

  tags = {
    Name        = "${var.prefix}-langgraph-checkpoints"
    Environment = var.environment
  }
}

# Writes Table - stores intermediate writes from successful nodes
# This enables recovery if a parallel node fails
resource "aws_dynamodb_table" "writes_table" {
  name         = "${var.prefix}-langgraph-writes"
  billing_mode = "PAY_PER_REQUEST"

  hash_key  = "thread_id_checkpoint_id_checkpoint_ns"
  range_key = "task_id_idx"

  attribute {
    name = "thread_id_checkpoint_id_checkpoint_ns"
    type = "S"
  }

  attribute {
    name = "task_id_idx"
    type = "S"
  }

  ttl {
    attribute_name = "expireAt"
    enabled        = true
  }

  tags = {
    Name        = "${var.prefix}-langgraph-writes"
    Environment = var.environment
  }
}

# IAM policy for Lambda to access DynamoDB
resource "aws_iam_role_policy" "dynamodb_access" {
  name = "dynamodb-access"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:Query",
          "dynamodb:UpdateItem",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem"
        ]
        Resource = [
          aws_dynamodb_table.checkpoints_table.arn,
          aws_dynamodb_table.writes_table.arn
        ]
      }
    ]
  })
}