# Pin to linux/amd64 — Lambda does not support OCI manifest lists produced by multi-platform builds.
FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.12

# Copy requirements and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt --no-cache-dir

# Copy your agent code and Lambda handler
COPY agent.py ${LAMBDA_TASK_ROOT}
COPY lambda_function.py ${LAMBDA_TASK_ROOT}

# Set the Lambda handler
CMD [ "lambda_function.lambda_handler" ]

