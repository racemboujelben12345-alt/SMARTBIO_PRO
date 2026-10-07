import pandas as pd
import pytest

from smartbio.agreement_inference import analyze_agreement_bootstrap


def _frame():
    return pd.DataFrame(
        {
            "patient_id": [1, 2, 3, 4, 5, 6],
            "reference_value": [10., 12., 15., 18., 21., 25.],
            "measurement_value": [10.5, 11.5, 15.5, 17.0, 22.0, 24.0],
        }
    )


def test_bootstrap_is_reproducible_and_contains_observed_metrics():
    frame = _frame()
    first = analyze_agreement_bootstrap(frame, n_bootstrap=400, seed=42)
    second = analyze_agreement_bootstrap(frame, n_bootstrap=400, seed=42)
    assert first == second
    assert first.n_pairs == 6
    assert first.mean_bias == pytest.approx(-1.0 / 12.0)
    assert first.mean_bias_ci_low <= first.mean_bias <= first.mean_bias_ci_high
    assert first.mae_ci_low <= first.mae <= first.mae_ci_high
    assert first.rmse_ci_low <= first.rmse <= first.rmse_ci_high
    assert first.loa_low is not None
    assert first.loa_high is not None


def test_repeated_rows_are_averaged_by_subject():
    frame = pd.concat([_frame(), _frame().iloc[[0]].assign(reference_value=11.0, measurement_value=11.0)])
    report = analyze_agreement_bootstrap(frame, n_bootstrap=300)
    assert report.n_pairs == 6


def test_bootstrap_requires_enough_pairs():
    frame = _frame().iloc[:2]
    with pytest.raises(ValueError, match="at least 3"):
        analyze_agreement_bootstrap(frame)


def test_bootstrap_requires_valid_count_and_confidence():
    with pytest.raises(ValueError, match="at least 200"):
        analyze_agreement_bootstrap(_frame(), n_bootstrap=199)
    with pytest.raises(ValueError, match="between 0 and 1"):
        analyze_agreement_bootstrap(_frame(), confidence_level=1.0)
