"""Leakage-safe device-held-out robustness utilities for SmartBio."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class DeviceRobustnessSplit:
    train: pd.DataFrame
    test: pd.DataFrame
    held_out_device: str
    excluded_patients: int


def unseen_device_split(df: pd.DataFrame, held_out_device: str) -> DeviceRobustnessSplit:
    required = {"device_model", "patient_id"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if not str(held_out_device).strip():
        raise ValueError("held_out_device must be non-empty.")

    test = df[df["device_model"].astype(str) == str(held_out_device)].copy()
    if test.empty:
        raise ValueError(f"Held-out device not found: {held_out_device}")

    held_patients = set(test["patient_id"])
    train = df[
        (df["device_model"].astype(str) != str(held_out_device))
        & (~df["patient_id"].isin(held_patients))
    ].copy()
    if train.empty:
        raise ValueError("No training records remain after patient-safe device holdout.")

    return DeviceRobustnessSplit(
        train=train,
        test=test,
        held_out_device=str(held_out_device),
        excluded_patients=len(held_patients),
    )


def summarize_device_distribution(df: pd.DataFrame) -> pd.DataFrame:
    required = {"device_model"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    out = (
        df.groupby("device_model", dropna=False)
        .size()
        .rename("n")
        .reset_index()
    )
    out["fraction"] = out["n"] / len(df)
    return out.sort_values("n", ascending=False).reset_index(drop=True)


def relative_mae_change(source_mae: float, held_out_mae: float) -> float:
    if not np.isfinite(source_mae) or not np.isfinite(held_out_mae):
        raise ValueError("MAE values must be finite.")
    if source_mae < 0 or held_out_mae < 0:
        raise ValueError("MAE values must be non-negative.")
    if source_mae == 0:
        return float("nan") if held_out_mae == 0 else float("inf")
    return float((held_out_mae - source_mae) / source_mae)


def device_robustness_report(
    source_metrics: pd.DataFrame,
    held_out_metrics: pd.DataFrame,
    *,
    key: str = "model",
) -> pd.DataFrame:
    required = {key, "mae", "rmse", "r2"}
    for name, frame in (("source_metrics", source_metrics), ("held_out_metrics", held_out_metrics)):
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"{name} missing columns: {sorted(missing)}")

    left = source_metrics[list(required)].copy()
    right = held_out_metrics[list(required)].copy()
    merged = left.merge(right, on=key, suffixes=("_source", "_held_out"))
    if merged.empty:
        raise ValueError("No matching models between source and held-out metrics.")

    merged["mae_relative_change"] = [
        relative_mae_change(a, b)
        for a, b in zip(merged["mae_source"], merged["mae_held_out"])
    ]
    merged["rmse_relative_change"] = [
        relative_mae_change(a, b)
        for a, b in zip(merged["rmse_source"], merged["rmse_held_out"])
    ]
    return merged.sort_values("mae_held_out").reset_index(drop=True)
