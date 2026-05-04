"""Backward-compatible root entrypoint.

Primary CLI now lives at ``agents/lit_review/main.py``.
"""

import typer

from agents.lit_review.main import main


if __name__ == "__main__":
    typer.run(main)
