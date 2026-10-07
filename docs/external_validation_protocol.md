# External validation protocol v1

External validation is the independent-domain test of a frozen SmartBio pipeline.

## Rules

1. External observations are never used for fitting, feature selection, calibration, threshold selection, or model selection.
2. Freeze preprocessing, calibration, regression model and uncertainty calibration before opening the external labels.
3. Require biomarker and target-unit compatibility.
4. Require explicit dataset identity and patient IDs.
5. Reject any patient overlap between development and external data.
6. Run the frozen pipeline once and report results without retuning.
7. If the external result motivates a change, that change starts a new development experiment.

## Report

Report sample count and patient count, MAE, RMSE, R2, Pearson r, Bland–Altman bias and 95% limits, plus uncertainty coverage and interval width when intervals are available.

External degradation is evidence of domain shift, not automatically model failure. Inspect acquisition conditions, device processing, ROI protocol and calibration assumptions before proposing adaptation.

## Scientific boundary

This protocol tests transportability to an independent dataset. It does not establish clinical validity, diagnostic performance, regulatory equivalence, or population-wide generalization.
