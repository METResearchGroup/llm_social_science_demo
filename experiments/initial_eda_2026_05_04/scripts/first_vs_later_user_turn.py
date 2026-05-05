from __future__ import annotations

import argparse
import os

import matplotlib.pyplot as plt
import pandas as pd

from experiments.initial_eda_2026_05_04.scripts import eda_io

ANALYSIS = "first_vs_later_user_turn"


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
    user_df["message_index"] = pd.to_numeric(user_df.get("message_index"), errors="coerce").fillna(0)
    user_df["plain_text"] = user_df.get("plain_text", "").fillna("").astype(str)
    first_idx = user_df.groupby("url")["message_index"].transform("min")
    user_df["is_first_user_turn"] = user_df["message_index"] == first_idx
    user_df["length"] = user_df["plain_text"].str.len()
    summary = user_df.groupby("is_first_user_turn")["length"].agg(["count", "mean", "median"]).to_dict()

    run_dir = eda_io.make_run_dir(ANALYSIS, args.run_id)
    fig, ax = plt.subplots(figsize=(6, 4))
    user_df.boxplot(column="length", by="is_first_user_turn", ax=ax)
    ax.set_title("User message length: first vs later")
    ax.set_xlabel("is_first_user_turn")
    ax.set_ylabel("characters")
    fig.suptitle("")
    eda_io.save_figure(fig, run_dir / "length_first_vs_later.png")
    plt.close(fig)

    warnings: list[str] = []
    topic_summary = {}
    if "topic" in user_df.columns:
        topic_summary = (
            user_df.groupby(["is_first_user_turn", "topic"]).size().reset_index(name="count").to_dict(orient="records")
        )
    else:
        warnings.append("topic column missing; skipped topic breakdown")

    eda_io.write_results_json(
        run_dir,
        analysis=ANALYSIS,
        batch_id=args.run_id,
        dataset_path=args.data,
        row_count_input=len(df),
        row_count_after_filters=len(user_df),
        filters={"role": "user"},
        figures=["length_first_vs_later.png"],
        metrics={
            "length_summary": summary,
            "topic_by_firstness": topic_summary,
        },
        warnings=warnings,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

