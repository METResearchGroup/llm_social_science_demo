"""EDA Q5: interrogativity and help-seeking surface cues (user turns)."""

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

ANALYSIS = "interrogativity_help_seeking"

CUE_RE = re.compile(
    r"\b(?:how|why|what|when|where|which|who|should|could|would|can\s+you|please\s+help)\b",
    re.I,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Question marks and help-seeking cues.")
    p.add_argument("--parquet", type=Path, default=None)
    p.add_argument("--batch-id", type=str, default=None)
    p.add_argument("--output-root", type=Path, default=None)
    return p.parse_args()


def stratified_rates(series_mask: pd.Series, df: pd.DataFrame, col: str) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    if col not in df.columns:
        return out
    g = df[col].fillna("(missing)").astype(str)
    for key in sorted(g.unique(), key=lambda x: (-(g == x).sum(), str(x)))[:15]:
        m = g == key
        denom = int(m.sum())
        if denom == 0:
            continue
        out[str(key)] = {"rate": float(series_mask[m].mean()), "n": float(denom)}
    return out


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
    text = u["plain_text"].astype(str)
    row_after = len(u)

    ends_q = text.str.rstrip().str.endswith("?")
    has_cue = text.str.contains(CUE_RE, regex=True, na=False)

    metrics: dict = {
        "rate_ends_with_question_mark": float(ends_q.mean()) if row_after else 0.0,
        "rate_contains_help_seeking_cue_regex": float(has_cue.mean()) if row_after else 0.0,
        "rate_either_question_or_cue": float((ends_q | has_cue).mean()) if row_after else 0.0,
        "by_language": stratified_rates(ends_q | has_cue, u, "detected_language_final"),
        "by_topic": stratified_rates(ends_q | has_cue, u, "topic"),
    }

    setup_matplotlib_agg()
    run_dir = make_run_dir(analysis_slug=ANALYSIS, batch_id=batch_id, output_root=output_root)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].bar(["ends ?", "cue phrase", "either"], [ends_q.mean(), has_cue.mean(), (ends_q | has_cue).mean()])
    axes[0].set_ylim(0, 1)
    axes[0].set_title("Overall rates (user turns)")

    lang_rates = metrics["by_language"]
    if lang_rates:
        keys = list(lang_rates.keys())[:12]
        vals = [lang_rates[k]["rate"] for k in keys]
        axes[1].barh(keys[::-1], vals[::-1])
        axes[1].set_xlim(0, 1)
        axes[1].set_title("Either ? or cue (by language, top buckets)")
    else:
        axes[1].text(0.5, 0.5, "No language", ha="center")
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
