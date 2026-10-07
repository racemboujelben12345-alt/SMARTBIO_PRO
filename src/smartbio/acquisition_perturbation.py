"""Paired acquisition perturbation sensitivity analysis.

This is an engineering measurement-quality layer. It quantifies how a declared
acquisition perturbation changes measurements relative to a paired reference.
It does not define clinical acceptance limits or prove clinical equivalence.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PerturbationEffect:
    condition: str
    n_pairs: int
    mean_bias: float
    sd_bias: float | None
    relative_bias_percent: float
    loa_low: float | None
    loa_high: float | None

    def to_dict(self) -> dict[str, object]:
        return {
            "condition": self.condition,
            "n_pairs": self.n_pairs,
            "mean_bias": self.mean_bias,
            "sd_bias": self.sd_bias,
            "relative_bias_percent": self.relative_bias_percent,
            "loa_low": self.loa_low,
            "loa_high": self.loa_high,
        }


@dataclass(frozen=True)
class AcquisitionPerturbationReport:
    n_rows: int
    n_subjects: int
    reference_condition: str
    factor_column: str
    effects: tuple[PerturbationEffect, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "n_rows": self.n_rows,
            "n_subjects": self.n_subjects,
            "reference_condition": self.reference_condition,
            "factor_column": self.factor_column,
            "effects": [effect.to_dict() for effect in self.effects],
        }


def _validate_frame(frame, value_column, subject_column, factor_column):
    required = {value_column, subject_column, factor_column}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError("measurement frame must not be empty.")

    df = frame[[value_column, subject_column, factor_column]].copy()
    df[value_column] = pd.to_numeric(df[value_column], errors="coerce")
    if df[value_column].isna().any() or not np.isfinite(
        df[value_column].to_numpy(float)
    ).all():
        raise ValueError("measurement values must be finite numeric values.")
    if df[subject_column].isna().any() or df[factor_column].isna().any():
        raise ValueError("subject and perturbation identifiers must be present.")
    return df


def analyze_acquisition_perturbation(
    frame,
    *,
    value_column: str = "measurement_value",
    subject_column: str = "patient_id",
    factor_column: str = "perturbation",
    reference_condition: str = "reference",
) -> AcquisitionPerturbationReport:
    """Estimate paired effects of declared acquisition perturbations.

    Each subject is compared within-subject between the reference condition
    and every other condition. Multiple rows per subject/condition are first
    averaged, preserving the paired design without treating repeats as
    independent subjects.
    """
    df = _validate_frame(frame, value_column, subject_column, factor_column)
    if str(reference_condition) not in set(df[factor_column].astype(str)):
        raise ValueError("reference condition is not present.")

    grouped = (
        df.assign(_condition=df[factor_column].astype(str))
        .groupby([subject_column, "_condition"], sort=True)[value_column]
        .mean()
        .reset_index()
    )
    reference = grouped[
        grouped["_condition"] == str(reference_condition)
    ][[subject_column, value_column]].rename(
        columns={value_column: "_reference"}
    )

    if reference.empty:
        raise ValueError("reference condition has no measurements.")

    effects = []
    for condition in sorted(
        c for c in grouped["_condition"].unique()
        if c != str(reference_condition)
    ):
        current = grouped[grouped["_condition"] == condition][
            [subject_column, value_column]
        ].rename(columns={value_column: "_condition_value"})
        paired = reference.merge(current, on=subject_column, how="inner")
        if paired.empty:
            continue

        differences = (
            paired["_condition_value"] - paired["_reference"]
        ).to_numpy(float)
        n_pairs = int(differences.size)
        if n_pairs == 0:
            continue

        bias = float(np.mean(differences))
        sd = (
            float(np.std(differences, ddof=1))
            if n_pairs >= 2
            else None
        )
        reference_mean = float(np.mean(paired["_reference"]))
        if reference_mean == 0:
            relative_bias = float("nan")
        else:
            relative_bias = 100.0 * bias / abs(reference_mean)

        loa_low = loa_high = None
        if sd is not None:
            loa_low = float(bias - 1.96 * sd)
            loa_high = float(bias + 1.96 * sd)

        effects.append(
            PerturbationEffect(
                condition=condition,
                n_pairs=n_pairs,
                mean_bias=bias,
                sd_bias=sd,
                relative_bias_percent=relative_bias,
                loa_low=loa_low,
                loa_high=loa_high,
            )
        )

    if not effects:
        raise ValueError("no paired perturbation conditions are available.")

    return AcquisitionPerturbationReport(
        n_rows=int(len(df)),
        n_subjects=int(df[subject_column].nunique()),
        reference_condition=str(reference_condition),
        factor_column=factor_column,
        effects=tuple(effects),
    )
