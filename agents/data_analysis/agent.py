"""LangGraph v1 data-analysis agent with deterministic routing.

To run:

PYTHONPATH=. uv run python agents/data_analysis/main.py --user-query "Can you find trends in the conversation between first message and the rest of the messages in a conversation?"

"""

from __future__ import annotations

import pathlib

import typer
from langgraph.graph import END, START, StateGraph

from agents.data_analysis.nodes import (
    analyze_first_vs_rest,
    ingest_question,
    load_dataset_context,
    route_query_answerability,
    summarize_results,
    unanswerable_query,
)
from agents.data_analysis.state import AgentState
from lib.env_vars_loader import EnvVarsLoader

# Keep direct module execution consistent with CLI env loading behavior.
EnvVarsLoader.load_env_vars()

current_dir = pathlib.Path(__file__).parent
visualization_path = current_dir / "visualization.png"


def build_graph():
    """Build and compile the data-analysis LangGraph."""
    graph = StateGraph(AgentState)

    graph.add_node("ingest_question", ingest_question)
    graph.add_node("unanswerable_query", unanswerable_query)
    graph.add_node("load_dataset_context", load_dataset_context)
    graph.add_node("analyze_first_vs_rest", analyze_first_vs_rest)
    graph.add_node("summarize_results", summarize_results)

    graph.add_edge(START, "ingest_question")
    graph.add_conditional_edges(
        "ingest_question",
        route_query_answerability,
        {
            "answerable": "load_dataset_context",
            "unanswerable": "unanswerable_query",
        },
    )
    graph.add_edge("load_dataset_context", "analyze_first_vs_rest")
    graph.add_edge("analyze_first_vs_rest", "summarize_results")
    graph.add_edge("summarize_results", END)
    graph.add_edge("unanswerable_query", END)

    return graph.compile()


def visualize_graph(app):
    """Generate and save a visualization of the graph."""
    try:
        from IPython.display import Image, display

        graph_image = app.get_graph().draw_mermaid_png()

        with open(visualization_path, "wb") as f:
            f.write(graph_image)

        print(f"Saved graph visualization to {visualization_path}")

        try:
            display(Image(graph_image))
        except Exception:
            pass

    except Exception as exc:
        print(f"Could not generate visual: {exc}")
        print("Falling back to ASCII representation...")
        print(app.get_graph().draw_ascii())


def run_query(user_query: str) -> str:
    """Run the graph for a single query and return final report text."""
    app = build_graph()
    result = app.invoke({"user_query": user_query})
    return result.get("report", "")


def main(user_query: str = typer.Option(..., "--user-query")) -> None:
    """CLI entrypoint used by this module for backward compatibility."""
    run_query(user_query)


if __name__ == "__main__":
    typer.run(main)
