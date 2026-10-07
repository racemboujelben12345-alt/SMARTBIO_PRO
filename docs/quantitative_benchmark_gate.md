# Quantitative Benchmark Gate v1

Before quantitative performance is reported, the evaluation frame must pass four boundaries:

1. **Target provenance** — biomarker, unit, source, reference method and reference measurement identity.
2. **Acquisition contract** — device, exposure, ISO, white balance, working distance, incidence angle and illumination.
3. **Partition identity** — no patient, acquisition or image identity overlap across development, calibration and evaluation.
4. **Frozen statistical evaluation** — only after the first three gates does the existing benchmark engine compute MAE, RMSE, R², Pearson, Bland–Altman, patient-cluster bootstrap confidence intervals and permutation tests.

Repeated optical acquisitions may legitimately reference the same laboratory measurement; therefore the benchmark gate does not require globally unique reference IDs. It still preserves the reference identity for auditability.

Passing the gate is a research reproducibility condition, not proof of analytical validity, clinical validity or regulatory clearance.
