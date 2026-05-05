from __future__ import annotations

import os
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from experiments.initial_eda_2026_05_04.scripts import eda_io

SCRIPTS = [
    "language_mix.py",
    "first_vs_later_user_turn.py",
    "thread_length_vs_user_properties.py",
    "pronoun_reference.py",
    "interrogativity_help_seeking.py",
]


def _run_script(script_name: str, run_id: str, dataset_path: str) -> tuple[str, int, str]:
    script_path = Path(__file__).resolve().parent / script_name
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"
    env[eda_io.RESULTS_ENV_VAR] = run_id
    env[eda_io.DEFAULT_DATASET_ENV_VAR] = dataset_path
    cmd = ["python", str(script_path), "--run-id", run_id, "--data", dataset_path]
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    output = (proc.stdout or "") + (proc.stderr or "")
    return script_name, proc.returncode, output


def main() -> int:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dataset_path = str(eda_io.default_dataset_path())
    print(f"INITIAL_EDA_RUN_ID={run_id}")
    failures: list[tuple[str, int, str]] = []
    with ProcessPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(_run_script, script_name, run_id, dataset_path) for script_name in SCRIPTS]
        for future in as_completed(futures):
            script_name, return_code, output = future.result()
            if return_code != 0:
                failures.append((script_name, return_code, output))
            print(f"{script_name}: exit={return_code}")
    if failures:
        print("Failures:")
        for script_name, return_code, output in failures:
            print(f"- {script_name} ({return_code})")
            print(output)
        return 1
    gen_script = Path(__file__).resolve().parent / "generate_writeups.py"
    gen_proc = subprocess.run(["python", str(gen_script), "--run-id", run_id], capture_output=True, text=True)
    if gen_proc.returncode != 0:
        print(gen_proc.stdout)
        print(gen_proc.stderr)
        return gen_proc.returncode
    print(gen_proc.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

