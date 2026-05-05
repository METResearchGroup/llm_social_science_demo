"""LangGraph scaffold for a basic data analysis agent.

To run:

PYTHONPATH=. uv run python agents/data_analysis/agent.py --user-query "Can you find trends in the conversation between first message and the rest of the messages in a conversation?"

"""

from __future__ import annotations

import operator
import pathlib
from typing import Annotated, Any, NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import Send

current_dir = pathlib.Path(__file__).parent
visualization_path = current_dir / "visualization.png"


class AgentState(TypedDict):
    """State passed between data-analysis nodes."""

    # Conversation context
    messages: Annotated[list, add_messages]
    user_query: str
    analysis_goal: str

    # Data context
    data_ref: str
    schema_digest: str

    # Planning + fan-out
    subtasks: list[dict[str, Any]]
    worker_id: NotRequired[int]
    worker_spec: NotRequired[dict[str, Any]]

    # Worker and merged outputs
    worker_outputs: Annotated[list[dict[str, Any]], operator.add]
    merged_results: dict[str, Any]

    # Final narrative output
    narrative: str
    report: str


def ingest_question(state: AgentState) -> dict[str, Any]:
    """Normalize user query into an analysis goal."""
    query = (state.get("user_query") or "").strip()
    return {
        "analysis_goal": query or "Summarize the dataset and answer the user question.",
    }


def load_context(state: AgentState) -> dict[str, Any]:
    """Load or summarize data context.

    Stub behavior:
    - Preserves provided data_ref when present.
    - Emits a placeholder schema digest.
    """
    data_ref = state.get("data_ref") or "TODO: set dataset path or table reference"
    schema_digest = (
        state.get("schema_digest")
        or "TODO: populate schema digest (columns, dtypes, row count, key fields)"
    )
    return {"data_ref": data_ref, "schema_digest": schema_digest}


def plan_analysis(state: AgentState) -> dict[str, Any]:
    """Create bounded subtasks from the analysis goal.

    Stub behavior:
    - Produces two generic subtasks so fan-out wiring is visible.
    """
    goal = state.get("analysis_goal") or "Understand the dataset"
    subtasks = [
        {"name": "baseline_summary", "instruction": f"Create baseline summary for: {goal}"},
        {"name": "focused_slice", "instruction": f"Analyze one focused slice for: {goal}"},
    ]
    return {"subtasks": subtasks}


def fan_out_subtasks(state: AgentState) -> list[Send]:
    """Map each planned subtask to a parallel worker node."""
    subtasks = state.get("subtasks") or []
    if not subtasks:
        raise ValueError("Expected at least one subtask from plan_analysis.")
    return [
        Send("worker_analyze", {"worker_id": i, "worker_spec": subtask})
        for i, subtask in enumerate(subtasks)
    ]


def worker_analyze(state: AgentState) -> dict[str, Any]:
    """Run one subtask analysis.

    Stub behavior:
    - Returns deterministic placeholder output per worker.
    """
    worker_id = state.get("worker_id", -1)
    worker_spec = state.get("worker_spec") or {}
    output = {
        "worker_id": worker_id,
        "status": "stubbed",
        "subtask": worker_spec,
        "preview": "TODO: attach dataframe preview or aggregate metrics.",
        "artifacts": [],
    }
    return {"worker_outputs": [output]}


def merge_results(state: AgentState) -> dict[str, Any]:
    """Merge all worker outputs into one object."""
    outputs = state.get("worker_outputs") or []
    merged = {
        "num_workers": len(outputs),
        "workers": outputs,
    }
    return {"merged_results": merged}


def interpret_results(state: AgentState) -> dict[str, Any]:
    """Generate narrative interpretation from merged worker outputs."""
    merged = state.get("merged_results") or {}
    worker_count = merged.get("num_workers", 0)
    narrative = (
        "Stub interpretation: completed "
        f"{worker_count} analysis branch(es). Replace with grounded findings and caveats."
    )
    return {"narrative": narrative}


def finalize_report(state: AgentState) -> dict[str, Any]:
    """Compose final report text."""
    goal = state.get("analysis_goal") or "N/A"
    narrative = state.get("narrative") or "No narrative generated."
    report = "\n".join(
        [
            "# Data Analysis Agent Report (Stub)",
            "",
            f"Goal: {goal}",
            "",
            "## Interpretation",
            narrative,
        ]
    )
    return {"report": report}


def build_graph():
    """Build and compile the data analysis LangGraph."""
    graph = StateGraph(AgentState)

    graph.add_node("ingest_question", ingest_question)
    graph.add_node("load_context", load_context)
    graph.add_node("plan_analysis", plan_analysis)
    graph.add_node("worker_analyze", worker_analyze)
    graph.add_node("merge_results", merge_results)
    graph.add_node("interpret_results", interpret_results)
    graph.add_node("finalize_report", finalize_report)

    graph.add_edge(START, "ingest_question")
    graph.add_edge("ingest_question", "load_context")
    graph.add_edge("load_context", "plan_analysis")
    graph.add_conditional_edges("plan_analysis", fan_out_subtasks, ["worker_analyze"])
    graph.add_edge("worker_analyze", "merge_results")
    graph.add_edge("merge_results", "interpret_results")
    graph.add_edge("interpret_results", "finalize_report")
    graph.add_edge("finalize_report", END)

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


if __name__ == "__main__":
    graph_app = build_graph()
    visualize_graph(graph_app)
