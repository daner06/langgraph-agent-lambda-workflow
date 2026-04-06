import os
import json
from agent import create_agent

_agent = None

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, X-Api-Key",
}


def get_agent():
    global _agent
    if _agent is None:
        _agent = create_agent()
    return _agent


def _response(status: int, body: dict) -> dict:
    return {"statusCode": status, "headers": CORS_HEADERS, "body": json.dumps(body)}


def lambda_handler(event, context):
    """Entry point for AWS Lambda (API Gateway HTTP API v2 and direct CLI invoke)."""

    # API key check — reject if API_KEY env var is set and header doesn't match
    expected_key = os.environ.get("API_KEY", "")
    if expected_key:
        provided_key = (event.get("headers") or {}).get("x-api-key", "")
        if provided_key != expected_key:
            return _response(401, {"error": "Unauthorized"})

    # Parse body — API Gateway v2 sends JSON as a string in event["body"]
    query = None
    thread_id = "default-session"

    body_raw = event.get("body")
    if body_raw:
        try:
            body = json.loads(body_raw) if isinstance(body_raw, str) else body_raw
            query = body.get("query")
            thread_id = body.get("thread_id", thread_id)
        except (json.JSONDecodeError, AttributeError):
            pass

    # Fallback: direct Lambda invoke (testing via CLI)
    if not query and isinstance(event, dict):
        query = event.get("query")
        thread_id = event.get("thread_id", thread_id)

    if not query:
        return _response(400, {"error": "Missing 'query' parameter"})

    try:
        config = {"configurable": {"thread_id": thread_id}}
        result = get_agent().invoke(
            {
                "query": query,
                "iterations": 0,
                "max_iterations": 2,
                "search_results": [],
                "summary": "",
                "answer": "",
            },
            config=config,
        )
        return _response(
            200,
            {
                "query": query,
                "answer": result.get("answer"),
                "iterations": result.get("iterations", 0),
                "thread_id": thread_id,
            },
        )
    except Exception as e:
        return _response(500, {"error": str(e)})
