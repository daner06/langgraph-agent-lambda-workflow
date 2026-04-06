resource "aws_ecr_repository" "langgraph_agent" {
  name         = "${var.prefix}-langgraph-agent"
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "${var.prefix}-langgraph-agent"
    Environment = var.environment
  }
}
