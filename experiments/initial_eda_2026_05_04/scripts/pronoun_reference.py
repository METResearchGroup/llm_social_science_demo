"""EDA Q4: self-reference vs other-reference pronoun ratios (user turns)."""

from __future__ import annotations

import argparse
import re
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

ANALYSIS = "pronoun_reference"

RE_I_ME_MY = re.compile(r"\b(i|me|my|mine|myself)\b", re.I)
RE_THEY = re.compile(r"\b(they|them|their|theirs|themselves)\b", re.I)
RE_YOU = re.compile(r"\b(you|your|yours|yourself|yourselves)\b", re.I)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Pronoun counts on user plain_text.")
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
    text = u["plain_text"].astype(str).str.lower()
    row_after = len(u)

    c_i = text.apply(lambda s: len(RE_I_ME_MY.findall(s)))
    c_they = text.apply(lambda s: len(RE_THEY.findall(s)))
    c_you = text.apply(lambda s: len(RE_YOU.findall(s)))
    total = (c_i + c_they + c_you).replace(0, pd.NA)

    rate_i = (c_i / total).mean(skipna=True)
    rate_they = (c_they / total).mean(skipna=True)
    rate_you = (c_you / total).mean(skipna=True)

    metrics: dict = {
        "mean_hits_i_me_my_per_message": float(c_i.mean()),
        "mean_hits_they_per_message": float(c_they.mean()),
        "mean_hits_you_per_message": float(c_you.mean()),
        "mean_rate_i_among_classified_pronoun_hits": float(rate_i) if pd.notna(rate_i) else None,
        "mean_rate_they_among_classified_pronoun_hits": float(rate_they) if pd.notna(rate_they) else None,
        "mean_rate_you_among_classified_pronoun_hits": float(rate_you) if pd.notna(rate_you) else None,
        "messages_with_any_pronoun_hit": int(total.notna().sum()),
    }

    setup_matplotlib_agg()
    run_dir = make_run_dir(analysis_slug=ANALYSIS, batch_id=batch_id, output_root=output_root)

    fig, ax = plt.subplots(figsize=(7, 5))
    labels = ["I/me/my", "they/them", "you (bot)"]
    vals = [float(c_i.sum()), float(c_they.sum()), float(c_you.sum())]
    ax.bar(labels, vals, color=["#1f77b4", "#ff7f0e", "#2ca02c"])
    ax.set_title("Total regex hits (user turns, corpus-wide)")
    fig.tight_layout()
    fig.savefig(run_dir / "visuals.png", dpi=150)
    plt.close(fig)

    write_results_json(
        run_dir,
        analysis=ANALYSIS,
        batch_id=batch_id,
        dataset_path=dataset_path_for_json(parquet),
        row_count_input=row_in,
        row_count_after_filters=row_after,
        filters={"role": "user"},
        figures=["visuals.png"],
        metrics=metrics,
        warnings=warnings,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
