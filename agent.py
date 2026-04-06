"""
LangGraph Research Agent
"""

import os
from typing import TypedDict, List, Dict, Any, Literal
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_aws import ChatBedrockConverse
from langchain_tavily import TavilySearch
from langgraph_checkpoint_dynamodb.saver import DynamoDBSaver

load_dotenv()

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

    search = TavilySearch(max_results=5)
    raw = search.invoke({"query": state["query"]})
    if isinstance(raw, dict) and "results" in raw:
        results = raw["results"]
    elif isinstance(raw, list):
        results = raw
    else:
        results = []

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
            "summary": "No search results found.",
        }

    llm = get_bedrock_llm()

    # Format search results for better readability by the LLM
    formatted_results = ""
    for i, result in enumerate(state["search_results"], 1):
        formatted_results += f"\n--- Result {i} ---\n"
        formatted_results += f"Title: {result.get('title', 'N/A')}\n"
        formatted_results += f"URL: {result.get('url', 'N/A')}\n"
        formatted_results += f"Content: {result.get('content', 'N/A')[:500]}...\n"

    prompt = f"""
    You are a research assistant. Based on these search results, provide a comprehensive summary answering: {state['query']}

    SEARCH RESULTS:
    {formatted_results}

    QUERY: {state['query']}

    INSTRUCTIONS:
    1. Synthesize information from all relevant sources
    2. Identify key themes and insights
    3. Note any conflicting information between sources
    4. Provide a balanced, accurate summary
    
    SUMMARY:
    """

    summary = _aimessage_text(llm.invoke(prompt))
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

    llm = get_bedrock_llm()

    prompt = f"""
    Based on this research summary, write a clear, well-structured answer to: {state['query']}
    
    RESEARCH SUMMARY:
    {state.get('summary', 'No summary available')}
    
    FORMAT REQUIREMENTS:
    - Start with a brief executive summary (2-3 sentences)
    - Use clear headings and bullet points where appropriate
    - Cite key sources by referencing the source URLs
    - Include a "Key Takeaways" section at the end
    - Keep the tone professional and informative
    
    FINAL ANSWER:
    """
    
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
