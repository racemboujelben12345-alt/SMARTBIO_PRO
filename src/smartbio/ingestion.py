"""Local ingestion helpers for authorized SmartBio dataset exports.

This module deliberately operates on files already present on disk. It does not
download gated datasets, infer missing acquisition metadata, or redistribute
source data.
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd
from .dataset_adapters import adapt_sewa_metadata


def load_metadata_table(path: str | Path) -> pd.DataFrame:
    """Load a local CSV, JSONL/JSON, or Parquet metadata export."""
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Metadata file not found: {source}")

    suffix = source.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(source)
    if suffix == ".csv":
        return pd.read_csv(source)
    if suffix in {".json", ".jsonl"}:
        return pd.read_json(source, lines=suffix == ".jsonl")

    raise ValueError(
        f"Unsupported metadata format: {suffix or '<none>'}. "
        "Use .parquet, .csv, .json, or .jsonl."
    )


def ingest_sewa_local(
    metadata_path: str | Path,
    *,
    output_path: str | Path,
    modalities: tuple[str, ...] = (
        "conjunctiva",
        "fingernails_open",
        "fingernails_closed",
        "tongue",
    ),
) -> pd.DataFrame:
    """Convert an authorized local SEWA export into canonical metadata."""
    raw = load_metadata_table(metadata_path)
    canonical = adapt_sewa_metadata(raw, modalities=modalities)

    if canonical.empty:
        raise ValueError(
            "SEWA ingestion produced zero canonical records. "
            "Check image paths and Hb/reference fields."
        )

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    canonical.to_csv(destination, index=False)
    return canonical
