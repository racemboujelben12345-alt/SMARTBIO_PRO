import pytest

from smartbio.cluster_bootstrap import cluster_bootstrap_metric_ci


def test_cluster_bootstrap_is_reproducible():
    y = [10, 11, 20, 21, 30, 31]
    p = [11, 10, 19, 22, 29, 32]
    groups = ["p1", "p1", "p2", "p2", "p3", "p3"]
    a = cluster_bootstrap_metric_ci(y, p, groups, n_bootstrap=300, random_state=7)
    b = cluster_bootstrap_metric_ci(y, p, groups, n_bootstrap=300, random_state=7)
    assert a == b
    assert a.n_clusters == 3
    assert a.lower <= a.estimate <= a.upper


def test_cluster_bootstrap_rejects_misaligned_groups():
    with pytest.raises(ValueError):
        cluster_bootstrap_metric_ci([1, 2], [1, 2], ["p1"], n_bootstrap=300)


def test_cluster_bootstrap_rejects_invalid_confidence():
    with pytest.raises(ValueError, match="confidence"):
        cluster_bootstrap_metric_ci(
            [1, 2], [1, 2], ["p1", "p2"], confidence=1.0, n_bootstrap=300
        )
