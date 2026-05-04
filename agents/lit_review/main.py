"""CLI entrypoint for the literature review agent.

Run from the repo root:

PYTHONPATH=. uv run python main.py --query "your topic"
PYTHONPATH=. uv run python -m agents.lit_review.main --query "your topic"
"""

from __future__ import annotations

import asyncio
from typing import Optional

import typer

from agents.lit_review.agent import build_graph, visualize_graph
from lib.env_vars_loader import EnvVarsLoader

# Load repo-root `.env` before any agent/MCP code reads `os.environ`.
EnvVarsLoader.load_env_vars()


def _initial_state(query: str) -> dict:
    return {
        "messages": [],
        "query": query,
        "search_queries": [],
        "tavily_raw_hits": [],
        "papers": [],
        "human_feedback": [],
        "summary": "",
    }


def main(
    query: Optional[str] = typer.Option(
        None,
        "--query",
        "-q",
        help="Research query. If omitted, you will be prompted interactively.",
    ),
    visualize: bool = typer.Option(
        False,
        "--visualize",
        "-v",
        help="Save LangGraph diagram to agents/lit_review/visualization.png",
    ),
) -> None:
    graph_app = build_graph()
    if visualize:
        visualize_graph(graph_app)
    try:
        result = asyncio.run(graph_app.ainvoke(_initial_state(query or "")))
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(result.get("summary") or "Run finished (no summary yet).")


if __name__ == "__main__":
    typer.run(main)
