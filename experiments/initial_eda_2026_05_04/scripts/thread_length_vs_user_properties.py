"""EDA Q3: thread length (turns_count) vs user-turn properties."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

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

ANALYSIS = "thread_length_vs_user_properties"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Thread length vs user message properties.")
    p.add_argument("--parquet", type=Path, default=None)
    p.add_argument("--batch-id", type=str, default=None)
    p.add_argument("--output-root", type=Path, default=None)
    return p.parse_args()


def turns_bin(tc: pd.Series) -> pd.Series:
    bins = pd.cut(
        tc.astype(float),
        bins=[-np.inf, 2, 5, np.inf],
        labels=["1-2", "3-5", "6+"],
    )
    return bins.astype(str)


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
    u["msg_len"] = u["plain_text"].astype(str).str.len()
    u["turn_bin"] = turns_bin(u["turns_count"])
    row_after = len(u)

    spearman_rho: float | None = None
    spearman_p: float | None = None
    if row_after >= 3:
        rho, pval = stats.spearmanr(u["turns_count"].astype(float), u["msg_len"].astype(float), nan_policy="omit")
        if not (np.isnan(rho) or np.isnan(pval)):
            spearman_rho = float(rho)
            spearman_p = float(pval)

    by_bin = u.groupby("turn_bin", observed=False)["msg_len"].agg(["mean", "median", "count"]).to_dict("index")

    lang_share_by_bin: dict[str, dict[str, float]] = {}
    if "detected_language_final" in u.columns:
        for b in u["turn_bin"].dropna().unique():
            sub = u[u["turn_bin"] == b]
            vc = sub["detected_language_final"].fillna("(missing)").astype(str).value_counts(normalize=True).head(8)
            lang_share_by_bin[str(b)] = {str(k): float(v) for k, v in vc.items()}

    topic_share_by_bin: dict[str, dict[str, float]] = {}
    if "topic" in u.columns:
        for b in u["turn_bin"].dropna().unique():
            sub = u[u["turn_bin"] == b]["topic"].dropna().astype(str)
            if len(sub):
                vc = sub.value_counts(normalize=True).head(8)
                topic_share_by_bin[str(b)] = {str(k): float(v) for k, v in vc.items()}

    metrics: dict = {
        "aggregation_note": "Per-message (user rows): Spearman between turns_count (conversation) and user plain_text length.",
        "spearman_turns_count_vs_user_msg_len": {"rho": spearman_rho, "pvalue": spearman_p},
        "summary_by_turn_bin": by_bin,
        "language_share_top8_by_bin": lang_share_by_bin,
        "topic_share_top8_by_bin": topic_share_by_bin,
    }

    setup_matplotlib_agg()
    run_dir = make_run_dir(analysis_slug=ANALYSIS, batch_id=batch_id, output_root=output_root)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    order = ["1-2", "3-5", "6+"]
    means = [by_bin.get(o, {}).get("mean", np.nan) for o in order]
    counts = [by_bin.get(o, {}).get("count", 0) for o in order]
    x = np.arange(len(order))
    axes[0].bar(x, [m if m == m else 0 for m in means], color="slateblue")
    axes[0].set_xticks(x, order)
    axes[0].set_title("Mean user message length by turns_count bin")
    axes[0].set_xlabel("turns_count bin")
    for i, c in enumerate(counts):
        axes[0].text(i, (means[i] if means[i] == means[i] else 0) + 1, f"n={int(c)}", ha="center", fontsize=8)

    if lang_share_by_bin:
        langs = sorted({k for d in lang_share_by_bin.values() for k in d})[:6]
        mat = np.zeros((len(order), len(langs)))
        for i, o in enumerate(order):
            d = lang_share_by_bin.get(o, {})
            for j, lang in enumerate(langs):
                mat[i, j] = d.get(lang, 0.0)
        im = axes[1].imshow(mat.T, aspect="auto", cmap="viridis")
        axes[1].set_xticks(range(len(order)), order)
        axes[1].set_yticks(range(len(langs)), langs)
        axes[1].set_title("Language share heatmap (top langs × bin)")
        fig.colorbar(im, ax=axes[1], fraction=0.046, pad=0.04)
    else:
        axes[1].text(0.5, 0.5, "No language column", ha="center", va="center")

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
