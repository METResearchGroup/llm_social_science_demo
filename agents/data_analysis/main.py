"""CLI entrypoint for the data analysis agent."""

import typer

from agents.data_analysis.agent import run_query
from lib.env_vars_loader import EnvVarsLoader

# Load repo-root `.env` before LLM-backed router reads `os.environ`.
EnvVarsLoader.load_env_vars()


def main(user_query: str = typer.Option(..., "--user-query")) -> None:
    """Run a single natural-language query through the data analysis graph."""
    run_query(user_query)


if __name__ == "__main__":
    typer.run(main)
