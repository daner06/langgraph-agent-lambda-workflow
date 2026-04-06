#!/usr/bin/env bash
# Build, push to ECR, and update Lambda. Requires: Docker, AWS CLI, deployer IAM permissions.
set -euo pipefail

REGION="${REGION:-eu-west-2}"
PREFIX="${PREFIX:-cd}"
REPO_NAME="${PREFIX}-langgraph-agent"               # ECR repository name
FUNCTION_NAME="${PREFIX}-langgraph-research-agent"  # Lambda function name
IMAGE_TAG="${IMAGE_TAG:-latest}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: docker not found. Install Docker Desktop and ensure it is on your PATH." >&2
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "Error: Docker is not running. Start Docker Desktop, then retry." >&2
  exit 1
fi

echo "=> Getting AWS Account ID..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "=> Logging into ECR..."
aws ecr get-login-password --region "$REGION" | \
  docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

echo "=>  Building Docker image (linux/amd64)..."
# --platform linux/amd64 + --provenance=false: Lambda does not support OCI manifest lists.
docker build --platform linux/amd64 --provenance=false -t "${REPO_NAME}:${IMAGE_TAG}" .

echo "=>  Tagging image..."
docker tag "${REPO_NAME}:${IMAGE_TAG}" "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}:${IMAGE_TAG}"

echo "=> Pushing image to ECR..."
docker push "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}:${IMAGE_TAG}"

echo "=> Updating Lambda function..."
aws lambda update-function-code \
  --function-name "${FUNCTION_NAME}" \
  --image-uri "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}:${IMAGE_TAG}" \
  --region "$REGION"

echo "✅ Deployment complete!"
echo ""
echo "Test with:"
echo "aws lambda invoke --function-name ${FUNCTION_NAME} --payload '{\"query\":\"What is serverless?\"}' response.json --region $REGION"
echo "cat response.json"
