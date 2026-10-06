# Experiment matrix

| ID | Calibration | Device | Quality gate | Purpose |
|---|---|---|---|---|
| E1 | None | same | No | baseline |
| E2 | affine reference | same | No | calibration effect |
| E3 | optical-reference calibration | same | No | planned alternative calibration |
| E4 | affine | same | Yes | full pipeline |
| E5 | affine | multi-device | Yes | robustness |
| E6 | affine | unseen device | Yes | generalization |

Additional bilirubin:
- forehead vs sternum;
- single ROI vs multi-ROI;
- subgroup analysis where metadata supports it.

Metrics:
MAE, RMSE, R², Pearson r, bias, Bland–Altman,
sensitivity/specificity/ROC-AUC for screening (only if a pre-specified clinical screening threshold and binary reference definition are available),
reject rate, device-wise performance, illumination-wise performance.


## Biophysical constraint
Smartphone RGB is treated as a low-dimensional, device-dependent optical measurement. Claims of chromophore concentration require controlled acquisition, external calibration and laboratory reference validation; no absolute spectroscopy claim is made.
