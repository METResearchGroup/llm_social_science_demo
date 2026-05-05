from __future__ import annotations

import argparse
import os
import re

import matplotlib.pyplot as plt

from experiments.initial_eda_2026_05_04.scripts import eda_io

ANALYSIS = "pronoun_reference"
SELF_RE = re.compile(r"\b(i|me|my|mine|myself)\b", flags=re.IGNORECASE)
BOT_RE = re.compile(r"\b(you|your|yours|yourself)\b", flags=re.IGNORECASE)
OTHER_RE = re.compile(r"\b(they|them|their|theirs|themselves)\b", flags=re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default=os.getenv(eda_io.RESULTS_ENV_VAR))
    parser.add_argument("--data", default=str(eda_io.default_dataset_path()))
    return parser.parse_args()


def _count(pattern: re.Pattern[str], text: str) -> int:
    return len(pattern.findall(text))


def main() -> int:
    args = parse_args()
    if not args.run_id:
        raise ValueError("run_id missing; pass --run-id or set INITIAL_EDA_RUN_ID")
    eda_io.ensure_agg_backend()
    df = eda_io.load_dataframe(args.data)
    user_df = df[df["role"].astype(str).str.lower() == "user"].copy()
    texts = user_df.get("plain_text", "").fillna("").astype(str)
    self_count = int(texts.map(lambda t: _count(SELF_RE, t)).sum())
    bot_count = int(texts.map(lambda t: _count(BOT_RE, t)).sum())
    other_count = int(texts.map(lambda t: _count(OTHER_RE, t)).sum())
    per_message_any = {
        "self_reference_rate": float(texts.str.contains(SELF_RE).mean()) if len(texts) else 0.0,
        "bot_reference_rate": float(texts.str.contains(BOT_RE).mean()) if len(texts) else 0.0,
        "other_reference_rate": float(texts.str.contains(OTHER_RE).mean()) if len(texts) else 0.0,
    }

    run_dir = eda_io.make_run_dir(ANALYSIS, args.run_id)
    fig, ax = plt.subplots(figsize=(6, 4))
    labels = ["self", "bot_you", "other_they"]
    values = [self_count, bot_count, other_count]
    ax.bar(labels, values)
    ax.set_title("Pronoun reference counts")
    ax.set_ylabel("count")
    eda_io.save_figure(fig, run_dir / "pronoun_counts.png")
    plt.close(fig)

    eda_io.write_results_json(
        run_dir,
        analysis=ANALYSIS,
        batch_id=args.run_id,
        dataset_path=args.data,
        row_count_input=len(df),
        row_count_after_filters=len(user_df),
        filters={"role": "user"},
        figures=["pronoun_counts.png"],
        metrics={
            "counts": {"self": self_count, "bot_you": bot_count, "other_they": other_count},
            "per_message_any": per_message_any,
        },
        warnings=[],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

