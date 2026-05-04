"""Smoke tests for ShareChat EDA shared I/O."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.initial_eda_2026_05_04.scripts import eda_io


def test_make_run_dir_creates_nested(tmp_path: Path) -> None:
    out = eda_io.make_run_dir(analysis_slug="language_mix", batch_id="batch_x", output_root=tmp_path)
    assert out.is_dir()
    assert out.name == "batch_x"
    assert (tmp_path / "language_mix" / "batch_x").exists()


def test_write_results_json_shape(tmp_path: Path) -> None:
    run_dir = tmp_path / "language_mix" / "b1"
    run_dir.mkdir(parents=True)
    p = eda_io.write_results_json(
        run_dir,
        analysis="language_mix",
        batch_id="b1",
        dataset_path="data/dataset.parquet",
        row_count_input=10,
        row_count_after_filters=5,
        filters={"role": "user"},
        figures=["visuals.png"],
        metrics={"x": 1},
        warnings=[],
    )
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["schema_version"] == eda_io.SCHEMA_VERSION
    assert set(data.keys()) >= eda_io.REQUIRED_RESULT_KEYS
