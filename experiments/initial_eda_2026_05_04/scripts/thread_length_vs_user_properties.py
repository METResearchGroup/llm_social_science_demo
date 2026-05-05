from __future__ import annotations

import argparse
import os

import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import spearmanr

from experiments.initial_eda_2026_05_04.scripts import eda_io

ANALYSIS = "thread_length_vs_user_properties"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default=os.getenv(eda_io.RESULTS_ENV_VAR))
    parser.add_argument("--data", default=str(eda_io.default_dataset_path()))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.run_id:
        raise ValueError("run_id missing; pass --run-id or set INITIAL_EDA_RUN_ID")
    eda_io.ensure_agg_backend()
    df = eda_io.load_dataframe(args.data)
    user_df = df[df["role"].astype(str).str.lower() == "user"].copy()
    user_df["turns_count_num"] = pd.to_numeric(user_df.get("turns_count"), errors="coerce").fillna(0)
    user_df["text_len"] = user_df.get("plain_text", "").fillna("").astype(str).str.len()
    user_df["turn_bin"] = pd.cut(user_df["turns_count_num"], bins=[0, 2, 5, 1_000_000], labels=["1-2", "3-5", "6+"])
    bin_summary = user_df.groupby("turn_bin")["text_len"].agg(["count", "mean", "median"]).to_dict()
    corr, p_value = spearmanr(user_df["turns_count_num"], user_df["text_len"], nan_policy="omit")

    run_dir = eda_io.make_run_dir(ANALYSIS, args.run_id)
    fig, ax = plt.subplots(figsize=(7, 4))
    grouped = user_df.groupby("turn_bin")["text_len"].mean().reindex(["1-2", "3-5", "6+"])
    grouped.plot(kind="bar", ax=ax)
    ax.set_title("Mean user message length by thread-length bin")
    ax.set_xlabel("turns_count bin")
    ax.set_ylabel("mean characters")
    eda_io.save_figure(fig, run_dir / "mean_length_by_turn_bin.png")
    plt.close(fig)

    eda_io.write_results_json(
        run_dir,
        analysis=ANALYSIS,
        batch_id=args.run_id,
        dataset_path=args.data,
        row_count_input=len(df),
        row_count_after_filters=len(user_df),
        filters={"role": "user"},
        figures=["mean_length_by_turn_bin.png"],
        metrics={
            "bin_summary": bin_summary,
            "spearman_correlation": {"rho": float(corr), "p_value": float(p_value)},
        },
        warnings=[],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

