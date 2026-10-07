"""Bootstrap inference for paired measurement agreement.

Engineering/statistical inference only. This module does not define clinical
acceptance limits, equivalence, or diagnostic thresholds.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class AgreementBootstrapReport:
    n_pairs: int
    n_bootstrap: int
    confidence_level: float
    seed: int
    mean_bias: float
    mean_bias_ci_low: float
    mean_bias_ci_high: float
    mae: float
    mae_ci_low: float
    mae_ci_high: float
    rmse: float
    rmse_ci_low: float
    rmse_ci_high: float
    loa_low: float | None
    loa_low_ci_low: float | None
    loa_low_ci_high: float | None
    loa_high: float | None
    loa_high_ci_low: float | None
    loa_high_ci_high: float | None

    def to_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


def _validate_pairs(
    frame: pd.DataFrame,
    *,
    reference_column: str,
    measurement_column: str,
    subject_column: str,
) -> np.ndarray:
    required = {reference_column, measurement_column, subject_column}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError("measurement frame must not be empty.")

    df = frame[[reference_column, measurement_column, subject_column]].copy()
    for col in (reference_column, measurement_column):
        df[col] = pd.to_numeric(df[col], errors="coerce")
        values = df[col].to_numpy(float)
        if df[col].isna().any() or not np.isfinite(values).all():
            raise ValueError(f"{col} must contain finite numeric values.")
    if df[subject_column].isna().any():
        raise ValueError("subject identifiers must be present.")

    paired = (
        df.groupby(subject_column, sort=True)[[reference_column, measurement_column]]
        .mean()
        .dropna()
    )
    if len(paired) < 3:
        raise ValueError("at least 3 paired subjects are required.")
    return (
        paired[measurement_column].to_numpy(float)
        - paired[reference_column].to_numpy(float)
    )


def _metrics(errors: np.ndarray) -> tuple[float, float, float, float | None, float | None]:
    bias = float(np.mean(errors))
    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors**2)))
    if len(errors) < 2:
        return bias, mae, rmse, None, None
    sd = float(np.std(errors, ddof=1))
    return bias, mae, rmse, bias - 1.96 * sd, bias + 1.96 * sd


def _percentile_interval(values: np.ndarray, confidence_level: float) -> tuple[float, float]:
    alpha = 1.0 - confidence_level
    return (
        float(np.quantile(values, alpha / 2.0)),
        float(np.quantile(values, 1.0 - alpha / 2.0)),
    )


def analyze_agreement_bootstrap(
    frame: pd.DataFrame,
    *,
    reference_column: str = "reference_value",
    measurement_column: str = "measurement_value",
    subject_column: str = "patient_id",
    n_bootstrap: int = 2000,
    confidence_level: float = 0.95,
    seed: int = 42,
) -> AgreementBootstrapReport:
    if n_bootstrap < 200:
        raise ValueError("n_bootstrap must be at least 200.")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must be between 0 and 1.")
    errors = _validate_pairs(
        frame,
        reference_column=reference_column,
        measurement_column=measurement_column,
        subject_column=subject_column,
    )

    observed = _metrics(errors)
    rng = np.random.default_rng(seed)
    boot = rng.integers(0, len(errors), size=(n_bootstrap, len(errors)))
    bias_values = np.empty(n_bootstrap)
    mae_values = np.empty(n_bootstrap)
    rmse_values = np.empty(n_bootstrap)
    loa_low_values = np.empty(n_bootstrap)
    loa_high_values = np.empty(n_bootstrap)

    for i, indices in enumerate(boot):
        bias, mae, rmse, loa_low, loa_high = _metrics(errors[indices])
        bias_values[i] = bias
        mae_values[i] = mae
        rmse_values[i] = rmse
        loa_low_values[i] = loa_low
        loa_high_values[i] = loa_high

    bias_ci = _percentile_interval(bias_values, confidence_level)
    mae_ci = _percentile_interval(mae_values, confidence_level)
    rmse_ci = _percentile_interval(rmse_values, confidence_level)
    low_ci = _percentile_interval(loa_low_values, confidence_level)
    high_ci = _percentile_interval(loa_high_values, confidence_level)

    return AgreementBootstrapReport(
        n_pairs=len(errors),
        n_bootstrap=n_bootstrap,
        confidence_level=confidence_level,
        seed=seed,
        mean_bias=observed[0],
        mean_bias_ci_low=bias_ci[0],
        mean_bias_ci_high=bias_ci[1],
        mae=observed[1],
        mae_ci_low=mae_ci[0],
        mae_ci_high=mae_ci[1],
        rmse=observed[2],
        rmse_ci_low=rmse_ci[0],
        rmse_ci_high=rmse_ci[1],
        loa_low=observed[3],
        loa_low_ci_low=low_ci[0],
        loa_low_ci_high=low_ci[1],
        loa_high=observed[4],
        loa_high_ci_low=high_ci[0],
        loa_high_ci_high=high_ci[1],
    )
