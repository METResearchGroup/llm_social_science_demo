"""LangGraph v1 data-analysis agent with deterministic routing.

To run:

PYTHONPATH=. uv run python agents/data_analysis/main.py --user-query "Can you find trends in the conversation between first message and the rest of the messages in a conversation?"

"""

from __future__ import annotations

import pathlib

import typer
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from agents.data_analysis.nodes import (
    finalize_report,
    ingest_question,
    interpret_results,
    load_dataset_context,
    merge_results,
    plan_analysis,
    route_query_answerability,
    unanswerable_query,
    worker_analyze,
)
from agents.data_analysis.state import AgentState
from lib.env_vars_loader import EnvVarsLoader

# Keep direct module execution consistent with CLI env loading behavior.
EnvVarsLoader.load_env_vars()

current_dir = pathlib.Path(__file__).parent
visualization_path = current_dir / "visualization.png"


def fan_out_subtasks(state: AgentState) -> list[Send]:
    """Map each planned subtask to a parallel worker node."""
    subtasks = state.get("subtasks") or []
    if not subtasks:
        raise ValueError("Expected at least one subtask from plan_analysis.")
    return [
        Send("worker_analyze", {"worker_id": i, "worker_spec": subtask})
        for i, subtask in enumerate(subtasks)
    ]


def build_graph():
    """Build and compile the data-analysis LangGraph."""
    graph = StateGraph(AgentState)

    graph.add_node("ingest_question", ingest_question)
    graph.add_node("unanswerable_query", unanswerable_query)
    graph.add_node("load_dataset_context", load_dataset_context)
    graph.add_node("plan_analysis", plan_analysis)
    graph.add_node("worker_analyze", worker_analyze)
    graph.add_node("merge_results", merge_results)
    graph.add_node("interpret_results", interpret_results)
    graph.add_node("finalize_report", finalize_report)

    graph.add_edge(START, "ingest_question")
    graph.add_conditional_edges(
        "ingest_question",
        route_query_answerability,
        {
            "answerable": "load_dataset_context",
            "unanswerable": "unanswerable_query",
        },
    )
    graph.add_edge("load_dataset_context", "plan_analysis")
    graph.add_conditional_edges("plan_analysis", fan_out_subtasks, ["worker_analyze"])
    graph.add_edge("worker_analyze", "merge_results")
    graph.add_edge("merge_results", "interpret_results")
    graph.add_edge("interpret_results", "finalize_report")
    graph.add_edge("finalize_report", END)
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
