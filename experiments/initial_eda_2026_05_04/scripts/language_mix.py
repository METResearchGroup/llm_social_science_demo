"""EDA Q1: language mix among user turns."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from eda_io import (
    batch_id_from_env_or_cli,
    column_warnings,
    dataset_path_for_json,
    default_output_root,
    default_parquet_path,
    make_run_dir,
    setup_matplotlib_agg,
    write_results_json,
)

ANALYSIS = "language_mix"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Language mix among user turns.")
    p.add_argument("--parquet", type=Path, default=None, help="Parquet path (default: data/dataset.parquet)")
    p.add_argument("--batch-id", type=str, default=None, help="Batch folder name (or SHARECHAT_EDA_BATCH_ID)")
    p.add_argument("--output-root", type=Path, default=None, help="Root under results/")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    batch_id = batch_id_from_env_or_cli(args.batch_id)
    if not batch_id:
        print("error: --batch-id or SHARECHAT_EDA_BATCH_ID is required for non-interactive runs")
        return 2

    parquet = (args.parquet or default_parquet_path()).resolve()
    output_root = (args.output_root or default_output_root()).resolve()

    df = pd.read_parquet(parquet)
    row_in = len(df)
    warnings = column_warnings(list(df.columns))

    user = df[df["role"].astype(str).str.lower() == "user"].copy()
    user = user[user["plain_text"].notna() & (user["plain_text"].astype(str).str.len() > 0)]
    row_after = len(user)

    lang = user["detected_language_final"].fillna("(missing)").astype(str)
    counts = lang.value_counts()
    top_n = counts.head(20)
    is_english = lang.str.lower().isin({"english", "en"})
    english_share = float(is_english.mean()) if row_after else 0.0

    metrics: dict = {
        "language_counts_top20": {str(k): int(v) for k, v in top_n.items()},
        "english_share_user_turns": english_share,
        "non_english_share_user_turns": 1.0 - english_share,
        "n_distinct_languages_observed": int(lang.nunique()),
    }

    setup_matplotlib_agg()
    run_dir = make_run_dir(analysis_slug=ANALYSIS, batch_id=batch_id, output_root=output_root)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    top_n.plot(kind="bar", ax=axes[0], color="steelblue")
    axes[0].set_title("Top languages (user turns)")
    axes[0].set_xlabel("detected_language_final")
    axes[0].tick_params(axis="x", rotation=45)

    axes[1].bar(["English", "Non-English"], [english_share, 1.0 - english_share], color=["#2ca02c", "#ff7f0e"])
    axes[1].set_ylim(0, 1)
    axes[1].set_title("English vs non-English (user turns)")
    fig.tight_layout()
    fig_path = run_dir / "visuals.png"
    fig.savefig(fig_path, dpi=150)
    plt.close(fig)

    figures = ["visuals.png"]
    write_results_json(
        run_dir,
        analysis=ANALYSIS,
        batch_id=batch_id,
        dataset_path=dataset_path_for_json(parquet),
        row_count_input=row_in,
        row_count_after_filters=row_after,
        filters={"role": "user", "non_empty_plain_text": True},
        figures=figures,
        metrics=metrics,
        warnings=warnings,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
