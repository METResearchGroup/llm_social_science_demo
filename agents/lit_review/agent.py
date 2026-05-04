"""LangGraph implementation of a basic lit review agent.

Run from the repo root:

PYTHONPATH=. uv run python main.py --query "your topic"
"""
import pathlib

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from agents.lit_review.nodes import (
    NUM_DIVERSIFIED_QUERIES,
    collect_query,
    diversify_queries,
    draft_summary,
    get_human_feedback,
    merge_paper_results,
    tavily_search,
)
from agents.lit_review.state import AgentState

current_dir = pathlib.Path(__file__).parent
visualization_path = current_dir / "visualization.png"


def fan_out_tavily(state: AgentState) -> list[Send]:
    """Map each diversified query to a parallel ``tavily_search`` task."""
    qs = state.get("search_queries") or []
    n = NUM_DIVERSIFIED_QUERIES
    if len(qs) != n:
        raise ValueError(f"Expected exactly {n} search_queries after diversify, got {len(qs)}.")
    return [
        Send("tavily_search", {"worker_query": q, "worker_id": i})
        for i, q in enumerate(qs)
    ]


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("collect_query", collect_query)
    graph.add_node("diversify_queries", diversify_queries)
    graph.add_node("tavily_search", tavily_search)
    graph.add_node("merge_paper_results", merge_paper_results)
    graph.add_node("get_human_feedback", get_human_feedback)
    graph.add_node("draft_summary", draft_summary)

    graph.add_edge(START, "collect_query")
    graph.add_edge("collect_query", "diversify_queries")
    graph.add_conditional_edges("diversify_queries", fan_out_tavily, ["tavily_search"])
    graph.add_edge("tavily_search", "merge_paper_results")
    graph.add_edge("merge_paper_results", "get_human_feedback")
    graph.add_edge("get_human_feedback", "draft_summary")
    graph.add_edge("draft_summary", END)

    return graph.compile()


def visualize_graph(app):
    """Generate and save a visualization of the graph"""
    try:
        from IPython.display import Image, display

        graph_image = app.get_graph().draw_mermaid_png()

        with open(visualization_path, "wb") as f:
            f.write(graph_image)

        print(f"✅ Graph visualization saved to {visualization_path}")

        try:
            display(Image(graph_image))
        except Exception:
            pass

    except Exception as e:
        print(f"⚠️  Could not generate visual: {e}")
        print("Falling back to ASCII representation...")
        print(app.get_graph().draw_ascii())
