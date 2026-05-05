"""Shared I/O helpers for initial EDA scripts."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import matplotlib
import pandas as pd

SCHEMA_VERSION = "1.0"
RESULTS_ENV_VAR = "INITIAL_EDA_RUN_ID"
DEFAULT_DATASET_ENV_VAR = "INITIAL_EDA_DATASET"

REQUIRED_RESULT_KEYS = {
    "schema_version",
    "analysis",
    "run_id",
    "dataset_path",
    "git_commit",
    "filters",
    "row_count_input",
    "row_count_after_filters",
    "metrics",
    "figures",
    "warnings",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_dataset_path() -> Path:
    from_env = os.getenv(DEFAULT_DATASET_ENV_VAR)
    if from_env:
        return Path(from_env).expanduser().resolve()
    return repo_root() / "data" / "dataset.parquet"


def ensure_agg_backend() -> None:
    matplotlib.use("Agg")


def load_dataframe(dataset_path: str | Path | None = None) -> pd.DataFrame:
    path = Path(dataset_path) if dataset_path else default_dataset_path()
    if not path.is_file():
        msg = f"Dataset parquet not found: {path}"
        raise FileNotFoundError(msg)
    return pd.read_parquet(path)


def make_run_dir(analysis_slug: str, batch_id: str, output_root: Path | None = None) -> Path:
    root = output_root or (repo_root() / "experiments" / "initial_eda_2026_05_04" / "results")
    out_dir = root / analysis_slug / batch_id
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def git_commit_hash() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            cwd=repo_root(),
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        return None
    return result.stdout.strip() or None


def save_figure(fig: Any, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=160)


def write_results_json(
    run_dir: Path,
    *,
    analysis: str,
    batch_id: str,
    dataset_path: str,
    row_count_input: int,
    row_count_after_filters: int,
    filters: dict[str, Any],
    figures: list[str],
    metrics: dict[str, Any],
    warnings: list[str],
) -> Path:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "analysis": analysis,
        "run_id": batch_id,
        "dataset_path": dataset_path,
        "git_commit": git_commit_hash(),
        "filters": filters,
        "row_count_input": int(row_count_input),
        "row_count_after_filters": int(row_count_after_filters),
        "metrics": metrics,
        "figures": [{"file": file_name, "title": file_name} for file_name in figures],
        "warnings": warnings,
    }
    output = run_dir / "results.json"
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return output

