"""Regenerate the data-analysis graph visualization image.

Run from repository root:

PYTHONPATH=. uv run python agents/data_analysis/visualize_graph.py
"""

from agents.data_analysis.agent import build_graph, visualize_graph


def main() -> None:
    app = build_graph()
    visualize_graph(app)


if __name__ == "__main__":
    main()
