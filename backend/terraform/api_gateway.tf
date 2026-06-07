# HTTP API (API Gateway v2)
resource "aws_apigatewayv2_api" "langgraph_agent" {
  name          = "${var.prefix}-langgraph-agent-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = var.allowed_origins
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["Content-Type", "X-Api-Key"]
    max_age       = 86400
  }

  tags = {
    Name        = "${var.prefix}-langgraph-agent-api"
    Environment = var.environment
  }
}

resource "aws_apigatewayv2_integration" "langgraph_agent" {
  api_id                 = aws_apigatewayv2_api.langgraph_agent.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.langgraph_agent.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "post_query" {
  api_id    = aws_apigatewayv2_api.langgraph_agent.id
  route_key = "POST /query"
  target    = "integrations/${aws_apigatewayv2_integration.langgraph_agent.id}"
}

# Routes for the private corpus browser ("View internal documents" feature).
# These allow the frontend to list and open the documents that live inside the
# deployed Lambda container (baked in via the Dockerfile).
resource "aws_apigatewayv2_route" "get_corpus" {
  api_id    = aws_apigatewayv2_api.langgraph_agent.id
  route_key = "GET /corpus"
  target    = "integrations/${aws_apigatewayv2_integration.langgraph_agent.id}"
}

resource "aws_apigatewayv2_route" "get_corpus_files" {
  api_id    = aws_apigatewayv2_api.langgraph_agent.id
  route_key = "GET /corpus/{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.langgraph_agent.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.langgraph_agent.id
  name        = "$default"
  auto_deploy = true
}

# Allow API Gateway to invoke the Lambda
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.langgraph_agent.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.langgraph_agent.execution_arn}/*/*"
}
