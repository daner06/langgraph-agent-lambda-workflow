# Backend — LangGraph research agent

Python agent, Lambda handler, Docker image, and Terraform for AWS. See the repo root `README.md` for the monorepo layout.

## How it works (hybrid RAG v1)

Every query runs a small LangGraph workflow that is now **visible in the UI**:

1. **Retrieve (RAG)**: The question is embedded with Amazon Bedrock (Titan Text Embeddings) and used to search a small **curated local corpus** (FAISS). Relevant passages from your own research notes are retrieved.
2. **Search (Tavily)**: In parallel (logically) we also run a live web search via Tavily.
3. **Analyse (Bedrock)**: Claude receives a clearly labelled combination of *internal documents* + *web results* and produces a factual summary.
4. **Finalise (Bedrock)**: A second call turns the summary into a well-structured answer with key takeaways.

The frontend now shows the exact **steps and decisions** the graph took (retrieve → search → analyse → finalise) plus which sources came from your documents vs the web.

For this region, set **`BEDROCK_MODEL_ID`** to an **EU inference profile** (model IDs look like `eu.anthropic.…`). The embedding model defaults to `amazon.titan-embed-text-v2:0` (override via `BEDROCK_EMBEDDING_MODEL`).

You can run the whole thing locally for manual testing (see "Local development with full API + hybrid RAG" below). No DynamoDB or Lambda required for day-to-day development.

## Prerequisites

- Python **3.12+**
- AWS credentials for **Bedrock Converse** in `eu-west-2` with model access enabled
- **Tavily** API key.

## Setup

From the repository root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment (`.env` or shell)

Place a `.env` file in **`backend/`** or at the **repository root** (both are loaded).

- **`TAVILY_API_KEY`** — required  
- **`BEDROCK_MODEL_ID`** — optional; default `eu.anthropic.claude-sonnet-4-6`  
- AWS via standard env vars, profile, or role

## Run (graph only)

```bash
cd backend
python3 agent.py
```

This runs the LangGraph agent directly with a test query and prints the execution trace (the same steps the UI will show).

## Local development with full API + hybrid RAG (recommended for manual testing)

You can run a local FastAPI server that speaks the exact same `/query` contract as the real Lambda. This is the easiest way to manually test the new "see the steps" UI and the RAG behaviour.

### 1. One-time setup (inside the backend folder)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Make sure your environment has AWS credentials that can call **Bedrock** (both the LLM and the embedding model) in `eu-west-2`.

### 2. Build the small internal research corpus (FAISS + Bedrock embeddings)

```bash
python scripts/build_faiss_index.py
```

This reads supported documents under `backend/docs/` (.md, .txt, .rst, .pdf), extracts text (page-aware for PDFs), chunks them, embeds them with Amazon Titan Text Embed v2, and writes a FAISS index to `backend/faiss_index/`.

You should see something like:

```
Found 4 document file(s)
Split into 12 chunks...
✅ Saved FAISS index to: .../faiss_index
```

(The current corpus contains a small set of internal financial documents for a fictional company plus any other research notes you add. Good for testing that the agent can cite specific internal sources the web cannot know.)

### 3. Start the local API server

```bash
USE_MEMORY_CHECKPOINTER=true uvicorn local_server:app --reload --port 8000
```

- `USE_MEMORY_CHECKPOINTER=true` means it won't try to talk to DynamoDB (perfect for laptops).
- The server also responds to `GET /health`.

### 4. Point the frontend at it

```bash
cd frontend
echo 'VITE_API_URL=http://localhost:8000/query' > .env.local
# No VITE_API_KEY needed for the local server

yarn install
yarn dev
```

Open http://localhost:5173, type a question, and send.

You will now see:
- The normal final answer (Markdown)
- The list of sources (📄 internal docs mixed with web URLs)
- A collapsible **"Show agent steps (N)"** section that reveals exactly what the LangGraph graph did:
  - `retrieve`: how many passages came from your local corpus (or "skipped")
  - `search`: Tavily result count
  - `analyse`: that it used hybrid context
  - `finalise`

Example good test questions for the baked-in corpus:
- "What did our internal tests show about Lambda cold starts in 2026?"
- "Summarise the trade-offs between serverless and containers for AI agents according to our notes."
- "How do we use DynamoDBSaver with LangGraph?"

A normal web question (e.g. "Latest news about AWS Lambda in 2026") will still go through Tavily and you will see both retrieve + search steps.

### Running the graph script with RAG

You can also run the agent directly:

```bash
cd backend
USE_MEMORY_CHECKPOINTER=true python agent.py
```

It prints the trace and the final answer to the terminal.

## How the hybrid RAG v1 flow works

```
User question
   │
   ▼
[retrieve]  ──► Bedrock Embeddings + FAISS over the curated docs/ corpus
   │
   ▼
[search]    ──► Tavily web search (always runs)
   │
   ▼
[analyse]   ──► Claude reads the *combined* internal + web context and writes a summary
   │
   ▼
[finalise]  ──► Claude turns the summary into a nicely structured final answer
   │
   ▼
Response to UI (includes `steps` array + combined `sources`)
```

The frontend renders the `steps` so you (and interviewers) can literally see the decisions the agent made.

If the FAISS index is missing the retrieve step is recorded as "skipped" and the agent continues with Tavily only (graceful degradation).

## Deployment to AWS

### RAG-specific steps (hybrid retrieval + private corpus)

Before running `./backend/deploy.sh`:

1. Build the FAISS index locally (requires Bedrock embeddings access in eu-west-2):
   ```bash
   python scripts/build_faiss_index.py
   ```

2. Then run the normal deploy scripts:
   ```bash
   ./backend/deploy.sh
   ./frontend/deploy.sh
   ```

This bakes both the FAISS index and the documents under `backend/docs/` into the container image.

---

Two separate AWS identities are needed:

| Identity | Purpose | Credentials |
|---|---|---|
| **Admin** | Runs `terraform apply` once to create all infrastructure | IAM user/role with broad permissions |
| **Deployer** (`cd-langgraph-bedrock-agent`) | Runs `deploy.sh` on every release | Narrowly scoped: ECR push, Lambda update, S3 sync, CloudFront invalidation |

### Step 1 — Create the deployer IAM user manually (once)

Terraform cannot manage the deployer user — it would need `iam:GetUser` to run, but only the admin can grant that (circular dependency). Do this once in the AWS console **with your admin account**:

1. **IAM → Users → Create user** — name: `cd-langgraph-bedrock-agent`
2. **Security credentials → Create access key** → *CLI* → save key/secret
3. **Add permissions → Attach policies → Create inline policy** — name it `LangGraphDeployerPolicy`, paste the JSON from `backend/terraform/deployer-iam-policy.example.json` (replace `YOUR_ACCOUNT_ID` with your 12-digit AWS account ID)
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

cd backend/terraform
terraform init
terraform plan
terraform apply -auto-approve

# The API URL is printed at the end — copy it for your React app
terraform output api_url
```

### Step 3 — Build and push the container image (deployer credentials)

After `terraform apply` succeeds, from the **repository root**:

```bash
export AWS_PROFILE=langgraph-deployer
./backend/deploy.sh
```

(Or `cd backend && ./deploy.sh`.)

Requirements: **Docker** must be installed and running (`docker info`).
