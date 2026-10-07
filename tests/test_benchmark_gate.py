import pandas as pd
from smartbio.benchmark_gate import run_benchmark_gate

def frame():
    return pd.DataFrame({
        "patient_id":["p1","p2","p3"],"image_id":["i1","i2","i3"],"acquisition_id":["a1","a2","a3"],
        "biomarker":["hemoglobin"]*3,"target_unit":["g/dL"]*3,"target_value":[10.,11.,12.],
        "target_source":["lab"]*3,"reference_method":["CBC"]*3,"reference_measurement_id":["r1","r2","r3"],
        "reference_type":["laboratory"]*3,"device_model":["D1"]*3,"exposure_us":[10000.]*3,
        "iso":[100.]*3,"white_balance_mode":["locked"]*3,"working_distance_mm":[50.]*3,
        "incidence_angle_deg":[0.]*3,"illumination":["flash"]*3})

def test_gate_passes():
    f=frame(); r=run_benchmark_gate(f,[10.2,10.8,12.1],manifest_hash="m",
<<<<<<< HEAD
        expected_biomarker="hemoglobin",expected_unit="g/dL",n_bootstrap=200,n_permutations=200)
=======
        expected_biomarker="hemoglobin",expected_unit="g/dL",n_bootstrap=20,n_permutations=20)
>>>>>>> origin/main
    assert r.passed

def test_missing_provenance_fails():
    f=frame().drop(columns=["reference_method"])
    r=run_benchmark_gate(f,[10,11,12],manifest_hash="m",expected_biomarker="hemoglobin",expected_unit="g/dL")
    assert not r.passed

def test_missing_acquisition_fails():
    f=frame().drop(columns=["iso"])
    r=run_benchmark_gate(f,[10,11,12],manifest_hash="m",expected_biomarker="hemoglobin",expected_unit="g/dL")
    assert not r.passed

def test_partition_overlap_fails():
    f=frame(); d=f.copy()
    r=run_benchmark_gate(f,[10,11,12],manifest_hash="m",expected_biomarker="hemoglobin",expected_unit="g/dL",development_frame=d)
    assert not r.passed
