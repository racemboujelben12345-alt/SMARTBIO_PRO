import pandas as pd
from smartbio.validator import validate_canonical
from smartbio.splits import patient_split, assert_no_patient_overlap

def test_validator_accepts_valid_record():
    df = pd.DataFrame({
        "patient_id":["p1"], "image_id":["i1"], "image_path":["x.jpg"],
        "source_dataset":["demo"], "biomarker":["hemoglobin"],
        "target_value":[12.0], "target_unit":["g/dL"]
    })
    assert validate_canonical(df)["valid"]

def test_patient_split_is_disjoint():
    df = pd.DataFrame({"patient_id":[f"p{i}" for i in range(40)]})
    a,b,c = patient_split(df)
    assert_no_patient_overlap(a,b,c)

def test_unseen_device_split_is_patient_safe():
    from smartbio.splits import unseen_device_split
    df = pd.DataFrame({
        "patient_id": ["p1", "p1", "p2", "p3"],
        "device_model": ["A", "B", "A", "A"],
    })
    train, test = unseen_device_split(df, "B")
    assert set(test.patient_id) == {"p1"}
    assert "p1" not in set(train.patient_id)


def test_roi_contract_rejects_wrong_target():
    import pytest
    from smartbio.roi import validate_roi_type
    with pytest.raises(ValueError):
        validate_roi_type("hemoglobin", "forehead")

def test_feature_extraction_requires_explicit_roi():
    from PIL import Image
    import tempfile
    from smartbio.features import extract_dataset
    from pathlib import Path
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / 'x.jpg'
        Image.new('RGB', (32, 32), (120, 80, 60)).save(p)
        meta = Path(d) / 'm.csv'
        pd.DataFrame({'patient_id':['p1'], 'image_path':[str(p)], 'roi_type':['conjunctiva']}).to_csv(meta, index=False)
        out = Path(d) / 'o.csv'
        result = extract_dataset(meta, out)
        assert result.loc[0, 'feature_error'] is not None


def test_unseen_device_split_requires_patient_column():
    import pytest
    from smartbio.splits import unseen_device_split
    with pytest.raises(ValueError):
        unseen_device_split(pd.DataFrame({'device_model':['A']}), 'A')


def test_flash_ambient_requires_metadata_pair_keys():
    import pytest
    from smartbio.optical import flash_minus_ambient
    with pytest.raises(ValueError):
        flash_minus_ambient([[[1,1,1]]], [[[0,0,0]]], metadata={'flash':{}, 'ambient':{}})

def test_package_version_is_pro():
    import smartbio
    assert smartbio.__version__.startswith("1.1.0-pro")


def test_audit_gate_requires_patient_split():
    from smartbio.audit import audit_gate
    inv = pd.DataFrame({'exists':[True], 'readable':[True], 'sha256':['abc']})
    q = pd.DataFrame({'quality_error':[None], 'quality_flag_brightness':[True], 'quality_flag_contrast':[True], 'quality_flag_blur':[True], 'quality_flag_saturation':[True]})
    checks, passed = audit_gate(inv, q, pd.DataFrame(), split_report={'passed':False})
    assert checks['patient_split_clean'] is False
    assert passed is False


def test_biophysics_identifiability_rejects_four_chromophores_on_rgb():
    from smartbio.biophysics import identifiability_report
    import numpy as np
    r = identifiability_report(np.ones((3, 4)))
    assert r["full_column_rank"] is False
    assert r["parameters"] == 4


def test_relative_od_requires_positive_reference():
    import pytest
    import numpy as np
    from smartbio.biophysics import relative_optical_density
    with pytest.raises(ValueError):
        relative_optical_density(np.ones((2,2,3))*100, np.zeros((2,2,3)))


def test_auto_white_balance_is_rejected():
    import pytest
    from smartbio.biophysics import validate_physical_capture
    r = validate_physical_capture({
        "image_format":"JPEG", "exposure_us":10000, "iso":100,
        "white_balance_mode":"auto", "raw_available":False,
    })
    assert not r["valid"]
    assert any("white balance" in x.lower() for x in r["errors"])


def test_flash_ambient_channel_gain():
    import numpy as np
    from smartbio.optical import flash_minus_ambient
    x = np.array([[[10.,20.,30.]]])
    a = np.array([[[1.,2.,3.]]])
    y = flash_minus_ambient(x, a, alpha=[2.,3.,4.])
    assert np.allclose(y, [[[8.,14.,18.]]])

def test_physics_rejects_nonpositive_camera_settings():
    from smartbio.biophysics import validate_physical_capture
    r = validate_physical_capture({
        'image_format':'JPEG','exposure_us':0,'iso':-1,
        'white_balance_mode':'manual','raw_available':False,
    })
    assert not r['valid']
    assert any('exposure_us' in x for x in r['errors'])
    assert any('iso' in x for x in r['errors'])


def test_flash_pair_accepts_exposure_alias():
    from smartbio.optical import validate_pair_metadata
    validate_pair_metadata(
        {'device_model':'A','exposure':10000,'iso':100,'white_balance_mode':'manual'},
        {'device_model':'A','exposure_us':10000,'iso':100,'white_balance_mode':'manual'},
    )


def test_legacy_flash_subtraction_requires_metadata():
    import pytest
    from smartbio.calibration import flash_minus_no_flash
    with pytest.raises(ValueError):
        flash_minus_no_flash([[[1,1,1]]], [[[0,0,0]]])


def test_center_roi_is_not_default_scientific_path(tmp_path):
    from PIL import Image
    from smartbio.features import extract
    p = tmp_path / 'x.jpg'
    Image.new('RGB', (16,16), (100,100,100)).save(p)
    import pytest
    with pytest.raises(ValueError):
        extract(p)
