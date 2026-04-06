resource "aws_lambda_function" "langgraph_agent" {
  function_name = "${var.prefix}-langgraph-research-agent"
  role          = aws_iam_role.lambda_execution.arn

  package_type = "Image"
  image_uri    = "${aws_ecr_repository.langgraph_agent.repository_url}:latest"

  timeout     = 900  # 15 minutes (max for Lambda)
  memory_size = 3008 # 3GB for better performance

  environment {
    variables = {
      BEDROCK_MODEL_ID   = "eu.anthropic.claude-sonnet-4-6"
      TAVILY_API_KEY     = var.tavily_api_key
      CHECKPOINTS_TABLE  = aws_dynamodb_table.checkpoints_table.name
      WRITES_TABLE       = aws_dynamodb_table.writes_table.name
    }
  }

  depends_on = [
    aws_ecr_repository.langgraph_agent
  ]

  tags = {
    Name        = "${var.prefix}-langgraph-research-agent"
    Environment = var.environment
  }
}
