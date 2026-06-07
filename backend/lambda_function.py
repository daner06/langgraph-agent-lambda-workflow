import os
import json
import base64
from pathlib import Path
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

    expected_key = os.environ.get("API_KEY", "")
    if expected_key:
        provided_key = (event.get("headers") or {}).get("x-api-key", "")
        if provided_key != expected_key:
            return _response(401, {"error": "Unauthorized"})

    # Corpus document serving (for the "View internal documents" feature)
    raw_path = (event.get("rawPath") or event.get("path") or "")
    if isinstance(raw_path, str):
        raw_path = raw_path.rstrip("/")

    if raw_path == "/corpus":
        docs_dir = Path(os.environ.get("LAMBDA_TASK_ROOT", ".")) / "docs"
        if not docs_dir.exists():
            return _response(200, [])
        items = []
        for p in sorted(docs_dir.iterdir()):
            if p.is_file():
                ext = p.suffix.lower()
                items.append({
                    "name": p.name,
                    "type": "pdf" if ext == ".pdf" else ("markdown" if ext in {".md", ".txt", ".rst"} else "other"),
                    "size": p.stat().st_size,
                })
        # Return plain JSON list (the _response helper is fine here)
        return _response(200, items)

    if raw_path.startswith("/corpus/"):
        filename = raw_path.split("/corpus/", 1)[1]
        safe_name = Path(filename).name
        docs_dir = Path(os.environ.get("LAMBDA_TASK_ROOT", ".")) / "docs"
        file_path = docs_dir / safe_name

        if not file_path.exists() or not file_path.is_file():
            return {"statusCode": 404, "body": json.dumps({"error": "Document not found"})}

        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            content = file_path.read_bytes()
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/pdf",
                    "Content-Disposition": f'inline; filename="{file_path.name}"',
                    "Access-Control-Allow-Origin": "*",
                },
                "body": base64.b64encode(content).decode("ascii"),
                "isBase64Encoded": True,
            }

        # Wrap text files in a minimal HTML page with forced light theme.
        # Prevents dark-mode browsers from rendering white text on white background.
        try:
            raw_text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raw_text = file_path.read_text(encoding="utf-8", errors="replace")

        import html as _html
        escaped = _html.escape(raw_text)

        html_page = (
            "<!doctype html><html lang=\"en\"><head>"
            "<meta charset=\"utf-8\">"
            f"<title>{_html.escape(file_path.name)}</title>"
            "<style>"
            ":root{color-scheme:light}"
            "body{margin:0;padding:24px;background:#fff;color:#111;font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,'Liberation Mono','Courier New',monospace;font-size:14px;line-height:1.5}"
            "pre{white-space:pre-wrap;word-break:break-word;margin:0}"
            ".hdr{font-size:12px;color:#666;margin-bottom:12px;border-bottom:1px solid #eee;padding-bottom:8px}"
            "</style></head><body>"
            f"<div class=\"hdr\">{_html.escape(file_path.name)}</div>"
            f"<pre>{escaped}</pre></body></html>"
        ).encode("utf-8")

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/html; charset=utf-8",
                "Content-Disposition": f'inline; filename="{file_path.name}.html"',
                "Access-Control-Allow-Origin": "*",
            },
            "body": base64.b64encode(html_page).decode("ascii"),
            "isBase64Encoded": True,
        }

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
                "retrieved_docs": [],
                "summary": "",
                "answer": "",
                "trace": [],
            },
            config=config,
        )

        web_urls = [r.get("url") for r in (result.get("search_results") or []) if r.get("url")]
        doc_sources = [d.get("source") for d in (result.get("retrieved_docs") or []) if d.get("source")]
        sources = doc_sources + web_urls  # internal first, then web

        return _response(
            200,
            {
                "query": query,
                "answer": result.get("answer"),
                "iterations": result.get("iterations", 0),
                "thread_id": thread_id,
                "steps": result.get("trace", []),
                "sources": sources,
            },
        )
    except Exception as e:
        return _response(500, {"error": str(e)})
