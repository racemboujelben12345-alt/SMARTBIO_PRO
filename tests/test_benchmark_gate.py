import pandas as pd

from smartbio.benchmark_gate import run_benchmark_gate


def frame():
    return pd.DataFrame(
        {
            "patient_id": ["p1", "p2", "p3"],
            "image_id": ["i1", "i2", "i3"],
            "biomarker": ["hemoglobin", "hemoglobin", "hemoglobin"],
            "target_unit": ["g/dL", "g/dL", "g/dL"],
            "target_value": [10.0, 11.0, 12.0],
            "target_source": ["lab", "lab", "lab"],
            "reference_method": ["CBC", "CBC", "CBC"],
            "reference_measurement_id": ["r1", "r2", "r3"],
            "reference_type": ["laboratory", "laboratory", "laboratory"],
            "device_model": ["PhoneA", "PhoneA", "PhoneA"],
            "exposure_us": [10000, 10000, 10000],
            "iso": [100, 100, 100],
            "white_balance_mode": ["locked", "locked", "locked"],
            "working_distance_mm": [50.0, 50.0, 50.0],
            "incidence_angle_deg": [0.0, 0.0, 0.0],
            "illumination": ["flash", "flash", "flash"],
            "acquisition_id": ["a1", "a2", "a3"],
            "roi_type": ["conjunctiva", "conjunctiva", "conjunctiva"],
            "roi_x0": [10, 10, 10],
            "roi_y0": [10, 10, 10],
            "roi_x1": [100, 100, 100],
            "roi_y1": [100, 100, 100],
            "image_width": [200, 200, 200],
            "image_height": [200, 200, 200],
        }
    )


def run(frame_):
    return run_benchmark_gate(
        frame_,
        [10.2, 10.8, 12.1],
        manifest_hash="m",
        expected_biomarker="hemoglobin",
        expected_unit="g/dL",
        n_bootstrap=200,
        n_permutations=200,
    )


def test_gate_passes():
    assert run(frame()).passed


def test_missing_provenance_fails():
    assert not run(frame().drop(columns=["reference_method"])).passed


def test_missing_acquisition_fails():
    assert not run(frame().drop(columns=["device_model"])).passed


def test_missing_roi_provenance_fails():
    assert not run(frame().drop(columns=["roi_x0"])).passed


def test_invalid_target_roi_fails():
    f = frame()
    f.loc[0, "roi_type"] = "forehead"
    result = run(f)
    assert not result.passed
    assert any("invalid ROI provenance" in error for error in result.errors)


def test_partition_overlap_fails():
    f = frame()
    development = f.copy()

    result = run_benchmark_gate(
        f,
        [10.2, 10.8, 12.1],
        manifest_hash="m",
        expected_biomarker="hemoglobin",
        expected_unit="g/dL",
        development_frame=development,
        n_bootstrap=200,
        n_permutations=200,
    )
    assert not result.passed
