"""Patient-safe dataset partitioning utilities.

These helpers prevent patient leakage, but they do not certify that the
underlying patient identifiers or reference measurements are clinically valid.
"""
from __future__ import annotations

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit


def _validate_patient_ids(df: pd.DataFrame) -> None:
    if "patient_id" not in df.columns:
        raise ValueError("Missing required column: patient_id.")
    if df.empty:
        raise ValueError("Cannot split an empty dataset.")
    patient_ids = df["patient_id"]
    if patient_ids.isna().any():
        raise ValueError("patient_id contains missing values; patient-safe splitting is not possible.")
    normalized = patient_ids.astype(str).str.strip()
    if normalized.eq("").any():
        raise ValueError("patient_id contains empty values; patient-safe splitting is not possible.")
    if normalized.nunique() < 4:
        raise ValueError("At least four distinct patients are required for train/validation/test splits.")


def patient_split(df, seed=42, train_size=0.70, val_size=0.15):
    """Create deterministic patient-grouped train/validation/test partitions."""
    if not (0 < train_size < 1 and 0 < val_size < 1 and train_size + val_size < 1):
        raise ValueError("Invalid split fractions: require train_size > 0, val_size > 0 and their sum < 1.")
    _validate_patient_ids(df)

    groups = df["patient_id"].astype(str).str.strip()
    g1 = GroupShuffleSplit(n_splits=1, train_size=train_size, random_state=seed)
    try:
        tr_idx, temp_idx = next(g1.split(df, groups=groups))
        train, temp = df.iloc[tr_idx].copy(), df.iloc[temp_idx].copy()

        rel_val = val_size / (1 - train_size)
        g2 = GroupShuffleSplit(n_splits=1, train_size=rel_val, random_state=seed)
        va_idx, te_idx = next(g2.split(temp, groups=groups.iloc[temp_idx]))
        val, test = temp.iloc[va_idx].copy(), temp.iloc[te_idx].copy()
    except ValueError as exc:
        raise ValueError(
            "Not enough patient groups for the requested train/validation/test fractions."
        ) from exc

    if train.empty or val.empty or test.empty:
        raise ValueError(
            "The requested fractions produced an empty partition; adjust fractions or add patients."
        )
    assert_no_patient_overlap(train, val, test)
    return train, val, test


def assert_no_patient_overlap(train, val, test):
    """Fail closed if patient IDs are missing or overlap across partitions."""
    for name, frame in (("train", train), ("validation", val), ("test", test)):
        _validate_patient_ids(frame)
    sets = [
        set(frame["patient_id"].astype(str).str.strip())
        for frame in (train, val, test)
    ]
    if sets[0] & sets[1] or sets[0] & sets[2] or sets[1] & sets[2]:
        raise AssertionError("Patient leakage detected between splits.")


def unseen_device_split(df, held_out_device):
    """Hold out a device while preventing patient leakage.

    Any patient observed on the held-out device is removed from training, even
    if that patient also has acquisitions from another device. Patients with
    unknown identity are rejected because leakage cannot be ruled out.
    """
    required = {"device_model", "patient_id"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns for unseen-device split: {sorted(missing)}")
    _validate_patient_ids(df)
    if held_out_device is None or not str(held_out_device).strip():
        raise ValueError("held_out_device must be explicitly specified.")
    if df["device_model"].isna().any() or df["device_model"].astype(str).str.strip().eq("").any():
        raise ValueError("device_model contains missing or empty values; unseen-device split is ambiguous.")

    test = df[df["device_model"] == held_out_device].copy()
    if test.empty:
        raise ValueError(f"Held-out device not found: {held_out_device}")
    held_out_patients = set(test["patient_id"].astype(str).str.strip())
    normalized_patients = df["patient_id"].astype(str).str.strip()
    train = df[
        (df["device_model"] != held_out_device)
        & (~normalized_patients.isin(held_out_patients))
    ].copy()
    if train.empty:
        raise ValueError("No training records remain after patient-safe device holdout.")
    assert_no_patient_overlap(train, test, test.iloc[0:0])
    return train, test
