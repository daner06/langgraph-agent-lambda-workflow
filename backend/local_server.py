"""
Local development API server for the research agent.

This lets you test the exact same request/response contract that the Lambda exposes,
without deploying or needing API Gateway / DynamoDB.

Run (from repo root or backend/):

    cd backend
    python3.12 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt

    # One-time: build the small internal corpus index (requires Bedrock embedding access)
    python scripts/build_faiss_index.py

    # Start the local API (uses in-memory LangGraph checkpointer)
    USE_MEMORY_CHECKPOINTER=true uvicorn local_server:app --reload --port 8000

Then point your frontend to it:

    cd frontend
    echo 'VITE_API_URL=http://localhost:8000/query' > .env.local
    # (no API key needed locally)
    yarn dev

POST /query accepts the same body as the real endpoint:
    { "query": "your question", "thread_id": "optional" }

It returns:
    { "answer": "...", "steps": [...], "sources": [...], "iterations": N, ... }
"""

import os
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

os.environ.setdefault("USE_MEMORY_CHECKPOINTER", "true")

from agent import create_agent  # type: ignore

app = FastAPI(title="LangGraph Research Agent — Local Dev Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_agent = None


class QueryRequest(BaseModel):
    query: str
    thread_id: str | None = None


class QueryResponse(BaseModel):
    query: str
    answer: str
    iterations: int
    thread_id: str
    steps: list[Dict[str, Any]] | None = None
    sources: list[str] | None = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = create_agent()
    return _agent


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest, x_api_key: str | None = Header(default=None)):
    expected = os.environ.get("API_KEY", "")
    if expected and x_api_key != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")

    thread_id = req.thread_id or "local-dev-session"

    try:
        result = get_agent().invoke(
            {
                "query": req.query,
                "iterations": 0,
                "max_iterations": 2,
                "search_results": [],
                "retrieved_docs": [],
                "summary": "",
                "answer": "",
                "trace": [],
            },
            config={"configurable": {"thread_id": thread_id}},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    web_urls = [r.get("url") for r in (result.get("search_results") or []) if r.get("url")]
    doc_sources = [d.get("source") for d in (result.get("retrieved_docs") or []) if d.get("source")]
    sources = doc_sources + web_urls

    return QueryResponse(
        query=req.query,
        answer=result.get("answer", ""),
        iterations=result.get("iterations", 0),
        thread_id=thread_id,
        steps=result.get("trace"),
        sources=sources or None,
    )


@app.get("/health")
async def health():
    return {"status": "ok", "mode": "local-dev", "memory_checkpointer": True}


_CORPUS_DIR = Path(__file__).parent / "docs"


@app.get("/corpus")
async def list_corpus():
    """List of documents in the private RAG corpus."""
    if not _CORPUS_DIR.exists():
        return []
    items = []
    for p in sorted(_CORPUS_DIR.iterdir()):
        if p.is_file():
            ext = p.suffix.lower()
            items.append({
                "name": p.name,
                "type": "pdf" if ext == ".pdf" else ("markdown" if ext in {".md", ".txt", ".rst"} else "other"),
                "size": p.stat().st_size,
            })
    return items


@app.get("/corpus/{filename}")
async def get_corpus_file(filename: str):
    """Serve a corpus document.

    PDFs are returned directly. Text files are wrapped in a minimal HTML page
    with forced light background/dark text to avoid white-on-white rendering
    in dark-mode browsers.
    """
    safe_name = Path(filename).name
    file_path = _CORPUS_DIR / safe_name

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Document not found")

    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return FileResponse(
            path=str(file_path),
            media_type="application/pdf",
            filename=file_path.name,
            content_disposition_type="inline",
        )

    try:
        raw_text = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raw_text = file_path.read_text(encoding="utf-8", errors="replace")

    import html
    escaped = html.escape(raw_text)

    html_page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(file_path.name)}</title>
  <style>
    :root {{ color-scheme: light; }}
    body {{
      margin: 0;
      padding: 24px;
      background: #ffffff;
      color: #111111;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
      font-size: 14px;
      line-height: 1.5;
    }}
    pre {{
      white-space: pre-wrap;
      word-break: break-word;
      margin: 0;
    }}
    .header {{
      font-size: 12px;
      color: #666;
      margin-bottom: 12px;
      border-bottom: 1px solid #eee;
      padding-bottom: 8px;
    }}
  </style>
</head>
<body>
  <div class="header">{html.escape(file_path.name)}</div>
  <pre>{escaped}</pre>
</body>
</html>"""

    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_page, media_type="text/html; charset=utf-8")
