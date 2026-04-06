"""
LangGraph Research Agent
"""

import os
from pathlib import Path
from typing import TypedDict, List, Dict, Any, Literal
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_aws import ChatBedrockConverse
from langchain_tavily import TavilySearch
from langgraph_checkpoint_dynamodb.saver import DynamoDBSaver

_backend_dir = Path(__file__).resolve().parent
load_dotenv(_backend_dir / ".env")
load_dotenv(_backend_dir.parent / ".env")  # optional repo-root .env

# ChatBedrockConverse may return AIMessage.content as plain text or a list of content blocks.
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


# That's the state used to track the agent's progress
class ResearchState(TypedDict):
    query: str                    # User's research question
    search_results: List[Dict]    # Raw search results from Tavily
    summary: str                  # Summarized findings
    answer: str                   # Final polished answer
    iterations: int               # Current loop counter
    max_iterations: int           # Safety limit to prevent infinite loops

def get_bedrock_llm():
    """Claude on Bedrock in eu-west-2 must use an EU inference profile ID (eu.*), not a raw foundation model ID."""
    return ChatBedrockConverse(
        model=os.environ.get("BEDROCK_MODEL_ID", "eu.anthropic.claude-sonnet-4-6"),
        region_name="eu-west-2",
        temperature=0.3,
        max_tokens=2000,
    )

# Node for searching the web
def search_node(state: ResearchState) -> Dict[str, Any]:
    """Search the web using Tavily API"""
    print(f"Searching the web for: {state['query']}")

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

    print(f"Search returned {len(results)} result(s)")
    return {
        "search_results": results,
        "iterations": state.get("iterations", 0) + 1,
    }

# Node for analysing
def analyse_node(state: ResearchState) -> Dict[str, Any]:
    """Analyse and summarise the search results with Claude Sonnet"""
    print("Analysing with Claude on Bedrock...")

    if not state.get("search_results"):
        return {
            "summary": (
                "SEARCH_FAILED: Tavily returned no results for this query. "
                "This may be due to content filtering, an invalid API key, or a temporary outage."
            ),
        }

    llm = get_bedrock_llm()

    # Format search results for better readability by the LLM
    formatted_results = ""
    for i, result in enumerate(state["search_results"], 1):
        formatted_results += f"\n--- Result {i} ---\n"
        formatted_results += f"Title: {result.get('title', 'N/A')}\n"
        formatted_results += f"URL: {result.get('url', 'N/A')}\n"
        formatted_results += f"Content: {result.get('content', 'N/A')[:500]}...\n"

    prompt = f"""You are a factual research assistant. Your job is to summarise the search results below.

CRITICAL RULES:
- You MUST use only the information from the search results provided — do not add, invent, or withhold anything.
- Do NOT refuse to summarise because the topic is sensitive. Your role is to report what the sources say, not to judge the topic.
- If a source says X happened, report that source says X happened.
- If sources conflict, note the conflict.
- Do NOT say you "cannot confirm" things that are directly stated in the results.

QUERY: {state['query']}

SEARCH RESULTS:
{formatted_results}

Write a concise factual summary of what the search results say about the query above.
SUMMARY:"""

    summary = _aimessage_text(llm.invoke(prompt))
    print(f"Analyse summary (first 300 chars): {summary[:300]}")
    return {
        "summary": summary
    }

# Decision logic
def should_continue(state: ResearchState) -> Literal["analyse", "finalise"]:
    """Decide whether to continue research or finalise the answer"""

    # prevent infinite loops
    if state.get("iterations", 0) >= state.get("max_iterations", 2):
        return "finalise"

    if state.get("summary"):
        return "finalise"
    
    return "analyse"

# Node for finalising the answer
def finalise_node(state: ResearchState) -> Dict[str, Any]:
    """Generate final polished answer with Claude Sonnet"""
    print("Generate final answer with Claude Sonnet")

    summary = state.get("summary", "")
    if summary.startswith("SEARCH_FAILED:"):
        return {
            "answer": (
                "Sorry, the web search didn't return any results for your question. "
                "This can happen when the search provider filters the query or the API key is misconfigured. "
                "Please try rephrasing your question or check the Lambda logs for details."
            )
        }

    llm = get_bedrock_llm()

    prompt = f"""You are a research assistant writing a final answer based solely on a research summary.

CRITICAL RULES:
- Report only what the summary states — do not add or invent information.
- Do NOT refuse or hedge because the topic is sensitive or involves conflict. Your role is to present what was found.
- If the summary contains information, present it clearly.
- If the summary itself says nothing useful was found, say so briefly — do not write a long disclaimer.

QUERY: {state['query']}

RESEARCH SUMMARY:
{state.get('summary', 'No summary available')}

FORMAT:
- Brief executive summary (2-3 sentences)
- Key findings with headings and bullet points
- Source URLs where available
- Short "Key Takeaways" section

FINAL ANSWER:"""
    
    answer = _aimessage_text(llm.invoke(prompt))
    return {"answer": answer}

# Built the Graph
def create_agent():
    """Create and compile the LangGraph agent workflow"""

    builder = StateGraph(ResearchState)
    builder.add_node("search", search_node)
    builder.add_node("analyse", analyse_node)
    builder.add_node("finalise", finalise_node)

    # Add Edges (connections between the nodes)
    builder.set_entry_point("search")
    builder.add_edge("search", "analyse")
    builder.add_conditional_edges(
        "analyse",
        should_continue,
        {
            "analyse": "analyse",
            "finalise": "finalise",
        }
    )
    builder.add_edge("finalise", END)

    # Create DynamoDB checkpointer for state persistence
    checkpointer = DynamoDBSaver(
        checkpoints_table_name=os.environ.get("CHECKPOINTS_TABLE", "langgraph-checkpoints"),
        writes_table_name=os.environ.get("WRITES_TABLE", "langgraph-writes"),
    )

    # Compile the graph with the checkpointer
    return builder.compile(checkpointer=checkpointer)

if __name__ == "__main__":
    print("Starting LangGraph Research Agent...")
    print("=" * 60)

    agent = create_agent()

    test_query = "What are the key benefits and challenges of serverless computing for startups in 2026?"

    print(f"Research query: {test_query}")
    print("-" * 60)

    # Add a thread_id to persist state across multiple runs
    config = {
        "configurable": {
            "thread_id": "test-session-001",
        }
    }

    result = agent.invoke({
        "query": test_query,
        "iterations": 0,
        "max_iterations": 2,
        "search_results": [],
        "summary": "",
        "answer": "",
    }, config=config)

     
    print("\n" + "=" * 60)
    print("FINAL ANSWER:")
    print("=" * 60)
    print(result["answer"])
    print("\n" + "=" * 60)
    print(f"✅ Research completed in {result.get('iterations', 0)} iteration(s)")
