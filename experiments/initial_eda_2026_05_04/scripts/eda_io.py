"""Shared I/O helpers for ShareChat initial EDA scripts.

Output contract (results.json top-level keys) is frozen here.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "1.0"

# Required JSON keys (documentation / tests)
REQUIRED_RESULT_KEYS = frozenset(
    {
        "schema_version",
        "analysis",
        "batch_id",
        "dataset_path",
        "row_count_input",
        "row_count_after_filters",
        "filters",
        "figures",
        "metrics",
        "warnings",
    }
)


def repo_root() -> Path:
    """Repository root: parent of ``experiments/``."""
    return Path(__file__).resolve().parent.parent.parent.parent


def default_parquet_path() -> Path:
    return repo_root() / "data" / "dataset.parquet"


def default_output_root() -> Path:
    return repo_root() / "experiments" / "initial_eda_2026_05_04" / "results"


def setup_matplotlib_agg() -> None:
    import matplotlib

    matplotlib.use("Agg")


def column_warnings(df_columns: list[str]) -> list[str]:
    warnings: list[str] = []
    if "topic" not in df_columns:
        warnings.append("Column 'topic' missing; topic-stratified metrics skipped or empty.")
    if "detected_language_final" not in df_columns:
        warnings.append("Column 'detected_language_final' missing.")
    return warnings


def make_run_dir(*, analysis_slug: str, batch_id: str, output_root: Path | None = None) -> Path:
    root = output_root if output_root is not None else default_output_root()
    run_dir = root / analysis_slug / batch_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def write_results_json(
    run_dir: Path,
    *,
    analysis: str,
    batch_id: str,
    dataset_path: str,
    row_count_input: int,
    row_count_after_filters: int,
    filters: Mapping[str, Any],
    figures: list[str],
    metrics: Any,
    warnings: list[str],
) -> Path:
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "analysis": analysis,
        "batch_id": batch_id,
        "dataset_path": dataset_path,
        "row_count_input": row_count_input,
        "row_count_after_filters": row_count_after_filters,
        "filters": dict(filters),
        "figures": list(figures),
        "metrics": metrics,
        "warnings": list(warnings),
    }
    missing = REQUIRED_RESULT_KEYS - payload.keys()
    if missing:
        msg = f"Internal error: missing keys {sorted(missing)}"
        raise RuntimeError(msg)
    out = run_dir / "results.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def dataset_path_for_json(path: Path) -> str:
    """Prefer repo-relative path string when under repo root."""
    try:
        rel = path.resolve().relative_to(repo_root())
        return str(rel)
    except ValueError:
        return str(path.resolve())


def batch_id_from_env_or_cli(cli_batch_id: str | None) -> str | None:
    if cli_batch_id:
        return cli_batch_id
    return os.environ.get("SHARECHAT_EDA_BATCH_ID")
