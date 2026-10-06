# SmartBio PRO

**Biophysics-aware, quality-gated, multi-device smartphone optical biomarker research platform**

Targets:
- Hemoglobin (Hb)
- Bilirubin

SmartBio is a research prototype for estimation/screening, not a clinical diagnostic device.

## Architecture

RAW
 ↓
Schema discovery
 ↓
Explicit mapping (never guessed)
 ↓
Canonical provenance-preserving dataset
 ↓
Integrity audit
 ├─ inventory
 ├─ exact duplicates
 ├─ image readability/dimensions
 ├─ missingness
 ├─ quality
 ├─ target sanity
 └─ patient leakage
 ↓
Patient-level / device-held-out splits
 ↓
Explicit anatomical ROI + optical/color features
 ↓
Biophysical guardrails
 ├─ sRGB linearization
 ├─ relative optical-density model (reference required)
 ├─ absorption + scattering forward model
 ├─ chromophore identifiability check
 └─ camera/acquisition physics audit
 ↓
Calibration (implemented: affine; other modes are experimental plans)
 ↓
ML + uncertainty (research layer)
 ↓
Regression/agreement evaluation
 ↓
Robustness report

## Installation

```bash
pip install -r requirements.txt
pip install -e .
```

## First run

```bash
python -m smartbio.cli discover --metadata data/metadata/YOUR.csv
```

Then edit:
`configs/mapping.template.yaml`

Only after explicit mapping:

```bash
python -m smartbio.cli canonicalize \
  --metadata data/metadata/YOUR.csv \
  --mapping configs/mapping.template.yaml \
  --dataset YOUR_DATASET \
  --biomarker hemoglobin \
  --unit g/dL \
  --output data/canonical/hb.csv
```

Then:

```bash
python -m smartbio.cli audit \
  --metadata data/canonical/hb.csv \
  --output reports/data_audit/hb
```

Only if the audit passes:

```bash
python -m smartbio.cli split \
  --metadata data/canonical/hb.csv \
  --output data/splits/hb

# Physics/acquisition audit before quantitative optical modeling
python -m smartbio.cli physics-audit \
  --metadata data/canonical/hb.csv \
  --output reports/data_audit/hb/physics_audit.json
```

## Biophysical rules

1. Smartphone RGB/JPEG values are camera-encoded signals, not calibrated spectral irradiance.
2. Tissue is modeled as an absorbing **and scattering** medium; a straight Beer-Lambert inversion is not accepted as an absolute tissue measurement.
3. Relative optical density requires a valid reference image and controlled geometry.
4. Flash/ambient correction uses a calibrated channel-wise gain; naive subtraction is not considered quantitative.
5. Auto white balance is rejected for quantitative color experiments.
6. RGB has at most three independent measurement channels; unconstrained inversion of four chromophores (e.g. HbO2, Hb, bilirubin, melanin) is underdetermined.
7. Spectral extinction coefficients must be supplied from an external traceable source; the repository does not invent biological constants.
8. Working distance, incidence angle, exposure, ISO and illumination state are treated as physical confounders.

## Scientific rules

1. No image-level random split.
2. No patient appears in multiple partitions.
3. Calibration must be fitted only on training/calibration data.
4. External datasets are not silently mixed into training.
5. Quality flags do not delete raw data.
6. Thresholds are engineering starting points, not clinical thresholds.
7. Hb and bilirubin are separate model branches.
8. Reference standards remain laboratory Hb and TSB.

## PRO scientific safeguards

- Hb and bilirubin are independent target-specific branches.
- Hb ROI contracts: conjunctiva or nail-bed. Bilirubin ROI contracts: forehead, sternum, or abdomen.
- The code does not claim automatic anatomical localization; a validated detector is required before deployment.
- Flash/no-flash subtraction requires comparable device, exposure and ISO metadata; supplied white-balance/geometry metadata are also checked when present.
- Saturated pixels are explicitly flagged rather than silently treated as valid optical measurements.
- Unseen-device validation is patient-safe: patients appearing on the held-out device are excluded from training.
- Calibration requires finite paired observations and is intended to be fitted only on training/calibration data.
- Evaluation should include agreement, subgroup/device robustness and uncertainty coverage, not correlation alone.

## Scientific status

SmartBio PRO is a research framework. Its biophysical layer is a guardrail/forward-model layer, not a substitute for calibrated spectroscopy, Monte Carlo light-transport inversion, laboratory reference measurements, or clinical validation. It is **not** a validated clinical diagnostic device and its engineering thresholds are not clinical decision thresholds.
