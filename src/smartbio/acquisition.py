"""Acquisition-level controls for quantitative smartphone imaging.

The acquisition contract is a fail-closed metadata layer. It does not infer
missing camera state and it does not turn consumer RGB/JPEG into spectroscopy.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping

import numpy as np

REQUIRED_QUANTITATIVE_FIELDS = {
    "device_model", "exposure_us", "iso", "white_balance_mode",
    "working_distance_mm", "incidence_angle_deg", "illumination",
}

ALLOWED_ILLUMINATION = {"flash", "ambient", "controlled_led", "reference"}
LOCKED_WB_VALUES = {"locked", "manual", "fixed"}


@dataclass(frozen=True)
class AcquisitionContract:
    """Immutable declaration of the acquisition state used for a record."""

    device_model: str
    exposure_us: float
    iso: float
    white_balance_mode: str
    working_distance_mm: float
    incidence_angle_deg: float
    illumination: str
    raw_available: bool = False

    def __post_init__(self) -> None:
        text_fields = {
            "device_model": self.device_model,
            "white_balance_mode": self.white_balance_mode,
            "illumination": self.illumination,
        }
        for name, value in text_fields.items():
            if not str(value).strip():
                raise ValueError(f"{name} must be non-empty.")

        numeric = {
            "exposure_us": self.exposure_us,
            "iso": self.iso,
            "working_distance_mm": self.working_distance_mm,
            "incidence_angle_deg": self.incidence_angle_deg,
        }
        for name, value in numeric.items():
            if not math.isfinite(float(value)):
                raise ValueError(f"{name} must be finite.")
            if float(value) <= 0 and name != "incidence_angle_deg":
                raise ValueError(f"{name} must be positive.")

        angle = float(self.incidence_angle_deg)
        if not 0 <= angle <= 90:
            raise ValueError("incidence_angle_deg must be in [0, 90].")

        if str(self.white_balance_mode).strip().lower() in {"auto", "awb"}:
            raise ValueError("Auto white balance is not allowed for quantitative capture.")

        if str(self.illumination).strip().lower() not in ALLOWED_ILLUMINATION:
            raise ValueError(
                f"Unsupported illumination condition: {self.illumination!r}."
            )


def _missing(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    try:
        return bool(pd_isna(value))
    except Exception:
        return False


def pd_isna(value) -> bool:
    try:
        result = np.isnan(value)
        return bool(result) if np.ndim(result) == 0 else False
    except (TypeError, ValueError):
        return False


def acquisition_gate(row: Mapping, *, quantitative: bool = True):
    """Validate acquisition metadata without inventing missing values."""
    errors: list[str] = []
    warnings: list[str] = []

    if quantitative:
        for key in sorted(REQUIRED_QUANTITATIVE_FIELDS):
            if key not in row or _missing(row[key]):
                errors.append(f"Missing quantitative acquisition field: {key}")

        if not errors:
            try:
                AcquisitionContract(
                    device_model=str(row["device_model"]).strip(),
                    exposure_us=float(row["exposure_us"]),
                    iso=float(row["iso"]),
                    white_balance_mode=str(row["white_balance_mode"]).strip(),
                    working_distance_mm=float(row["working_distance_mm"]),
                    incidence_angle_deg=float(row["incidence_angle_deg"]),
                    illumination=str(row["illumination"]).strip().lower(),
                    raw_available=bool(row.get("raw_available", False)),
                )
            except (TypeError, ValueError) as exc:
                errors.append(str(exc))

    illumination = str(row.get("illumination", "")).strip().lower()
    if illumination and illumination not in ALLOWED_ILLUMINATION:
        warnings.append(
            "Unknown illumination condition; optical comparability is not established."
        )

    wb = str(row.get("white_balance_mode", "")).strip().lower()
    if wb in {"auto", "awb"} and not any("white balance" in e.lower() for e in errors):
        errors.append("Auto white balance must be disabled/locked.")

    return {"valid": not errors, "errors": errors, "warnings": warnings}


def contract_from_row(row: Mapping) -> AcquisitionContract:
    """Build a strict contract from a metadata row; never impute missing state."""
    result = acquisition_gate(row, quantitative=True)
    if not result["valid"]:
        raise ValueError("Acquisition contract failed: " + "; ".join(result["errors"]))
    return AcquisitionContract(
        device_model=str(row["device_model"]).strip(),
        exposure_us=float(row["exposure_us"]),
        iso=float(row["iso"]),
        white_balance_mode=str(row["white_balance_mode"]).strip().lower(),
        working_distance_mm=float(row["working_distance_mm"]),
        incidence_angle_deg=float(row["incidence_angle_deg"]),
        illumination=str(row["illumination"]).strip().lower(),
        raw_available=bool(row.get("raw_available", False)),
    )
