"""EDA Q2: first user turn vs later user turns (per conversation url)."""

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

ANALYSIS = "first_vs_later_user_turn"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="First vs later user turns by conversation.")
    p.add_argument("--parquet", type=Path, default=None)
    p.add_argument("--batch-id", type=str, default=None)
    p.add_argument("--output-root", type=Path, default=None)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    batch_id = batch_id_from_env_or_cli(args.batch_id)
    if not batch_id:
        print("error: --batch-id or SHARECHAT_EDA_BATCH_ID is required")
        return 2

    parquet = (args.parquet or default_parquet_path()).resolve()
    output_root = (args.output_root or default_output_root()).resolve()

    df = pd.read_parquet(parquet)
    row_in = len(df)
    warnings = column_warnings(list(df.columns))

    u = df[df["role"].astype(str).str.lower() == "user"].copy()
    u = u[u["plain_text"].notna()]
    u["text_len"] = u["plain_text"].astype(str).str.len()
    u = u.sort_values(["url", "message_index"])
    u["_user_ord"] = u.groupby("url", sort=False).cumcount()
    u["is_first_user"] = u["_user_ord"] == 0

    first = u[u["is_first_user"]]["text_len"]
    later = u[~u["is_first_user"]]["text_len"]
    row_after = len(u)

    metrics: dict = {
        "first_user_turn_n": int(len(first)),
        "later_user_turn_n": int(len(later)),
        "first_mean_len": float(first.mean()) if len(first) else None,
        "first_median_len": float(first.median()) if len(first) else None,
        "later_mean_len": float(later.mean()) if len(later) else None,
        "later_median_len": float(later.median()) if len(later) else None,
    }

    if "topic" in u.columns and u["topic"].notna().any():
        first_topics = u[u["is_first_user"]]["topic"].dropna().astype(str)
        later_topics = u[~u["is_first_user"]]["topic"].dropna().astype(str)
        metrics["first_topic_top10"] = first_topics.value_counts().head(10).to_dict()
        metrics["later_topic_top10"] = later_topics.value_counts().head(10).to_dict()

    setup_matplotlib_agg()
    run_dir = make_run_dir(analysis_slug=ANALYSIS, batch_id=batch_id, output_root=output_root)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    if len(first):
        axes[0].hist(first, bins=50, alpha=0.7, label="first", color="C0", density=True)
    if len(later):
        axes[0].hist(later, bins=50, alpha=0.7, label="later", color="C1", density=True)
    axes[0].set_title("User message length (chars)")
    axes[0].legend()

    data_box = [first, later] if len(first) and len(later) else []
    if data_box:
        axes[1].boxplot(data_box, tick_labels=["first", "later"], showfliers=False)
    axes[1].set_title("Length distribution (boxplot)")
    fig.tight_layout()
    fig_path = run_dir / "visuals.png"
    fig.savefig(fig_path, dpi=150)
    plt.close(fig)

    write_results_json(
        run_dir,
        analysis=ANALYSIS,
        batch_id=batch_id,
        dataset_path=dataset_path_for_json(parquet),
        row_count_input=row_in,
        row_count_after_filters=row_after,
        filters={"role": "user", "sorted_by": ["url", "message_index"]},
        figures=["visuals.png"],
        metrics=metrics,
        warnings=warnings,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
