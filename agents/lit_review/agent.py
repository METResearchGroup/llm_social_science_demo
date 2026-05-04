"""LangGraph implementation of a basic lit review agent.

Run from the repo root:

PYTHONPATH=. uv run python main.py run
"""
import pathlib
from langgraph.graph import StateGraph, START, END

from agents.lit_review.nodes import (
    collect_query,
    draft_summary,
    get_human_feedback,
    get_papers,
)
from agents.lit_review.state import AgentState

current_dir = pathlib.Path(__file__).parent
visualization_path = current_dir / "visualization.png"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("collect_query", collect_query)
    graph.add_node("get_papers", get_papers)
    graph.add_node("get_human_feedback", get_human_feedback)
    graph.add_node("draft_summary", draft_summary)

    graph.add_edge(START, "collect_query")
    graph.add_edge("collect_query", "get_papers")
    graph.add_edge("get_papers", "get_human_feedback")
    graph.add_edge("get_human_feedback", "draft_summary")
    graph.add_edge("draft_summary", END)

    # compile
    app = graph.compile()

    return app

def visualize_graph(app):
    """Generate and save a visualization of the graph"""
    try:
        from IPython.display import Image, display
        
        # Generate the graph image
        graph_image = app.get_graph().draw_mermaid_png()
        
        # Save to file
        with open(visualization_path, "wb") as f:
            f.write(graph_image)
        
        print(f"✅ Graph visualization saved to {visualization_path}")
        
        # Display in Jupyter if available
        try:
            display(Image(graph_image))
        except:
            pass
            
    except Exception as e:
        print(f"⚠️  Could not generate visual: {e}")
        print("Falling back to ASCII representation...")
        print(app.get_graph().draw_ascii())
