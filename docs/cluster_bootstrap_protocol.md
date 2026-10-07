# Patient-Cluster Bootstrap Protocol v1

## Purpose

Medical imaging datasets commonly contain repeated observations from the same
patient. A row-level bootstrap can therefore underestimate uncertainty because
it treats correlated observations as independent.

This protocol resamples **patient clusters**, keeping every observation from a
sampled patient together.

## Procedure

1. Freeze the evaluation predictions.
2. Define the patient identifier before resampling.
3. Sample patient IDs with replacement.
4. Include all rows belonging to each sampled patient.
5. Recompute the metric.
6. Repeat for the configured number of bootstrap replicates.
7. Report the percentile confidence interval and number of unique patients.

## Interpretation

The interval describes uncertainty under the cluster-resampling assumption.
It is not a clinical confidence interval and does not repair selection bias,
dataset shift, measurement bias, or patient-identification errors.

For single-observation-per-patient datasets, cluster bootstrap reduces to the
ordinary row bootstrap.

## Required reporting

At minimum:

- metric and point estimate
- confidence level
- number of bootstrap replicates
- number of rows
- number of unique patients
- random seed
- experiment manifest hash
