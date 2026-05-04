"""Smoke test for :meth:`data.dataloader.DataLoader.load_data_from_local`.

Run from repository root (prints ``shape`` and ``head``):

    PYTHONPATH=. uv run python data/smoke_tests/test_load_local_dataset.py

Or with pytest (stdout needs ``-s``):

    PYTHONPATH=. uv run pytest data/smoke_tests/test_load_local_dataset.py -s
"""

from __future__ import annotations

from data.dataloader import DataLoader


def _print_local_sample() -> None:
    loader = DataLoader()
    df = loader.load_data_from_local()
    breakpoint()
    print(df.shape)
    print(df.head())


def test_load_local_dataset() -> None:
    _print_local_sample()


if __name__ == "__main__":
    _print_local_sample()
