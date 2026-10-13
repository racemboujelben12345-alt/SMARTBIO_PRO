from sklearn.model_selection import GroupShuffleSplit


def _validate_patient_ids(df, min_unique=1):
    if "patient_id" not in df.columns:
        raise ValueError("Missing required column: patient_id.")
    if df.empty:
        raise ValueError("Cannot split an empty dataset.")
    ids = df["patient_id"]
    if ids.isna().any():
        raise ValueError("patient_id contains missing values; patient-safe splitting is not possible.")
    normalized = ids.astype(str).str.strip()
    if normalized.eq("").any():
        raise ValueError("patient_id contains empty values; patient-safe splitting is not possible.")
    if normalized.nunique() < min_unique:
        raise ValueError(f"At least {min_unique} distinct patients are required.")


def patient_split(df, seed=42, train_size=0.70, val_size=0.15):
    if not (0 < train_size < 1 and 0 < val_size < 1 and train_size + val_size < 1):
        raise ValueError("Invalid split fractions.")
    _validate_patient_ids(df, min_unique=4)
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
        raise ValueError("Not enough patient groups for the requested split fractions.") from exc
    if train.empty or val.empty or test.empty:
        raise ValueError("Requested fractions produced an empty partition.")
    assert_no_patient_overlap(train, val, test)
    return train, val, test


def assert_no_patient_overlap(train, val, test):
    for frame in (train, val, test):
        _validate_patient_ids(frame)
    sets = [set(x["patient_id"].astype(str).str.strip()) for x in (train, val, test)]
    if sets[0] & sets[1] or sets[0] & sets[2] or sets[1] & sets[2]:
        raise AssertionError("Patient leakage detected between splits.")


def unseen_device_split(df, held_out_device):
    required = {"device_model", "patient_id"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns for unseen-device split: {sorted(missing)}")
    _validate_patient_ids(df, min_unique=1)
    if held_out_device is None or not str(held_out_device).strip():
        raise ValueError("held_out_device must be explicitly specified.")
    if df["device_model"].isna().any() or df["device_model"].astype(str).str.strip().eq("").any():
        raise ValueError("device_model contains missing or empty values.")
    test = df[df["device_model"] == held_out_device].copy()
    if test.empty:
        raise ValueError(f"Held-out device not found: {held_out_device}")
    held_out = set(test["patient_id"].astype(str).str.strip())
    normalized = df["patient_id"].astype(str).str.strip()
    train = df[(df["device_model"] != held_out_device) & (~normalized.isin(held_out))].copy()
    if train.empty:
        raise ValueError("No training records remain after patient-safe device holdout.")
    if set(train["patient_id"].astype(str).str.strip()) & set(test["patient_id"].astype(str).str.strip()):
        raise AssertionError("Patient leakage detected between unseen-device train and test.")
    return train, test
