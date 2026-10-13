# SMARTBIO_PRO — Dataset source and compatibility audit

**Audit date:** 2026-10-13  
**Scope:** public dataset cards and published repository metadata. This is a source-level audit only; the raw downloaded files have not been inspected in this pass.

## 1. SEWA Rural Anemia Dataset

**Source:** https://huggingface.co/datasets/sewa-rural-care/anemia-survey-data  
**Dataset version shown by source:** 1.0 (April 2026)  
**License shown by source:** CC BY-NC 4.0, with an access/data-use agreement.

### Source facts observed

- The dataset card describes conjunctiva, fingernail-open, fingernail-closed, tongue and PPG modalities.
- It documents `participant_uuid` as the participant identifier.
- The published metadata uses flattened camera fields such as `cam_Anemia_Conjunctiva_exposure_ns`, `cam_Anemia_Conjunctiva_iso`, `cam_Anemia_Conjunctiva_awb_mode` and `cam_Anemia_Conjunctiva_flash_mode`.
- The card identifies `haemoglobin_gdl` as primary venous-blood-draw ground truth and `cbc_hgb_gdl` as a CBC field.
- The source says acquisition metadata are available for device/camera parameters; it describes the primary device as Samsung Galaxy S24 and reports flash-enabled collection protocols.
- The data are access-gated. The card requires a data-use agreement, non-commercial research use, attribution, no re-identification, secure handling, and no re-hosting/redistribution of raw files without written permission. The repository must not commit or publicly mirror the raw dataset.

### Compatibility defects found and action

The previous adapter expected `patient_uuid` only, expected a JSON-style `camera_meta_conjunctiva` object, and treated `haemoglobin_gdl` as a survey fallback. Those assumptions do not match the published flattened schema and ground-truth description.

The working branch now:
- accepts `participant_uuid` as the primary published identifier while retaining legacy aliases;
- reads the published flattened camera columns for each modality, as well as the legacy JSON representation;
- classifies `cbc_hgb_gdl` as laboratory CBC and `haemoglobin_gdl` as venous-blood-draw laboratory Hb;
- reserves `self_reported` for explicitly survey-named fallback fields;
- maps recognized flash modes only, leaving missing or unknown modes missing;
- retains tongue rows in canonical ingestion, while the quantitative ROI gate continues to reject tongue as an Hb ROI.

### Still outstanding

- Obtain/confirm authorized access before inspecting actual participant files.
- Verify exact source column names and data types from the downloaded metadata, not only the dataset card.
- Audit file counts, readability, dimensions, hashes, exact/near duplicates, broken image paths, missingness and value distributions.
- Verify CBC/venous reference semantics and whether both columns represent distinct measurements or alternate representations.
- Verify the real values and encoding of `flash_mode`, `awb_mode`, exposure and ISO.
- Confirm each image row links to the correct patient-level reference without multiplying one blood measurement into falsely independent observations. Repeated images/modalities from one patient must remain grouped by patient during splitting.
- Store only derived audit summaries/manifests in this repository unless the dataset owner explicitly permits raw-data redistribution.

**Interim status:** source is relevant for Hb research and the adapter now targets the published schema, but quantitative readiness is pending file-level audit and access compliance.

## 2. Fingertip Video Dataset for Hb

**Source:** https://www.open-access.bcu.ac.uk/15484/  
**Publication:** Sabir, Khan and Ishaq (2024), IEEE Access; DOI 10.1109/ACCESS.2024.3398353.  
**Visible license on the repository page:** Creative Commons Attribution-NonCommercial-NoDerivatives for the accepted paper.

### Source facts observed

- The publication describes approximately one-minute fingertip video recordings from 150 anemic patients, ages 6 months to 32 years.
- The paper reports Hb values from 4.3 to 12.4 g/dL and comparison with CBC laboratory reports.
- The source page's visible license applies to the accepted paper; it does not by itself establish the license or redistribution permission for the underlying video files.

### Decision

Keep the adapter as an explicit-manifest intake only. Do not infer that a supplied number is a CBC result, that the reference ID is verified, or that flash was active solely because the dataset is a fingertip PPG dataset. Before quantitative use, confirm the data-file license/access terms and verify patient-to-video-to-CBC linkage, units, measurement timing, device, exposure/ISO/WB and ROI/representation semantics. The current `fingertip` ROI is outside the quantitative image ROI contract; PPG/video analysis needs a separate validated representation contract rather than relabeling it as conjunctiva or nailbed.

**Interim status:** useful candidate for a distinct PPG branch; quantitative readiness and raw-data licensing are unverified.

## 3. Neonatal Jaundice Assessment — Mendeley Data

**Source:** https://data.mendeley.com/datasets/yfsz6c36vc/1  
**DOI:** 10.17632/yfsz6c36vc.1  
**License shown by source:** CC BY 4.0.

### Source facts observed

- The landing page describes images from 300 infants, with forehead and sternum sites, JPG images at 640 × 480.
- It says TSB was determined from blood samples and TcB was measured using an MBJ20 meter.
- Images were captured within 30 minutes of TSB/TcB measurements, according to the landing page.
- The collection was reported at Ghaem Hospital in Mashhad, Iran, from January to May 2023, with an ethics approval and parental consent statement.

### Still outstanding

The landing page is not a substitute for a file-level audit. Before using it quantitatively, inspect the downloaded files and verify:
- patient/infant identifier and one-to-many mapping between images, anatomical sites and reference measurements;
- which column is TSB (the intended reference target) versus TcB (a device measurement, not the same reference);
- units, missing values, repeated measurements, image integrity, duplicates and image-to-lab timing;
- whether every row has a trustworthy patient ID suitable for patient-level splits;
- whether the downloaded package includes all documentation needed to interpret the data.

**Interim status:** plausible bilirubin research candidate with a source-declared CC BY 4.0 license and TSB linkage described; not yet certified quantitative-ready because the actual package has not been audited.

## 4. Cross-dataset policy

1. Hb and bilirubin remain separate experiments and model branches.
2. Never mix datasets silently or treat different reference methods as interchangeable.
3. A source landing page or paper is evidence of documented claims, not proof that every local file is correct.
4. Keep raw clinical datasets out of public GitHub unless their terms explicitly allow it.
5. Preserve patient grouping and source provenance; do not count multiple images of the same patient as independent patients.
6. No performance claims follow from this source audit.
