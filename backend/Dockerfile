# Pin to linux/amd64 — Lambda does not support OCI manifest lists produced by multi-platform builds.
FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.12

# Copy requirements and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt --no-cache-dir

# Copy your agent code and Lambda handler
COPY agent.py ${LAMBDA_TASK_ROOT}
COPY lambda_function.py ${LAMBDA_TASK_ROOT}

# Optional pre-built FAISS index for demo deploys (RAG v1).
# Run `python scripts/build_faiss_index.py` locally (with Bedrock access) before `docker build`
# to include a small curated corpus inside the image. If the directory is empty the agent
# gracefully falls back to Tavily-only retrieval.
COPY faiss_index ${LAMBDA_TASK_ROOT}/faiss_index

# Also copy the local dev server (harmless in Lambda, useful for reference)
COPY local_server.py ${LAMBDA_TASK_ROOT}/local_server.py

# Set the Lambda handler
CMD [ "lambda_function.lambda_handler" ]

