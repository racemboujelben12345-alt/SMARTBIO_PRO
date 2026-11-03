# SMARTBIO_PRO — NeoJaundice file-level audit

**Audit date:** 2026-11-03
**Dataset:** NeoJaundice
**Scope:** Local inspection of the downloaded archive, image files and CSV metadata.
**Status:** File-level structural audit completed; target provenance and quantitative readiness remain pending.

## 1. Dataset structure

The inspected archive contains:
- An `images/` directory.
- A CSV metadata file: `chd_jaundice_published_2.csv`.

The extracted dataset contains 2,235 image files and a CSV with 2,235 rows and 8 columns.

The CSV columns are:

- `patient_id`
- `image_idx`
- `gender`
- `gestational_age`
- `age(day)`
- `weight`
- `blood(mg/dL)`
- `Treatment`

## 2. Image-to-metadata integrity

The local file-level checks found:

| Check | Result |
|---|---:|
| CSV rows | 2,235 |
| Image files | 2,235 |
| CSV image references | 2,235 |
| Matching image references | 2,235 |
| Missing image files | 0 |
| Duplicate image references | 0 |
| Distinct patient IDs | 745 |
| Images per patient | 3 |

Every patient has exactly three image records in the inspected metadata.

These results establish structural correspondence between the CSV image references and the local image files. They do not establish clinical validity or reference-measurement provenance.

## 3. Missing values and patient-level consistency

The `age(day)` column contains 6 missing values. No missing values were observed in the other seven columns.

For each patient:
- `blood(mg/dL)` is consistent across the three image records.
- `Treatment` is consistent across the three image records.

The metadata therefore repeats patient-level target and treatment values across multiple image rows. These rows must not be treated as independent patients.

## 4. Blood-value inspection

The observed row-level distribution of `blood(mg/dL)` is:

| Statistic | Value |
|---|---:|
| Count | 2,235 image rows |
| Mean | 11.21 mg/dL |
| Standard deviation | 5.21 mg/dL |
| Minimum | 0.00 mg/dL |
| 25th percentile | 7.40 mg/dL |
| Median | 11.80 mg/dL |
| 75th percentile | 15.10 mg/dL |
| Maximum | 25.70 mg/dL |

These statistics are calculated over image rows, not independent patients. Each patient contributes three image records, so patient-level summaries should be used for patient-level statistical analysis.

A value of `0.00 mg/dL` appears in three image rows, corresponding to one patient. Its meaning has not been established. It must not be silently removed, replaced or interpreted as a missing value without source documentation.

## 5. Treatment-label inspection and leakage risk

The observed row counts are:

| Treatment value | Image rows |
|---|---:|
| 0 | 1,302 |
| 1 | 933 |

The inspected CSV shows a perfect relationship between `Treatment` and the 12.9 mg/dL threshold:

| Blood value | Treatment = 0 | Treatment = 1 |
|---|---:|---:|
| `blood(mg/dL) <= 12.9` | 1,302 | 0 |
| `blood(mg/dL) > 12.9` | 0 | 933 |

This relationship raises a target-leakage risk. The exact definition and derivation of `Treatment` must be confirmed from the dataset documentation.

**Do not use `Treatment` as an input feature** for a model predicting `blood(mg/dL)` unless an independent scientific justification demonstrates that doing so is valid. It may encode information derived directly from the target threshold.

## 6. Patient-level splitting requirements

The dataset contains three image records per patient. All images belonging to one patient must remain in the same partition.

SMARTBIO_PRO already provides:
- `patient_split()` for patient-grouped train/validation/test splitting.
- `assert_no_patient_overlap()` to check patient separation.

The intended default proportions are 70% training, 15% validation and 15% testing, grouped by patient ID.

An image-row-level random split would risk patient leakage and must not be used.

No claim is made here that a NeoJaundice split has already been generated or evaluated.

## 7. Target provenance: unresolved requirements

The numeric column `blood(mg/dL)` is a candidate target, but its presence does not by itself satisfy `docs/target_provenance_protocol.md`.

The following information still requires confirmation from the dataset paper or authoritative documentation:

- Exact biological meaning of `blood(mg/dL)`.
- Whether the value represents Total Serum Bilirubin (TSB).
- Reference laboratory method or measurement device.
- Reference measurement identity.
- Reference type (`laboratory` or `validated_reference`).
- Time difference between image acquisition and reference measurement.

Do not populate missing provenance fields by assumption. Do not mark this dataset benchmark-ready until the target provenance contract is satisfied.

## 8. Data handling and repository policy

This audit documents derived structural findings only.

Do not commit:
- The original ZIP archive.
- Neonatal images.
- The raw CSV.
- Patient-level records or identifiable clinical information.

Raw data must remain subject to the dataset's license, access conditions and the project's data policy. Only permitted derived audit documentation should be committed.

## 9. Audit conclusion

The local archive passed the inspected image-to-CSV correspondence checks:
- 2,235 image files matched 2,235 CSV references.
- 745 patients were identified, with three images per patient.
- Patient-level consistency was observed for the blood and treatment fields.

However, important scientific questions remain unresolved:
- The meaning and provenance of the blood target.
- The interpretation of the zero blood value.
- The derivation of the treatment label and its relationship to the target threshold.

**Interim status:** structurally consistent for further investigation; not yet certified as quantitative-benchmark-ready.

This audit makes no claim about model performance, analytical accuracy, clinical validity or regulatory validity.
