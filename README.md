# LangGraph research agent

## How it works

1. **Search (Tavily)**: Your question is sent to the Tavily API, which returns a list of web results (title, URL, snippet).
2. **Analyse (Bedrock)**: **Claude** via Amazon Bedrock **Converse** in **`eu-west-2`** reads those results and writes a **research summary** that answers the question.
3. **Finalise (Bedrock)**: Claude is called again to turn the summary into a **polished final answer** (structure, key takeaways, source references).

For this region, set **`BEDROCK_MODEL_ID`** to an **EU inference profile** (model IDs look like `eu.anthropic.…`). Plain `anthropic.…` foundation IDs are not what you pass here for London.

## Prerequisites

- Python **3.12+**
- AWS credentials for **Bedrock Converse** in `eu-west-2` with model access enabled
- **Tavily** API key.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment (`.env` or shell)

- **`TAVILY_API_KEY`** — required  
- **`BEDROCK_MODEL_ID`** — optional; default `eu.anthropic.claude-sonnet-4-6`  
- AWS via standard env vars, profile, or role

## Run

```bash
python3 agent.py
```

## Deployment to AWS

Two separate AWS identities are needed:

| Identity | Purpose | Credentials |
|---|---|---|
| **Admin** | Runs `terraform apply` once to create all infrastructure | IAM user/role with broad permissions |
| **Deployer** (`cd-langgraph-bedrock-agent`) | Runs `deploy.sh` on every release | Narrowly scoped: ECR push + Lambda update only |

### Step 1 — Create the deployer IAM user manually (once)

Terraform cannot manage the deployer user — it would need `iam:GetUser` to run, but only the admin can grant that (circular dependency). Do this once in the AWS console **with your admin account**:

1. **IAM → Users → Create user** — name: `cd-langgraph-bedrock-agent`
2. **Security credentials → Create access key** → *CLI* → save key/secret
3. **Add permissions → Attach policies → Create inline policy** — name it `LangGraphDeployerPolicy`, paste the JSON from `terraform/deployer-iam-policy.example.json` (replace `YOUR_ACCOUNT_ID` with your 12-digit AWS account ID)
4. Add the deployer credentials to `~/.aws/credentials` under a named profile, e.g.:

```ini
[langgraph-deployer]
aws_access_key_id     = AKIA...
aws_secret_access_key = ...
```

### Step 2 — Provision infrastructure with Terraform (admin credentials)

```bash
# Switch to your admin profile
export AWS_PROFILE=your-admin-profile

# for prod use AWS Secrets Manager instead
export TF_VAR_tavily_api_key="tvly-xxxxxxxxxxxxxxxx"

cd terraform
terraform init
terraform plan
terraform apply -auto-approve
```

### Step 3 — Build and push the container image (deployer credentials)

After `terraform apply` succeeds, build and deploy from the **repo root**:

```bash
export AWS_PROFILE=langgraph-deployer
bash deploy.sh
```

Requirements: **Docker** must be installed and running (`docker info`).
