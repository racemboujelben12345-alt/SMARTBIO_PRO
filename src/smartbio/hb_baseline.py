"""Hemoglobin baseline regression pipeline.

Research-only utilities for patient-safe Hb regression from extracted image features.
The module deliberately separates feature extraction, grouped splitting, fitting,
prediction, and evaluation so calibration/model selection cannot leak across patients.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from xgboost import XGBRegressor

from .evaluation import regression_metrics
from .features import extract
from .roi import ROIBox, crop, validate_roi_type
from .splits import patient_split


@dataclass(frozen=True)
class HbBaselineResult:
    """Container for test predictions and regression metrics."""

    predictions: pd.DataFrame
    metrics: dict[str, float]


def _build_model(name: str, random_state: int = 42) -> Pipeline:
    """Build a baseline regressor with deterministic preprocessing."""
    models = {
        "xgboost": XGBRegressor(
            n_estimators=400,
            max_depth=4,
            learning_rate=0.03,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_lambda=1.0,
            objective="reg:squarederror",
            random_state=random_state,
            n_jobs=1,
        ),
        "random_forest": RandomForestRegressor(
            n_estimators=400,
            max_depth=None,
            min_samples_leaf=2,
            random_state=random_state,
            n_jobs=1,
        ),
        "svr": Pipeline([
            ("scale", StandardScaler()),
            ("svr", SVR(C=10.0, epsilon=0.1, gamma="scale")),
        ]),
    }
    if name not in models:
        raise ValueError(f"Unknown model: {name}. Choose from {sorted(models)}.")
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("model", models[name]),
    ])


def build_feature_table(
    metadata: pd.DataFrame,
    image_root: str | Path | None = None,
    require_explicit_roi: bool = True,
) -> pd.DataFrame:
    """Extract RGB/HSV/Lab/chromatic features from canonical Hb metadata.

    Expected columns include image_path, patient_id and Hb_g_dL (or target_value).
    ROI coordinates should be explicit unless require_explicit_roi=False.
    """
    df = metadata.copy()
    target_col = "Hb_g_dL" if "Hb_g_dL" in df.columns else "target_value"
    required = {"image_path", "patient_id", target_col}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    rows: list[dict[str, float | str]] = []
    for _, row in df.iterrows():
        path = Path(row["image_path"])
        if image_root is not None and not path.is_absolute():
            path = Path(image_root) / path
        image = np.asarray(__import__("PIL.Image", fromlist=["Image"]).open(path).convert("RGB"))
        if "roi_type" not in row or pd.isna(row["roi_type"]):
            raise ValueError("Each Hb image needs an explicit roi_type (conjunctiva or nailbed).")
        validate_roi_type("hemoglobin", str(row["roi_type"]))
        coords = ["roi_x0", "roi_y0", "roi_x1", "roi_y1"]
        if not all(c in row and pd.notna(row[c]) for c in coords):
            raise ValueError(f"Explicit ROI coordinates required: {coords}")
        roi = crop(image, ROIBox(*(int(row[c]) for c in coords)))
        feats = extract(roi)
        record = {
            "patient_id": str(row["patient_id"]),
            "image_path": str(row["image_path"]),
            "target_value": float(row[target_col]),
        }
        record.update({str(k): float(v) for k, v in feats.items()})
        rows.append(record)
    return pd.DataFrame(rows)


def train_test_hb(
    feature_table: pd.DataFrame,
    model_name: str = "xgboost",
    random_state: int = 42,
) -> HbBaselineResult:
    """Train on patient-disjoint train split and evaluate on held-out test."""
    if "patient_id" not in feature_table or "target_value" not in feature_table:
        raise ValueError("feature_table must contain patient_id and target_value")

    train, _, test = patient_split(feature_table, seed=random_state)
    feature_cols = [
        c for c in feature_table.columns
        if c not in {"patient_id", "image_path", "target_value"}
        and pd.api.types.is_numeric_dtype(feature_table[c])
    ]
    if not feature_cols:
        raise ValueError("No numeric features available for training.")

    model = _build_model(model_name, random_state)
    model.fit(train[feature_cols], train["target_value"])
    pred = model.predict(test[feature_cols])

    y_true = test["target_value"].to_numpy(dtype=float)
    metrics = regression_metrics(y_true, pred)
    predictions = test[["patient_id", "image_path", "target_value"]].copy()
    predictions["prediction"] = pred
    return HbBaselineResult(predictions=predictions.reset_index(drop=True), metrics=metrics)


def save_result(result: HbBaselineResult, output_dir: str | Path) -> None:
    """Save predictions and metrics without saving raw patient images."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    result.predictions.to_csv(output / "test_predictions.csv", index=False)
    pd.Series(result.metrics, name="value").to_csv(output / "metrics.csv")


__all__ = ["HbBaselineResult", "build_feature_table", "train_test_hb", "save_result"]
