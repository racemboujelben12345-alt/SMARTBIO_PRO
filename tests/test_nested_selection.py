import numpy as np
from sklearn.linear_model import Ridge

from smartbio.nested_selection import nested_group_cv


def test_nested_group_cv_is_group_disjoint_and_reproducible():
    rng = np.random.default_rng(4)
    groups = np.repeat(np.arange(12), 2)
    X = rng.normal(size=(24, 3))
    y = 2 * X[:, 0] - X[:, 1] + rng.normal(scale=0.1, size=24)
    result = nested_group_cv(
        X, y, groups,
        Ridge(),
        {"alpha": [0.1, 1.0, 10.0]},
        outer_splits=3,
        inner_splits=2,
    )
    assert result.n_outer_folds == 3
    assert len(result.outer_mae) == 3
    assert np.isfinite(result.mean_mae)
    assert np.isfinite(result.mean_rmse)


def test_nested_group_cv_rejects_insufficient_groups():
    with __import__("pytest").raises(ValueError, match="not enough"):
        nested_group_cv(
            np.ones((4, 2)),
            np.ones(4),
            ["p1", "p1", "p2", "p2"],
            Ridge(),
            {"alpha": [1.0]},
            outer_splits=3,
            inner_splits=2,
        )
