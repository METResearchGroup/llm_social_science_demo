from __future__ import annotations

import argparse
import os

import matplotlib.pyplot as plt

from experiments.initial_eda_2026_05_04.scripts import eda_io

ANALYSIS = "language_mix"


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
    user_df["language"] = user_df["detected_language_final"].fillna("unknown").astype(str)
    lang_counts = user_df["language"].value_counts().head(10)
    english_rate = float((user_df["language"].str.lower() == "english").mean()) if len(user_df) else 0.0
    run_dir = eda_io.make_run_dir(ANALYSIS, args.run_id)

    fig1, ax1 = plt.subplots(figsize=(8, 4))
    lang_counts.sort_values(ascending=True).plot(kind="barh", ax=ax1)
    ax1.set_title("Top user-turn languages")
    ax1.set_xlabel("Count")
    eda_io.save_figure(fig1, run_dir / "top_languages.png")
    plt.close(fig1)

    fig2, ax2 = plt.subplots(figsize=(5, 4))
    labels = ["english", "non_english"]
    vals = [english_rate, 1.0 - english_rate]
    ax2.bar(labels, vals)
    ax2.set_title("English share among user turns")
    ax2.set_ylim(0, 1)
    eda_io.save_figure(fig2, run_dir / "english_share.png")
    plt.close(fig2)

    eda_io.write_results_json(
        run_dir,
        analysis=ANALYSIS,
        batch_id=args.run_id,
        dataset_path=args.data,
        row_count_input=len(df),
        row_count_after_filters=len(user_df),
        filters={"role": "user"},
        figures=["top_languages.png", "english_share.png"],
        metrics={
            "english_rate": english_rate,
            "top_languages": lang_counts.to_dict(),
        },
        warnings=[],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

