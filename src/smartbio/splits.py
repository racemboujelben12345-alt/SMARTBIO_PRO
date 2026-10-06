from sklearn.model_selection import GroupShuffleSplit

def patient_split(df, seed=42, train_size=0.70, val_size=0.15):
    if train_size <= 0 or val_size <= 0 or train_size + val_size >= 1:
        raise ValueError("Invalid split fractions.")

    g1 = GroupShuffleSplit(n_splits=1, train_size=train_size, random_state=seed)
    tr_idx, temp_idx = next(g1.split(df, groups=df["patient_id"]))
    train, temp = df.iloc[tr_idx].copy(), df.iloc[temp_idx].copy()

    rel_val = val_size / (1 - train_size)
    g2 = GroupShuffleSplit(n_splits=1, train_size=rel_val, random_state=seed)
    va_idx, te_idx = next(g2.split(temp, groups=temp["patient_id"]))
    val, test = temp.iloc[va_idx].copy(), temp.iloc[te_idx].copy()

    return train, val, test

def assert_no_patient_overlap(train, val, test):
    sets = [set(x["patient_id"]) for x in (train,val,test)]
    if sets[0]&sets[1] or sets[0]&sets[2] or sets[1]&sets[2]:
        raise AssertionError("Patient leakage detected between splits.")

def unseen_device_split(df, held_out_device):
    """Hold out a device while preventing patient leakage.

    Any patient observed on the held-out device is removed from training, even
    if that patient also has acquisitions from another device.
    """
    required = {"device_model", "patient_id"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns for unseen-device split: {sorted(missing)}")
    test = df[df["device_model"] == held_out_device].copy()
    if test.empty:
        raise ValueError(f"Held-out device not found: {held_out_device}")
    held_out_patients = set(test["patient_id"])
    train = df[(df["device_model"] != held_out_device) & (~df["patient_id"].isin(held_out_patients))].copy()
    if train.empty:
        raise ValueError("No training records remain after patient-safe device holdout.")
    return train, test
