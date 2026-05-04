"""Run all five ShareChat EDA analyses in parallel worker processes."""

from __future__ import annotations

import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent

ANALYSIS_SCRIPTS = (
    "language_mix.py",
    "first_vs_later_user_turn.py",
    "thread_length_vs_user_properties.py",
    "pronoun_reference.py",
    "interrogativity_help_seeking.py",
)


def _run_script(args: tuple[Path, str, Path, Path]) -> tuple[str, int]:
    script_path, batch_id, parquet, output_root = args
    cmd = [
        sys.executable,
        str(script_path),
        "--batch-id",
        batch_id,
        "--parquet",
        str(parquet),
        "--output-root",
        str(output_root),
    ]
    completed = subprocess.run(cmd, cwd=str(REPO_ROOT), check=False)
    return str(script_path), completed.returncode


def main() -> int:
    batch_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    parquet = REPO_ROOT / "data" / "dataset.parquet"
    output_root = REPO_ROOT / "experiments" / "initial_eda_2026_05_04" / "results"

    tasks: list[tuple[Path, str, Path, Path]] = [
        (SCRIPTS_DIR / name, batch_id, parquet, output_root) for name in ANALYSIS_SCRIPTS
    ]

    exit_codes: dict[str, int] = {}
    with ProcessPoolExecutor(max_workers=len(tasks)) as ex:
        futures = [ex.submit(_run_script, t) for t in tasks]
        for fut in as_completed(futures):
            path, code = fut.result()
            exit_codes[path] = code

    for script_path, bid, _, out_root in tasks:
        slug = script_path.name.removesuffix(".py")
        print((out_root / slug / bid / "results.json").resolve())

    bad = [k for k, v in exit_codes.items() if v != 0]
    if bad:
        print("Failures:", file=sys.stderr)
        for k in sorted(bad):
            print(f"  {k} exit={exit_codes[k]}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
