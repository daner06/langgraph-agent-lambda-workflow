# LangGraph research agent

## How it works

1. **Search (Tavily)**: Your question is sent to the Tavily API, which returns a list of web results (title, URL, snippet).
2. **Analyse (Bedrock)**: **Claude** via Amazon Bedrock **Converse** in **`eu-west-2`** reads those results and writes a **research summary** that answers the question.
3. **Finalise (Bedrock)**: Claude is called again to turn the summary into a **polished final answer** (structure, key takeaways, source references).

For this region, set **`BEDROCK_MODEL_ID`** to an **EU inference profile** (model IDs look like `eu.anthropic.…`). Plain `anthropic.…` foundation IDs are not what you pass here for London.

## Prerequisites

- Python **3.10+**
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
python agent.py
```

## Example of response:

```
python3 agent.py

Starting LangGraph Research Agent...
============================================================
Research query: What are the key benefits and challenges of serverless computing for startups in 2026?
------------------------------------------------------------
Searching the web for: What are the key benefits and challenges of serverless computing for startups in 2026?
Analysing with Claude on Bedrock...
Generate final answer with Claude Sonnet

Final Answer:
============================================================
# Serverless Computing for Startups in 2026: Benefits & Challenges

## Executive Summary

Serverless computing in 2026 offers startups a compelling path to faster development cycles, reduced operational overhead, and cost-efficient scaling — particularly for teams with limited engineering resources. However, the model introduces nuanced challenges around vendor lock-in, hidden integration costs, and architectural complexity that can undermine its advantages if not carefully managed. Success ultimately depends on matching serverless to the right workloads and building with discipline from day one.

---

## Key Benefits

### 1. Cost Efficiency
- The **pay-per-execution model** means startups only pay for compute they actually use, eliminating costs associated with idle server capacity
- Particularly valuable during early-stage growth when traffic patterns are unpredictable and budgets are tight
- No upfront infrastructure investment significantly lowers the barrier to entry
- Event-driven execution remains **one of the most cost-efficient ways to run cloud workloads** (TechStories)

### 2. Built-In Scalability & Agility
- **Auto-scaling is native to the architecture**, allowing startups to absorb sudden traffic spikes without manual intervention or costly over-provisioning
- Event-driven design enables systems to respond dynamically to real-time demand
- Organizations adopting cloud-native architectures, including serverless, demonstrate measurable agility advantages over competitors (Systango)

### 3. Reduced Operational Overhead
- Developers spend time **writing product code rather than managing infrastructure**, directly accelerating time-to-market
- Server patching, maintenance, and capacity planning are handled entirely by the cloud provider
- This is especially impactful for small founding teams competing against resource-rich incumbents

### 4. Edge Computing Integration
- By 2026, serverless is increasingly deployed alongside **edge computing infrastructure**, reducing latency and improving global performance for end users (LinkedIn/American Chase)
- Multi-cloud orchestration capabilities further enhance resilience and reduce single-point-of-failure risk

---

## Key Challenges

### 1. Vendor Lock-In
- Platforms like **AWS Lambda, Azure Functions, and Google Cloud Functions** create deep ecosystem dependencies that are difficult and expensive to unwind (CodeGive)
- For startups that may need to pivot their technology stack, this represents a meaningful long-term strategic risk
- Proprietary tooling, event formats, and integrations compound the switching cost over time

### 2. Hidden & Integration Costs
- A critical and frequently underestimated risk: **integration costs from supporting services** — including API Gateway, DynamoDB, SQS, and Step Functions — can easily **outweigh raw compute savings** (CodeGive)
- Startups must calculate total cost of ownership across the full service ecosystem, not just function execution costs
- Without careful cost monitoring, serverless architectures can produce billing surprises at scale

### 3. Cold Start Latency
- **Cold start delays** remain a persistent technical limitation in 2026, introducing response time variability that can degrade user experience (American Chase)
- This is particularly problematic for customer-facing applications where consistent, low-latency performance is a competitive requirement
- Mitigation strategies exist (e.g., provisioned concurrency) but add cost and complexity

### 4. Architectural Discipline & Engineering Maturity
- Serverless is **"cost-efficient and operationally elegant, but only when applied to the right workloads"** (TechStories)
- Poorly designed serverless systems can become expensive, fragile, and difficult to maintain — a risk for early-stage teams still developing engineering practices
- Function sprawl, improper state management, and over-reliance on managed services can create technical debt quickly

### 5. Observability & Debugging Complexity
- Distributed, function-based architectures are inherently **harder to monitor and troubleshoot** than traditional monolithic or containerized applications
- Tracing failures across dozens of loosely coupled functions requires dedicated tooling and operational expertise that many startups lack early on

---

## When Serverless Works — and When It Doesn't

| **Well-Suited Use Cases** | **Less Ideal Scenarios** |
|--------------------------|--------------------------|
| Variable or unpredictable workloads | Latency-critical, always-on applications |
| Small teams minimizing ops burden | Highly predictable, high-volume workloads |
| Event-driven tasks: APIs, webhooks, background jobs | Teams without architectural discipline in place |
| Rapid prototyping and MVP development | Applications requiring complex stateful workflows |

---

## Key Takeaways

1. **Cost efficiency is real but conditional** — the pay-per-use model delivers genuine savings for variable workloads, but integration costs can erode those gains if the full service ecosystem isn't accounted for (CodeGive)

2. **Operational leverage is the strongest argument for startups** — eliminating infrastructure management allows small teams to punch above their weight and ship faster

3. **Vendor lock-in deserves serious strategic consideration** — startups should evaluate portability and exit costs before committing deeply to any single cloud provider's serverless ecosystem (CodeGive)

4. **Cold starts and observability remain unsolved at scale** — teams building latency-sensitive or complex distributed systems should plan mitigation strategies from the outset (American Chase)

5. **Architectural maturity is non-negotiable** — serverless amplifies both good and bad engineering decisions; startups that invest in proper design patterns early will see compounding returns, while those that don't risk costly rewrites (TechStories)

> **Bottom Line:** Serverless computing in 2026 is a genuine accelerant for the right startup profile — lean teams, event-driven workloads, and unpredictable scaling needs. The startups that extract the most value will be those that approach it with clear eyes about total costs, vendor dependencies, and the architectural discipline required to make it work sustainably.
============================================================

============================================================
📋 FINAL ANSWER:
============================================================
# Serverless Computing for Startups in 2026: Benefits & Challenges

## Executive Summary

Serverless computing in 2026 offers startups a compelling path to faster development cycles, reduced operational overhead, and cost-efficient scaling — particularly for teams with limited engineering resources. However, the model introduces nuanced challenges around vendor lock-in, hidden integration costs, and architectural complexity that can undermine its advantages if not carefully managed. Success ultimately depends on matching serverless to the right workloads and building with discipline from day one.

---

## Key Benefits

### 1. Cost Efficiency
- The **pay-per-execution model** means startups only pay for compute they actually use, eliminating costs associated with idle server capacity
- Particularly valuable during early-stage growth when traffic patterns are unpredictable and budgets are tight
- No upfront infrastructure investment significantly lowers the barrier to entry
- Event-driven execution remains **one of the most cost-efficient ways to run cloud workloads** (TechStories)

### 2. Built-In Scalability & Agility
- **Auto-scaling is native to the architecture**, allowing startups to absorb sudden traffic spikes without manual intervention or costly over-provisioning
- Event-driven design enables systems to respond dynamically to real-time demand
- Organizations adopting cloud-native architectures, including serverless, demonstrate measurable agility advantages over competitors (Systango)

### 3. Reduced Operational Overhead
- Developers spend time **writing product code rather than managing infrastructure**, directly accelerating time-to-market
- Server patching, maintenance, and capacity planning are handled entirely by the cloud provider
- This is especially impactful for small founding teams competing against resource-rich incumbents

### 4. Edge Computing Integration
- By 2026, serverless is increasingly deployed alongside **edge computing infrastructure**, reducing latency and improving global performance for end users (LinkedIn/American Chase)
- Multi-cloud orchestration capabilities further enhance resilience and reduce single-point-of-failure risk

---

## Key Challenges

### 1. Vendor Lock-In
- Platforms like **AWS Lambda, Azure Functions, and Google Cloud Functions** create deep ecosystem dependencies that are difficult and expensive to unwind (CodeGive)
- For startups that may need to pivot their technology stack, this represents a meaningful long-term strategic risk
- Proprietary tooling, event formats, and integrations compound the switching cost over time

### 2. Hidden & Integration Costs
- A critical and frequently underestimated risk: **integration costs from supporting services** — including API Gateway, DynamoDB, SQS, and Step Functions — can easily **outweigh raw compute savings** (CodeGive)
- Startups must calculate total cost of ownership across the full service ecosystem, not just function execution costs
- Without careful cost monitoring, serverless architectures can produce billing surprises at scale

### 3. Cold Start Latency
- **Cold start delays** remain a persistent technical limitation in 2026, introducing response time variability that can degrade user experience (American Chase)
- This is particularly problematic for customer-facing applications where consistent, low-latency performance is a competitive requirement
- Mitigation strategies exist (e.g., provisioned concurrency) but add cost and complexity

### 4. Architectural Discipline & Engineering Maturity
- Serverless is **"cost-efficient and operationally elegant, but only when applied to the right workloads"** (TechStories)
- Poorly designed serverless systems can become expensive, fragile, and difficult to maintain — a risk for early-stage teams still developing engineering practices
- Function sprawl, improper state management, and over-reliance on managed services can create technical debt quickly

### 5. Observability & Debugging Complexity
- Distributed, function-based architectures are inherently **harder to monitor and troubleshoot** than traditional monolithic or containerized applications
- Tracing failures across dozens of loosely coupled functions requires dedicated tooling and operational expertise that many startups lack early on

---

## When Serverless Works — and When It Doesn't

| **Well-Suited Use Cases** | **Less Ideal Scenarios** |
|--------------------------|--------------------------|
| Variable or unpredictable workloads | Latency-critical, always-on applications |
| Small teams minimizing ops burden | Highly predictable, high-volume workloads |
| Event-driven tasks: APIs, webhooks, background jobs | Teams without architectural discipline in place |
| Rapid prototyping and MVP development | Applications requiring complex stateful workflows |

---

## Key Takeaways

1. **Cost efficiency is real but conditional** — the pay-per-use model delivers genuine savings for variable workloads, but integration costs can erode those gains if the full service ecosystem isn't accounted for (CodeGive)

2. **Operational leverage is the strongest argument for startups** — eliminating infrastructure management allows small teams to punch above their weight and ship faster

3. **Vendor lock-in deserves serious strategic consideration** — startups should evaluate portability and exit costs before committing deeply to any single cloud provider's serverless ecosystem (CodeGive)

4. **Cold starts and observability remain unsolved at scale** — teams building latency-sensitive or complex distributed systems should plan mitigation strategies from the outset (American Chase)

5. **Architectural maturity is non-negotiable** — serverless amplifies both good and bad engineering decisions; startups that invest in proper design patterns early will see compounding returns, while those that don't risk costly rewrites (TechStories)

> **Bottom Line:** Serverless computing in 2026 is a genuine accelerant for the right startup profile — lean teams, event-driven workloads, and unpredictable scaling needs. The startups that extract the most value will be those that approach it with clear eyes about total costs, vendor dependencies, and the architectural discipline required to make it work sustainably.

============================================================
✅ Research completed in 1 iteration(s)
```
