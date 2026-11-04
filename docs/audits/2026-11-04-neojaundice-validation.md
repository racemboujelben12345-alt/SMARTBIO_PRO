# NeoJaundice — Validation Update (2026-11-04)

## 1. Treatment and blood value relationship

Observed in the CSV (2235 image-level rows):

| Treatment | Minimum blood (mg/dL) | Maximum blood (mg/dL) | Rows |
|---|---:|---:|---:|
| 0 | 0.0 | 12.9 | 1302 |
| 1 | 13.0 | 25.7 | 933 |

A threshold label was computed as:

`threshold_label = 1 if blood(mg/dL) > 12.9 else 0`

The cross-tabulation showed an exact match between Treatment and this threshold label:

| Treatment | threshold 0 | threshold 1 |
|---|---:|---:|
| 0 | 1302 | 0 |
| 1 | 0 | 933 |

### ML implication

Do not use `Treatment` as an input feature when predicting blood bilirubin values. Its exact relationship with the threshold-derived label creates a strong data leakage risk.

The exact clinical meaning and derivation of `Treatment` still require confirmation from the dataset documentation.

## 2. Zero blood value

One patient (`patient_id = 1302`) has `blood(mg/dL) = 0.0` across all three image rows.

- Images: `1302-1.jpg`, `1302-2.jpg`, `1302-3.jpg`
- Treatment: 0
- The value is retained without modification.
- Its clinical interpretation remains unverified.

## 3. Image naming and patient identity

For the inspected records, the numeric filename prefix matches `patient_id` (for example, patient 1 has `0001-1.jpg`, `0001-2.jpg`, and `0001-3.jpg`).

The suffixes `-1`, `-2`, and `-3` have not yet been mapped reliably to anatomical regions. Keep `roi_type` as unknown until verified.

## 4. Data integrity and provenance status

- Keep all images belonging to a patient in the same data split.
- Do not use `Treatment` as a model input.
- Do not modify or remove the zero value without evidence.
- Do not assume target provenance fields that are not documented.
- `target_source`, `reference_method`, and `reference_measurement_id` still require verification before the dataset can be considered benchmark-ready.

## 5. Current conclusion

The CSV shows a perfect correspondence between `Treatment` and the threshold at 12.9 mg/dL. This is an observed data relationship, not by itself proof of the clinical definition of Treatment.

Further source documentation is required before finalizing the NeoJaundice dataset adapter.
