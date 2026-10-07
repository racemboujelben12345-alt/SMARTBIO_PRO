# Uncertainty Calibration Diagnostics v1

## Purpose

Evaluate whether frozen prediction intervals achieve their declared nominal
coverage on an evaluation set. This is an engineering/statistical diagnostic,
not a clinical confidence statement.

## Reported quantities

- nominal coverage: `1 - alpha`
- observed empirical coverage
- coverage error
- miss rate
- mean and median interval width
- optional subject-level bootstrap 95% interval for observed coverage

## Leakage and repeated observations

The diagnostic consumes already-generated intervals. It does not fit models,
recalibrate conformal quantiles, select features, or tune thresholds.

When subject identifiers are supplied, bootstrap resampling occurs at subject
level. Repeated observations from the same subject therefore remain clustered.

## Interpretation

Observed coverage below nominal coverage indicates under-coverage on the
evaluation sample; above nominal coverage indicates conservative intervals.
This does not establish population coverage.

The bootstrap interval summarizes uncertainty in the observed coverage under
subject-level resampling. It is not a clinical confidence interval.
