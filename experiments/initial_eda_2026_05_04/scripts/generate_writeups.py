"""Generate writeup.md per analysis from the latest results.json + figures."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from eda_io import repo_root

ANALYSIS_SLUGS = (
    "language_mix",
    "first_vs_later_user_turn",
    "thread_length_vs_user_properties",
    "pronoun_reference",
    "interrogativity_help_seeking",
)


def latest_batch_dir(results_root: Path, analysis: str) -> Path | None:
    base = results_root / analysis
    if not base.is_dir():
        return None
    candidates = [p for p in base.iterdir() if p.is_dir() and (p / "results.json").is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda p: (p.stat().st_mtime, p.name))


def rel_link(from_md: Path, target: Path) -> str:
    return Path(os.path.relpath(target.resolve(), start=from_md.parent.resolve())).as_posix()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Write markdown writeups from latest EDA JSON.")
    p.add_argument(
        "--experiment-root",
        type=Path,
        default=None,
        help="experiments/initial_eda_2026_05_04 directory",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    exp = (args.experiment_root or (root / "experiments" / "initial_eda_2026_05_04")).resolve()
    results_root = exp / "results"
    writeups_root = exp / "writeups"
    dataset_note = (root / "data" / "DATASET_DESCRIPTION.md").read_text(encoding="utf-8", errors="replace")

    limitations_blurb = (
        "ShareChat is built from **publicly shared** conversation links (self-selected threads), "
        "and this repo’s default loader slice uses the **`chatgpt`** config only (see `data/dataloader.py`). "
        "See `data/DATASET_DESCRIPTION.md` for platform imbalance, PII redaction, and paper limitations."
    )

    for analysis in ANALYSIS_SLUGS:
        run_dir = latest_batch_dir(results_root, analysis)
        out_dir = writeups_root / analysis
        out_dir.mkdir(parents=True, exist_ok=True)
        out_md = out_dir / "writeup.md"
        if run_dir is None:
            out_md.write_text(
                f"# {analysis}\n\nNo `results/{analysis}/<batch_id>/results.json` found yet. "
                f"Run `scripts/main.py` first.\n",
                encoding="utf-8",
            )
            continue

        data = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
        figures = data.get("figures") or []
        metric_preview = json.dumps(data.get("metrics"), indent=2, ensure_ascii=False)[:8000]

        lines: list[str] = [
            f"# {analysis}",
            "",
            f"- **Latest batch:** `{run_dir.name}`",
            f"- **Dataset:** `{data.get('dataset_path')}`",
            f"- **Rows (input / after filters):** {data.get('row_count_input')} / {data.get('row_count_after_filters')}",
            "",
            "## Limitations",
            "",
            limitations_blurb,
            "",
            "## Metrics (excerpt)",
            "",
            "```json",
            metric_preview,
            "```",
            "",
            "## Figures",
            "",
        ]
        for fig in figures:
            fp = run_dir / fig
            if fp.is_file():
                link = rel_link(out_md, fp)
                lines.append(f"![{fig}]({link})")
                lines.append("")
            else:
                lines.append(f"- Missing on disk: `{fig}`")
                lines.append("")

        lines.extend(
            [
                "## Dataset documentation (reference)",
                "",
                "<details><summary>DATASET_DESCRIPTION.md (truncated)</summary>",
                "",
                "```text",
                dataset_note[:6000],
                "```",
                "",
                "</details>",
                "",
            ]
        )

        out_md.write_text("\n".join(lines), encoding="utf-8")
        print(out_md)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
