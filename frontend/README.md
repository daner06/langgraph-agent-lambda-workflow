# Frontend — React research assistant UI

React + TypeScript + Vite app served via S3 + CloudFront. See the repo root `README.md` for the full architecture.

## Local development

```bash
cd frontend
cp .env.example .env.local   # fill in VITE_API_URL and VITE_API_KEY
yarn install
yarn dev                      # http://localhost:5173
```

### Environment variables

| Variable | Description |
|---|---|
| `VITE_API_URL` | API Gateway URL — get it from `cd backend/terraform && terraform output api_url` |
| `VITE_API_KEY` | API key set via `TF_VAR_api_key` during `terraform apply` |

## Deploy to AWS

Requires the S3 bucket and CloudFront distribution to exist first:

```bash
# Provision infra once (admin credentials)
export AWS_PROFILE=your-admin-profile
cd frontend/terraform && terraform init && terraform apply -auto-approve

# Deploy on every release (deployer credentials)
AWS_PROFILE=langgraph-deployer ./frontend/deploy.sh
```

`deploy.sh` runs `yarn build`, syncs `dist/` to S3, and invalidates the CloudFront cache.

[Privacy Policy](https://d3kl9ppl7q0k8s.cloudfront.net/privacy)
