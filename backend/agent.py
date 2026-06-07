"""
LangGraph Research Agent
"""

import os
import time
from pathlib import Path
from typing import TypedDict, List, Dict, Any, Literal
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_aws import ChatBedrockConverse, BedrockEmbeddings
from langchain_tavily import TavilySearch
from langchain_community.vectorstores import FAISS
from langgraph_checkpoint_dynamodb.saver import DynamoDBSaver
from langgraph.checkpoint.memory import MemorySaver

_backend_dir = Path(__file__).resolve().parent
load_dotenv(_backend_dir / ".env")
load_dotenv(_backend_dir.parent / ".env")

def _aimessage_text(msg: Any) -> str:
    """Normalise AIMessage.content (str or Bedrock content blocks) to a single string."""
    c = msg.content
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        parts: List[str] = []
        for block in c:
            if isinstance(block, dict):
                t = block.get("text")
                if isinstance(t, str):
                    parts.append(t)
        return "".join(parts) if parts else str(c)
    return str(c)


class ResearchState(TypedDict):
    query: str
    search_results: List[Dict]
    retrieved_docs: List[Dict]
    summary: str
    answer: str
    iterations: int
    max_iterations: int
    trace: List[Dict[str, Any]]

def get_bedrock_llm():
    """Claude on Bedrock in eu-west-2 must use an EU inference profile ID (eu.*), not a raw foundation model ID."""
    return ChatBedrockConverse(
        model=os.environ.get("BEDROCK_MODEL_ID", "eu.anthropic.claude-sonnet-4-6"),
        region_name="eu-west-2",
        temperature=0.3,
        max_tokens=2000,
    )


def get_bedrock_embeddings() -> BedrockEmbeddings:
    """Bedrock embedding model for RAG (v1 uses Titan Text Embeddings v2 by default)."""
    model_id = os.environ.get("BEDROCK_EMBEDDING_MODEL", "amazon.titan-embed-text-v2:0")
    return BedrockEmbeddings(
        model_id=model_id,
        region_name="eu-west-2",
    )

def retrieve_node(state: ResearchState) -> Dict[str, Any]:
    """Retrieve relevant passages from the curated research corpus using Bedrock embeddings + FAISS."""
    query = state["query"]
    trace = list(state.get("trace", []))

    index_path = os.environ.get("FAISS_INDEX_PATH", "faiss_index")
    if not os.path.isabs(index_path):
        candidates = [
            Path(index_path),
            Path(__file__).resolve().parent / index_path,
            Path.cwd() / index_path,
            Path.cwd().parent / index_path,
        ]
        for c in candidates:
            if c.is_dir():
                index_path = str(c)
                break

    if not os.path.isdir(index_path):
        trace.append({
            "node": "retrieve",
            "detail": "No FAISS index found — RAG disabled for this query (hybrid will use Tavily only)",
            "skipped": True,
            "ts": time.time(),
        })
        return {"retrieved_docs": [], "trace": trace}

    try:
        embeddings = get_bedrock_embeddings()
        vectorstore = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
        hits = vectorstore.similarity_search(query, k=4)

        retrieved: List[Dict[str, Any]] = []
        for d in hits:
            retrieved.append({
                "source": d.metadata.get("source", d.metadata.get("path", "unknown")),
                "content": d.page_content[:800],
            })

        trace.append({
            "node": "retrieve",
            "detail": f"Retrieved {len(retrieved)} passages from internal research corpus",
            "ts": time.time(),
        })
        print(f"retrieve_node: got {len(retrieved)} internal passages")
        return {"retrieved_docs": retrieved, "trace": trace}
    except Exception as e:
        print(f"ERROR: FAISS retrieval failed: {e}")
        trace.append({
            "node": "retrieve",
            "detail": f"RAG retrieval error ({e}) — continuing with Tavily only",
            "error": True,
            "ts": time.time(),
        })
        return {"retrieved_docs": [], "trace": trace}


def search_node(state: ResearchState) -> Dict[str, Any]:
    """Search the web using Tavily API (always combined with local corpus retrieval)."""
    print(f"Searching the web for: {state['query']}")

    trace = list(state.get("trace", []))

    try:
        search = TavilySearch(max_results=5)
        raw = search.invoke({"query": state["query"]})
        print(f"Tavily raw response type: {type(raw)}, value: {str(raw)[:500]}")

        if isinstance(raw, dict) and "results" in raw:
            results = raw["results"]
        elif isinstance(raw, list):
            results = raw
        else:
            print(f"WARNING: Unexpected Tavily response format: {raw}")
            results = []
    except Exception as e:
        print(f"ERROR: Tavily search failed: {e}")
        results = []

    trace.append({
        "node": "search",
        "detail": f"Tavily returned {len(results)} web result(s)",
        "ts": time.time(),
    })

    print(f"Search returned {len(results)} result(s)")
    return {
        "search_results": results,
        "iterations": state.get("iterations", 0) + 1,
        "trace": trace,
    }

def analyse_node(state: ResearchState) -> Dict[str, Any]:
    """Analyse and summarise using the local corpus + Tavily web results."""
    print("Analysing with Claude on Bedrock (hybrid: docs + web)...")

    trace = list(state.get("trace", []))
    retrieved = state.get("retrieved_docs", []) or []
    web_results = state.get("search_results", []) or []

    if not retrieved and not web_results:
        trace.append({
            "node": "analyse",
            "detail": "No internal documents and no web results — analysis skipped",
            "ts": time.time(),
        })
        return {
            "summary": (
                "SEARCH_FAILED: No internal documents and Tavily returned no web results for this query."
            ),
            "trace": trace,
        }

    llm = get_bedrock_llm()

    formatted_docs = ""
    if retrieved:
        for i, doc in enumerate(retrieved, 1):
            src = doc.get("source", "internal")
            content = doc.get("content", "")[:600]
            formatted_docs += f"\n--- Internal Document {i} (source: {src}) ---\n{content}\n"

    formatted_web = ""
    for i, result in enumerate(web_results, 1):
        formatted_web += f"\n--- Web Result {i} ---\n"
        formatted_web += f"Title: {result.get('title', 'N/A')}\n"
        formatted_web += f"URL: {result.get('url', 'N/A')}\n"
        formatted_web += f"Content: {result.get('content', 'N/A')[:500]}...\n"

    context_label = []
    if retrieved:
        context_label.append("INTERNAL RESEARCH DOCUMENTS (from curated corpus)")
    if web_results:
        context_label.append("WEB SEARCH RESULTS (from Tavily)")

    prompt = f"""You are a factual research assistant. Your job is to produce a concise, accurate summary that answers the user's query.

You have access to two sources of information:
- A small curated INTERNAL research corpus (vector-retrieved passages)
- Fresh WEB search results from Tavily

CRITICAL RULES:
- You MUST use only the information from the provided sources — do not add, invent, or withhold anything.
- Clearly distinguish between internal documents and web sources when they disagree.
- If a source says X happened, report that source says X happened.
- If sources conflict, note the conflict.
- Prefer the internal corpus for claims that appear there.
- Do NOT refuse to summarise because the topic is sensitive.

QUERY: {state['query']}

{formatted_docs}

{formatted_web}

Write a concise factual summary drawing on BOTH the internal documents and web results (when present).
SUMMARY:"""

    summary = _aimessage_text(llm.invoke(prompt))
    print(f"Analyse summary (first 300 chars): {summary[:300]}")

    trace.append({
        "node": "analyse",
        "detail": f"Analysed hybrid context ({len(retrieved)} internal passages + {len(web_results)} web results)",
        "ts": time.time(),
    })

    return {
        "summary": summary,
        "trace": trace,
    }

def should_continue(state: ResearchState) -> Literal["analyse", "finalise"]:
    """Decide whether to continue research or finalise the answer"""
    if state.get("iterations", 0) >= state.get("max_iterations", 2):
        return "finalise"

    if state.get("summary"):
        return "finalise"
    
    return "analyse"

def finalise_node(state: ResearchState) -> Dict[str, Any]:
    """Generate final polished answer with Claude Sonnet."""
    print("Generate final answer with Claude Sonnet")

    trace = list(state.get("trace", []))
    summary = state.get("summary", "")

    if summary.startswith("SEARCH_FAILED:"):
        trace.append({
            "node": "finalise",
            "detail": "Finalised with failure notice (no usable sources)",
            "ts": time.time(),
        })
        return {
            "answer": (
                "Sorry, neither the internal research corpus nor the web search returned useful results for your question. "
                "This can happen when the corpus is too narrow or the search provider filters the query."
            ),
            "trace": trace,
        }

    llm = get_bedrock_llm()

    prompt = f"""You are a research assistant writing a final answer based solely on a research summary.

CRITICAL RULES:
- Report only what the summary states — do not add or invent information.
- Do NOT refuse or hedge because the topic is sensitive or involves conflict. Your role is to present what was found.
- If the summary contains information, present it clearly.
- If the summary itself says nothing useful was found, say so briefly — do not write a long disclaimer.
- When the summary references internal documents or web URLs, include the most relevant ones in the answer.

QUERY: {state['query']}

RESEARCH SUMMARY:
{state.get('summary', 'No summary available')}

FORMAT:
- Brief executive summary (2-3 sentences)
- Key findings with headings and bullet points
- Source references (document names from the internal corpus and/or web URLs) when available
- Short "Key Takeaways" section

FINAL ANSWER:"""
    
    answer = _aimessage_text(llm.invoke(prompt))

    trace.append({
        "node": "finalise",
        "detail": "Produced final structured answer",
        "ts": time.time(),
    })

    return {"answer": answer, "trace": trace}

def create_agent():
    """Create and compile the LangGraph agent workflow.

    Flow: retrieve (local corpus) → search (web) → analyse → finalise
    Steps are recorded in state.trace for the UI.
    """
    builder = StateGraph(ResearchState)
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("search", search_node)
    builder.add_node("analyse", analyse_node)
    builder.add_node("finalise", finalise_node)

    builder.set_entry_point("retrieve")
    builder.add_edge("retrieve", "search")
    builder.add_edge("search", "analyse")
    builder.add_edge("analyse", "finalise")
    builder.add_edge("finalise", END)

    # Use in-memory checkpointer for local runs (avoids needing DynamoDB tables)
    use_memory = os.environ.get("USE_MEMORY_CHECKPOINTER", "").lower() in ("1", "true", "yes")
    if use_memory:
        checkpointer: Any = MemorySaver()
    else:
        checkpointer = DynamoDBSaver(
            checkpoints_table_name=os.environ.get("CHECKPOINTS_TABLE", "langgraph-checkpoints"),
            writes_table_name=os.environ.get("WRITES_TABLE", "langgraph-writes"),
        )

    return builder.compile(checkpointer=checkpointer)

if __name__ == "__main__":
    print("Starting LangGraph Research Agent...")
    print("=" * 60)

    os.environ.setdefault("USE_MEMORY_CHECKPOINTER", "true")

    agent = create_agent()

    test_query = "What did our internal research conclude about Lambda cold starts and mitigation patterns?"

    print(f"Research query: {test_query}")
    print("-" * 60)

    config = {
        "configurable": {
            "thread_id": "test-session-001",
        }
    }

    result = agent.invoke(
        {
            "query": test_query,
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

    print("\n" + "=" * 60)
    print("EXECUTION TRACE (steps & decisions):")
    print("=" * 60)
    for step in result.get("trace", []):
        print(f"• {step.get('node')}: {step.get('detail')}")

    print("\n" + "=" * 60)
    print("FINAL ANSWER:")
    print("=" * 60)
    print(result["answer"])
    print("\n" + "=" * 60)
    print(f"✅ Research completed in {result.get('iterations', 0)} iteration(s)")
