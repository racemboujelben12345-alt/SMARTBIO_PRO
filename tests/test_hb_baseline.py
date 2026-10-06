import numpy as np
import pandas as pd

from smartbio.hb_baseline import _build_model


def test_baseline_models_are_constructible():
    for name in ("xgboost", "random_forest", "svr"):
        model = _build_model(name)
        X = pd.DataFrame(np.random.default_rng(1).normal(size=(8, 4)))
        y = np.linspace(9.0, 14.0, 8)
        model.fit(X, y)
        assert np.isfinite(model.predict(X)).all()
