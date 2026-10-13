import pandas as pd
import pytest

from smartbio.splits import assert_no_patient_overlap, patient_split, unseen_device_split


def _frame(n_patients=20):
    return pd.DataFrame({
        "patient_id": [f"P{i:03d}" for i in range(n_patients) for _ in range(2)],
        "image_id": [f"I{i:03d}_{j}" for i in range(n_patients) for j in range(2)],
        "device_model": ["Phone A" if i % 2 == 0 else "Phone B" for i in range(n_patients) for _ in range(2)],
    })


def test_patient_split_is_deterministic_and_disjoint():
    frame = _frame()
    first = patient_split(frame, seed=17)
    second = patient_split(frame, seed=17)
    assert [x["image_id"].tolist() for x in first] == [x["image_id"].tolist() for x in second]
    assert all(not x.empty for x in first)
    assert_no_patient_overlap(*first)


@pytest.mark.parametrize("missing_id", [None, ""])
def test_patient_split_rejects_missing_or_empty_patient_ids(missing_id):
    frame = _frame()
    frame.loc[frame.index[0], "patient_id"] = missing_id
    with pytest.raises(ValueError, match="patient_id contains"):
        patient_split(frame)


def test_patient_split_rejects_missing_patient_column():
    with pytest.raises(ValueError, match="Missing required column"):
        patient_split(pd.DataFrame({"image_id": ["I1", "I2", "I3", "I4"]}))


def test_patient_split_rejects_too_few_patients():
    with pytest.raises(ValueError, match="At least 4 distinct patients"):
        patient_split(_frame(3))


def test_patient_split_rejects_fractions_that_produce_empty_partition():
    with pytest.raises(ValueError, match="Not enough patient groups|empty partition"):
        patient_split(_frame(4), train_size=0.9, val_size=0.05)


def test_assert_no_patient_overlap_fails_on_overlap():
    frame = _frame()
    train = frame[frame["patient_id"].isin(["P000", "P001"])]
    val = frame[frame["patient_id"].isin(["P001", "P002"])]
    test = frame[frame["patient_id"].isin(["P003", "P004"])]
    with pytest.raises(AssertionError, match="leakage"):
        assert_no_patient_overlap(train, val, test)


def test_unseen_device_split_removes_all_held_out_patients_from_train():
    frame = pd.DataFrame([
        {"patient_id": "P1", "image_id": "a", "device_model": "A"},
        {"patient_id": "P1", "image_id": "b", "device_model": "B"},
        {"patient_id": "P2", "image_id": "c", "device_model": "A"},
        {"patient_id": "P3", "image_id": "d", "device_model": "B"},
    ])
    train, test = unseen_device_split(frame, "A")
    assert set(test["patient_id"]) == {"P1", "P2"}
    assert set(train["patient_id"]) == {"P3"}
    assert not (set(train["patient_id"]) & set(test["patient_id"]))


def test_unseen_device_split_rejects_unknown_patient_identity():
    frame = _frame()
    frame.loc[frame.index[0], "patient_id"] = None
    with pytest.raises(ValueError, match="patient_id contains missing"):
        unseen_device_split(frame, "Phone A")


def test_unseen_device_split_rejects_unknown_device_metadata():
    frame = _frame()
    frame.loc[frame.index[0], "device_model"] = None
    with pytest.raises(ValueError, match="device_model contains"):
        unseen_device_split(frame, "Phone A")
