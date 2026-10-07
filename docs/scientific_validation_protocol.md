# Scientific Validation Protocol v1

## Purpose

Scientific Validation v1 adds statistical and subgroup diagnostics around a
**frozen** SmartBio prediction pipeline. It does not fit a model, tune
hyperparameters, select features, or calibrate an external dataset.

The objective is to quantify uncertainty in reported performance and expose
heterogeneity that can be hidden by one global metric.

## Mandatory order

1. Lock the development pipeline.
2. Freeze preprocessing, calibration, feature definitions, model, and
   uncertainty configuration.
3. Generate predictions exactly once for the evaluation partition.
4. Run the global regression and Bland–Altman metrics.
5. Add bootstrap confidence intervals to predeclared primary metrics.
6. Run predeclared subgroup analyses.
7. Investigate failures or large subgroup degradation without changing the
   frozen evaluation result.
8. Any methodological change starts a new development experiment.

## Statistical uncertainty

`bootstrap_metric_ci()` uses paired non-parametric bootstrap resampling of
observed target/prediction pairs. The default is a 95% percentile CI with
2,000 replicates and a deterministic random seed.

The interval describes sampling uncertainty of the observed evaluation metric;
it is **not** a clinical confidence interval and does not compensate for
dataset shift or selection bias.

For very small or dependent samples, patient-level or cluster bootstrap should
be preferred over row-level resampling. The current helper is intended for
independent evaluation rows and must not be used to break patient clustering.

## Leakage controls

`assert_patient_disjoint()` rejects patient overlap between evaluation
partitions and rejects duplicate patient IDs within a partition.

For multi-image or longitudinal datasets, all observations belonging to one
patient must remain in the same partition. Device-held-out evaluation must
also apply the existing cross-device patient exclusion rule.

## Subgroup analysis

`subgroup_metrics()` evaluates frozen predictions by a predeclared grouping
variable such as device, acquisition condition, ROI, or study site.

Groups below the configured minimum sample size are omitted rather than given
unstable estimates. Subgroup analysis is descriptive unless a multiplicity
and hypothesis-testing plan is explicitly declared.

## Required reporting

For each primary evaluation:

- sample count and patient count
- MAE, RMSE, R², Pearson correlation
- Bland–Altman bias and 95% limits of agreement
- bootstrap CI for the primary metric(s)
- subgroup performance and sample sizes
- uncertainty coverage and interval width when conformal intervals exist
- abstention/repeat-acquisition rate when an abstention rule is active

## Interpretation

A wider confidence interval indicates limited statistical precision. A
subgroup degradation indicates possible heterogeneity or domain shift; it is
not automatically evidence that the model is invalid.

No result from this protocol alone establishes clinical validity, diagnostic
accuracy, regulatory equivalence, or population-wide generalization.
