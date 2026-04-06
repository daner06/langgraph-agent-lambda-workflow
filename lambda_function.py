import os
import json
from agent import create_agent

_agent = None

def get_agent():
    global _agent
    if _agent is None:
        _agent = create_agent()
    return _agent

def lambda_handler(event, context):
    """Entry point for AWS Lambda"""
    
    agent = get_agent()
    
    query = None
    thread_id = event.get("thread_id", "default-session")
    
    if isinstance(event, dict):
        # Direct invocation or API Gateway
        query = event.get("query") or event.get("queryStringParameters", {}).get("query")
        
        # Handle API Gateway body
        body = event.get("body")
        if body and not query:
            try:
                body_json = json.loads(body) if isinstance(body, str) else body
                query = body_json.get("query")
            except:
                pass
    else:
        # Raw string payload
        query = str(event) if event else None
    
    if not query:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Missing 'query' parameter"})
        }
    
    try:
        # Use thread_id to maintain conversation state across invocations
        config = {"configurable": {"thread_id": thread_id}}
        
        result = agent.invoke({
            "query": query,
            "iterations": 0,
            "max_iterations": 2,
            "search_results": [],
            "summary": "",
            "answer": ""
        }, config=config)
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "query": query,
                "answer": result.get("answer"),
                "iterations": result.get("iterations", 0),
                "thread_id": thread_id
            })
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }
