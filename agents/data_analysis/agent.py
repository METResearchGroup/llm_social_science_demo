"""LangGraph v1 data-analysis agent with deterministic routing.

To run:

PYTHONPATH=. uv run python agents/data_analysis/main.py --user-query "Can you find trends in the conversation between first message and the rest of the messages in a conversation?"

"""

from __future__ import annotations

import pathlib
import re
from typing import Any, TypedDict

import typer
from langgraph.graph import END, START, StateGraph

from data.dataloader import DataLoader

current_dir = pathlib.Path(__file__).parent
visualization_path = current_dir / "visualization.png"


class AgentState(TypedDict, total=False):
    """State passed between data-analysis nodes."""

    user_query: str
    analysis_goal: str
    route: str
    dataframe_path: str
    analysis_result: dict[str, Any]
    report: str


def ingest_question(state: AgentState) -> dict[str, Any]:
    """Normalize user query into a canonical analysis goal string."""
    query = (state.get("user_query") or "").strip()
    goal = query or "analyze first message versus later messages"
    return {"analysis_goal": goal}


def route_query_answerability(state: AgentState) -> str:
    """Route query to answerable vs unanswerable branch."""
    query = (state.get("analysis_goal") or "").lower()
    supported_keywords = {
        "trend",
        "conversation",
        "first",
        "rest",
        "message",
        "messages",
        "turn",
        "turns",
        "length",
        "question",
        "topic",
        "language",
        "sharechat",
    }
    unsupported_keywords = {
        "weather",
        "temperature",
        "stock",
        "bitcoin",
        "tomorrow",
        "next week",
        "news",
    }

    if any(token in query for token in unsupported_keywords):
        return "unanswerable"
    if any(token in query for token in supported_keywords):
        return "answerable"
    return "unanswerable"


def unanswerable_query(_: AgentState) -> dict[str, Any]:
    """Emit exact contract string for unanswerable questions."""
    message = "this query can't be answered by the data"
    print(message)
    return {"report": message}


def load_dataset_context(_: AgentState) -> dict[str, Any]:
    """Load local parquet through DataLoader.load_data_from_local."""
    loader = DataLoader()
    _ = loader.load_data_from_local()
    return {"dataframe_path": str(loader.output_path)}


def analyze_first_vs_rest(_: AgentState) -> dict[str, Any]:
    """Compute deterministic v1 metrics for first-turn vs later turns."""
    loader = DataLoader()
    df = loader.load_data_from_local()

    working_df = df.copy()
    working_df["message_index"] = (
        working_df["message_index"].astype("string").str.extract(r"(-?\d+)", expand=False)
    )
    working_df["message_index"] = (
        working_df["message_index"]
        .fillna("-1")
        .astype(int)
    )
    working_df["plain_text"] = working_df["plain_text"].fillna("").astype(str)

    # Contract requires first-turn derivation from message_index == 0.
    # ShareChat slices may be 1-indexed, so normalize to keep the same predicate.
    index_shift = 1 if int(working_df["message_index"].min()) >= 1 else 0
    working_df["normalized_message_index"] = working_df["message_index"] - index_shift
    working_df["is_first_turn"] = working_df["normalized_message_index"] == 0
    working_df["text_length"] = working_df["plain_text"].str.len()
    working_df["has_question_mark"] = working_df["plain_text"].str.contains(r"\?")
    working_df["has_why"] = working_df["plain_text"].str.contains(r"\bwhy\b", flags=re.IGNORECASE)

    first = working_df[working_df["is_first_turn"]]
    rest = working_df[~working_df["is_first_turn"]]

    def _rate(series: Any) -> float:
        return float(series.mean()) if len(series) else 0.0

    result = {
        "counts": {
            "first_turn_rows": int(len(first)),
            "non_first_turn_rows": int(len(rest)),
        },
        "average_text_length": {
            "first_turn": round(float(first["text_length"].mean()) if len(first) else 0.0, 2),
            "non_first_turn": round(float(rest["text_length"].mean()) if len(rest) else 0.0, 2),
        },
        "question_rate": {
            "first_turn": round(_rate(first["has_question_mark"]), 4),
            "non_first_turn": round(_rate(rest["has_question_mark"]), 4),
        },
        "lexical_cue_rate_why": {
            "first_turn": round(_rate(first["has_why"]), 4),
            "non_first_turn": round(_rate(rest["has_why"]), 4),
        },
    }

    first_len = result["average_text_length"]["first_turn"]
    rest_len = result["average_text_length"]["non_first_turn"]
    first_q = result["question_rate"]["first_turn"]
    rest_q = result["question_rate"]["non_first_turn"]
    interpretation = (
        "First-turn messages are generally longer than later turns."
        if first_len > rest_len
        else "Later turns are generally longer than first-turn messages."
    )
    interpretation += (
        " First turns are more likely to contain questions."
        if first_q > rest_q
        else " Later turns are more likely to contain questions."
    )
    result["interpretation"] = interpretation
    return {"analysis_result": result}


def summarize_results(state: AgentState) -> dict[str, Any]:
    """Format final report text for the answerable path."""
    goal = state.get("analysis_goal", "")
    result = state.get("analysis_result", {})
    report = "\n".join(
        [
            "# Data Analysis Agent Report",
            "",
            f"Goal: {goal}",
            "",
            "## First-vs-rest trend metrics",
            str(result),
            "",
            "## Interpretation",
            str(result.get("interpretation", "")),
        ]
    )
    print(report)
    return {"report": report}


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
