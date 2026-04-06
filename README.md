# 🧠 AI Research Assistant

> A production-ready, multi-agent research assistant built with LangGraph, AWS Bedrock (Claude Sonnet 4.6), and React. Deployed serverlessly on AWS Lambda with Terraform infrastructure as code.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-CloudFront-blue?style=for-the-badge&logo=amazoncloudfront)](https://d3kl9ppl7q0k8s.cloudfront.net/)
[![AWS](https://img.shields.io/badge/AWS-Lambda%20%7C%20Bedrock%20%7C%20CloudFront-orange?style=for-the-badge&logo=amazonaws)](https://aws.amazon.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic%20Workflow-green?style=for-the-badge)](https://langchain-ai.github.io/langgraph/)
[![Terraform](https://img.shields.io/badge/Terraform-Infrastructure%20as%20Code-purple?style=for-the-badge&logo=terraform)](https://terraform.io)

---

## 🎯 Live Demo

**Try it yourself:** [https://d3kl9ppl7q0k8s.cloudfront.net/](https://d3kl9ppl7q0k8s.cloudfront.net/)

Ask any research question, and the agent will:
1. Search the web via Tavily API
2. Analyse results with Claude Sonnet 4.6 on AWS Bedrock
3. Generate a well-structured, cited answer

---

## 🏗️ Architecture

| Layer | Component | Technology |
|-------|-----------|------------|
| **Frontend** | User Browser → CloudFront CDN → S3 | React + TypeScript |
| **API** | API Gateway (POST /query) | HTTP API (v2) |
| **Compute** | Lambda Container (3GB, 15min timeout) | Python + LangGraph |
| **Agent Workflow** | Search → Analyse → Finalise (conditional loop) | LangGraph |
| **External APIs** | Tavily (search) + Bedrock (Claude 4.6) | REST + SDK |
| **Persistence** | DynamoDB (checkpoints + writes tables) | NoSQL |

## 🛠️ Technology Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **LangGraph** | Multi-agent workflow orchestration |
| **AWS Bedrock (Claude Sonnet 4.6)** | LLM for analysis and answer generation |
| **Tavily API** | Web search for research results |
| **AWS Lambda** | Serverless compute (15-min timeout, 3GB memory) |
| **DynamoDB** | State persistence (checkpoints + writes tables) |
| **API Gateway** | REST endpoint for frontend communication |

### Infrastructure
| Technology | Purpose |
|------------|---------|
| **Terraform** | Infrastructure as Code (ECR, Lambda, DynamoDB, API Gateway, S3, CloudFront) |
| **Docker** | Containerised Lambda deployment |
| **AWS ECR** | Container registry |

### Frontend
| Technology | Purpose |
|------------|---------|
| **React 18** | UI framework |
| **TypeScript** | Type safety |
| **Vite** | Build tool |
| **Fetch API** | API client (native browser) |
| **CloudFront** | CDN + HTTPS |
| **S3** | Static hosting |

