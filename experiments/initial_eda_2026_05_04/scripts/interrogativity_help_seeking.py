from __future__ import annotations

import argparse
import os

import matplotlib.pyplot as plt

from experiments.initial_eda_2026_05_04.scripts import eda_io

ANALYSIS = "interrogativity_help_seeking"
HELP_PATTERN = r"\b(how|why|what|should|can you|could you|help)\b"


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
    user_df["text"] = user_df.get("plain_text", "").fillna("").astype(str)
    user_df["is_question"] = user_df["text"].str.rstrip().str.endswith("?")
    user_df["has_help_cue"] = user_df["text"].str.contains(HELP_PATTERN, case=False, regex=True, na=False)

    question_rate = float(user_df["is_question"].mean()) if len(user_df) else 0.0
    help_rate = float(user_df["has_help_cue"].mean()) if len(user_df) else 0.0
    by_language = (
        user_df.groupby("detected_language_final")[["is_question", "has_help_cue"]].mean().fillna(0).to_dict(orient="index")
        if "detected_language_final" in user_df.columns
        else {}
    )
    warnings: list[str] = []
    if "topic" not in user_df.columns:
        warnings.append("topic column missing; skipped topic breakdown")

    run_dir = eda_io.make_run_dir(ANALYSIS, args.run_id)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(["question_rate", "help_cue_rate"], [question_rate, help_rate])
    ax.set_title("Interrogativity and help-seeking rates")
    ax.set_ylim(0, 1)
    eda_io.save_figure(fig, run_dir / "question_help_rates.png")
    plt.close(fig)

    eda_io.write_results_json(
        run_dir,
        analysis=ANALYSIS,
        batch_id=args.run_id,
        dataset_path=args.data,
        row_count_input=len(df),
        row_count_after_filters=len(user_df),
        filters={"role": "user"},
        figures=["question_help_rates.png"],
        metrics={
            "question_rate": question_rate,
            "help_cue_rate": help_rate,
            "by_language": by_language,
        },
        warnings=warnings,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

