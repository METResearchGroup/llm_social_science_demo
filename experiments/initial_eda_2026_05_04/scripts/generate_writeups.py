from __future__ import annotations

import argparse
import json
from pathlib import Path

SLUGS = [
    "language_mix",
    "first_vs_later_user_turn",
    "thread_length_vs_user_properties",
    "pronoun_reference",
    "interrogativity_help_seeking",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    return parser.parse_args()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def main() -> int:
    args = parse_args()
    root = _repo_root() / "experiments" / "initial_eda_2026_05_04"
    for slug in SLUGS:
        result_json = root / "results" / slug / args.run_id / "results.json"
        if not result_json.is_file():
            raise FileNotFoundError(f"Missing results for {slug}: {result_json}")
        payload = json.loads(result_json.read_text(encoding="utf-8"))
        writeup_dir = root / "writeups" / slug
        writeup_dir.mkdir(parents=True, exist_ok=True)
        lines = [
            f"# {slug.replace('_', ' ').title()}",
            "",
            f"- Run ID: `{payload['run_id']}`",
            f"- Dataset: `{payload['dataset_path']}`",
            f"- Filtered rows: `{payload['row_count_after_filters']}` of `{payload['row_count_input']}`",
            "",
            "## Metrics",
            "",
            "```json",
            json.dumps(payload["metrics"], indent=2, ensure_ascii=True),
            "```",
            "",
            "## Figures",
            "",
        ]
        for figure in payload.get("figures", []):
            figure_file = figure["file"]
            lines.append(f"- `experiments/initial_eda_2026_05_04/results/{slug}/{args.run_id}/{figure_file}`")
        lines.extend(
            [
                "",
                "## Caveats",
                "",
                "- Exploratory analysis over the local slice (typically 10% ChatGPT config by default).",
                "- Topic-specific summaries require `topic` to exist in the dataset.",
            ]
        )
        (writeup_dir / "writeup.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote writeups for run_id={args.run_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

