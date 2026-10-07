import json
import numpy as np

from smartbio.benchmark import build_benchmark_report


def test_benchmark_report_is_reproducible_and_serializable():
    y = np.array([10, 11, 20, 21, 30, 31], dtype=float)
    p = np.array([11, 10, 19, 22, 29, 32], dtype=float)
    groups = ["p1", "p1", "p2", "p2", "p3", "p3"]

    a = build_benchmark_report(
        y, p, groups,
        manifest_hash="abc123",
        n_bootstrap=250,
        n_permutations=250,
        random_state=8,
    )
    b = build_benchmark_report(
        y, p, groups,
        manifest_hash="abc123",
        n_bootstrap=250,
        n_permutations=250,
        random_state=8,
    )

    assert a == b
    payload = json.loads(a.to_json())
    assert payload["n_patients"] == 3
    assert set(payload["cluster_ci"]) == {"mae", "rmse", "r2", "pearson_r"}
    assert set(payload["permutation"]) == {"mae", "rmse"}


def test_benchmark_rejects_alignment_error():
    import pytest
    with pytest.raises(ValueError, match="align"):
        build_benchmark_report(
            [1, 2], [1], ["p1", "p2"], manifest_hash="x",
            n_bootstrap=250, n_permutations=250,
        )
