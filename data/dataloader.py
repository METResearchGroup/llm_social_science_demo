"""Local Hugging Face → Parquet helper for ShareChat.

Run from repository root:

    PYTHONPATH=. uv run python data/dataloader.py

Sourced from https://huggingface.co/datasets/tucnguyen/ShareChat
- Original ArXiv paper: https://arxiv.org/html/2512.17843v2
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from datasets import load_dataset

PROP_DEFAULT = 0.10

HF_DATASET_ID = "tucnguyen/ShareChat"
HF_DEFAULT_CONFIG = "chatgpt"


class DataLoader:
    """Load a fractional slice of ShareChat and write Parquet locally."""

    def __init__(
        self,
        *,
        dataset_id: str = HF_DATASET_ID,
        config_name: str = HF_DEFAULT_CONFIG,
        output_path: Path | None = None,
    ) -> None:
        self.dataset_id = dataset_id
        self.config_name = config_name
        self.output_path = output_path or (Path(__file__).resolve().parent / "dataset.parquet")
        self._dataset = None
        self._loaded_prop: float | None = None

    def load_data_from_huggingface(self, *, prop: float = PROP_DEFAULT) -> None:
        """Load ``train`` from Hugging Face as the first ``prop`` fraction of rows (by split slice)."""
        pct = max(1, min(100, int(round(prop * 100))))
        split = f"train[:{pct}%]"
        self._dataset = load_dataset(
            self.dataset_id,
            self.config_name,
            split=split,
        )
        self._loaded_prop = prop

    def save_data_locally(self, *, prop: float = PROP_DEFAULT) -> Path:
        """Write the in-memory dataset to ``dataset.parquet`` (or ``output_path``).

        ``prop`` must match the fraction used in :meth:`load_data_from_huggingface`.
        """
        if self._dataset is None:
            msg = "No data loaded; call load_data_from_huggingface first."
            raise RuntimeError(msg)
        if self._loaded_prop is not None and prop != self._loaded_prop:
            msg = (
                f"Requested prop={prop} but data was loaded with prop={self._loaded_prop}. "
                "Reload with load_data_from_huggingface(prop=...) first."
            )
            raise ValueError(msg)
        path = self.output_path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._dataset.to_parquet(str(path))
        return path

    def load_data_from_local(self, *, path: Path | None = None) -> pd.DataFrame:
        """Read the local Parquet file (default: ``output_path``) into a pandas DataFrame."""
        parquet_path = path or self.output_path
        if not parquet_path.is_file():
            msg = f"Parquet file not found: {parquet_path}"
            raise FileNotFoundError(msg)
        return pd.read_parquet(parquet_path)


def main() -> Path:
    loader = DataLoader()
    loader.load_data_from_huggingface(prop=PROP_DEFAULT)
    return loader.save_data_locally(prop=PROP_DEFAULT)


if __name__ == "__main__":
    out = main()
    print(f"Wrote {out} ({out.stat().st_size} bytes)")
