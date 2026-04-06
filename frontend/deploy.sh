#!/usr/bin/env bash
# Build the React app and deploy it to S3 + CloudFront.
# Usage: ./frontend/deploy.sh (or cd frontend && ./deploy.sh)
# Requires: Node, yarn, AWS CLI, and AWS credentials with S3+CloudFront write access.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Resolve infra outputs ──────────────────────────────────────────────────

TF_DIR="$SCRIPT_DIR/terraform"

if [[ ! -d "$TF_DIR/.terraform" ]]; then
  echo "ERROR: Run 'terraform init && terraform apply' in frontend/terraform first."
  exit 1
fi

echo "Reading Terraform outputs…"
BUCKET=$(terraform -chdir="$TF_DIR" output -raw s3_bucket_name)
CF_ID=$(terraform -chdir="$TF_DIR" output -raw cloudfront_distribution_id)
CF_URL=$(terraform -chdir="$TF_DIR" output -raw cloudfront_url)

echo "  Bucket : $BUCKET"
echo "  CF ID  : $CF_ID"
echo "  URL    : $CF_URL"

# ── Build ──────────────────────────────────────────────────────────────────

echo ""
echo "Building React app…"
yarn install --frozen-lockfile
yarn build          # outputs to dist/

# ── Upload ─────────────────────────────────────────────────────────────────

echo ""
echo "Syncing dist/ → s3://$BUCKET …"

# HTML files: no cache (always revalidate)
aws s3 sync dist/ "s3://$BUCKET" \
  --region eu-west-2 \
  --delete \
  --exclude "*" \
  --include "*.html" \
  --cache-control "no-cache, no-store, must-revalidate"

# Assets (JS/CSS/images): immutable — Vite content-hashes the filenames
aws s3 sync dist/ "s3://$BUCKET" \
  --region eu-west-2 \
  --delete \
  --exclude "*.html" \
  --cache-control "public, max-age=31536000, immutable"

# ── CloudFront invalidation ────────────────────────────────────────────────

echo ""
echo "Invalidating CloudFront cache…"
aws cloudfront create-invalidation \
  --distribution-id "$CF_ID" \
  --paths "/*" \
  --query "Invalidation.Id" \
  --output text

echo ""
echo "Done! App is live at $CF_URL"
