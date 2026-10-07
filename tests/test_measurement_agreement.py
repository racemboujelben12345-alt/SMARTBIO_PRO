import pandas as pd
import pytest
from smartbio.measurement_agreement import analyze_measurement_agreement

def test_paired_agreement_and_error_decomposition():
    frame=pd.DataFrame({"patient_id":[1,2,3],"reference_value":[10.,20.,30.],"measurement_value":[11.,19.,31.]})
    r=analyze_measurement_agreement(frame)
    assert r.n_pairs==3
    assert r.mean_bias==pytest.approx(1/3)
    assert r.mae==pytest.approx(1.)
    assert r.rmse==pytest.approx(1.)
    assert r.error_sd==pytest.approx((4/3)**0.5)
    assert r.loa_low==pytest.approx(1/3-1.96*((4/3)**0.5))
    assert r.loa_high==pytest.approx(1/3+1.96*((4/3)**0.5))

def test_repeated_rows_are_averaged_within_subject():
    frame=pd.DataFrame({"patient_id":[1,1,2,2],"reference_value":[10.,12.,20.,20.],"measurement_value":[11.,13.,19.,21.]})
    r=analyze_measurement_agreement(frame)
    assert r.n_pairs==2
    assert r.mean_reference==pytest.approx(15.5)
    assert r.mean_measurement==pytest.approx(16.)
    assert r.mean_bias==pytest.approx(.5)

def test_zero_reference_mean_fails_closed():
    frame=pd.DataFrame({"patient_id":[1,2],"reference_value":[-1.,1.],"measurement_value":[0.,0.]})
    with pytest.raises(ValueError,match="mean reference"): analyze_measurement_agreement(frame)

def test_nonnumeric_measurement_fails_closed():
    frame=pd.DataFrame({"patient_id":[1,2],"reference_value":[10.,20.],"measurement_value":["bad",21.]})
    with pytest.raises(ValueError,match="finite numeric"): analyze_measurement_agreement(frame)

def test_missing_subject_is_rejected():
    frame=pd.DataFrame({"patient_id":[1,None],"reference_value":[10.,20.],"measurement_value":[11.,21.]})
    with pytest.raises(ValueError,match="subject"): analyze_measurement_agreement(frame)
