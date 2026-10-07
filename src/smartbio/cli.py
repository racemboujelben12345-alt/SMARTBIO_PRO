import argparse
import json
from pathlib import Path
import pandas as pd
import yaml

from .schema import ColumnMapping
from .schema_discovery import print_schema_report
from .canonical import build_canonical
from .audit import (
    inventory, exact_duplicate_groups, quality_audit,
    missingness, target_summary, audit_gate
)
from .splits import patient_split, assert_no_patient_overlap
from .features import extract_dataset
from .validator import validate_canonical
from .acquisition import REQUIRED_QUANTITATIVE_FIELDS
from .biophysics import validate_physical_capture
from .quality import QualityGateConfig, assess_paths
from .ingestion import ingest_sewa_local, load_metadata_table
from .sewa_preflight import preflight_sewa
from .fingertip_preflight import preflight_fingertip
from .fingertip_video_validation import validate_fingertip_videos
from .experimental_intake import audit_experimental_intake
from .optical_pipeline import OpticalPreprocessConfig, preprocess_roi
from .features import roi_from_metadata
from .roi import validate_roi_type

def mapping_from_yaml(path):
    cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    c = cfg["columns"]
    required = ["patient_id","image_path","target_value"]
    if any(not c.get(k) or str(c[k]).startswith("YOUR_") for k in required):
        raise ValueError("Explicit mapping is incomplete.")
    return ColumnMapping(**c)

def main():
    parser = argparse.ArgumentParser(prog="smartbio")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("discover")
    p.add_argument("--metadata", required=True)

    p = sub.add_parser("canonicalize")
    p.add_argument("--metadata", required=True)
    p.add_argument("--mapping", required=True)
    p.add_argument("--dataset", required=True)
    p.add_argument("--biomarker", required=True, choices=["hemoglobin","bilirubin"])
    p.add_argument("--unit", required=True)
    p.add_argument("--output", required=True)

    p = sub.add_parser("audit")
    p.add_argument("--metadata", required=True)
    p.add_argument("--output", required=True)

    p = sub.add_parser("split")
    p.add_argument("--metadata", required=True)
    p.add_argument("--output", required=True)

    p = sub.add_parser("features")
    p.add_argument("--metadata", required=True)
    p.add_argument("--output", required=True)

    p = sub.add_parser("physics-audit")
    p.add_argument("--metadata", required=True)
    p.add_argument("--output", required=True)

    p = sub.add_parser("sewa-preflight")
    p.add_argument("--metadata", required=True)
    p.add_argument("--output", required=True)

    p = sub.add_parser("fingertip-preflight")
    p.add_argument("--manifest", required=True)
    p.add_argument("--output", required=True)

    p = sub.add_parser("fingertip-video-validate")
    p.add_argument("--manifest", required=True)
    p.add_argument("--video-root", default=None)
    p.add_argument("--output", required=True)

    p = sub.add_parser("ingest-sewa")
    p.add_argument("--metadata", required=True)
    p.add_argument("--output", required=True)

    p = sub.add_parser("experimental-intake")
    p.add_argument("--manifest", required=True)
    p.add_argument("--data-root", default=None)
    p.add_argument("--output", required=True)
    p.add_argument("--biomarker", required=True, choices=["hemoglobin","bilirubin"])
    p.add_argument("--unit", required=True)

    p = sub.add_parser("optical-audit")
    p.add_argument("--metadata", required=True)
    p.add_argument("--data-root", default=None)
    p.add_argument("--output", required=True)
    p.add_argument("--min-valid-fraction", type=float, default=0.80)

    p = sub.add_parser("quality")
    p.add_argument("--images", required=True)
    p.add_argument("--config", required=True)
    p.add_argument("--output", required=True)

    args = parser.parse_args()

    if args.cmd == "discover":
        print_schema_report(pd.read_csv(args.metadata))

    elif args.cmd == "canonicalize":
        raw = pd.read_csv(args.metadata)
        result = build_canonical(
            raw, mapping_from_yaml(args.mapping),
            args.dataset, args.biomarker, args.unit
        )
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(args.output, index=False)

    elif args.cmd == "audit":
        out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
        df = pd.read_csv(args.metadata)
        validation = validate_canonical(df)
        if not validation["valid"]:
            (out / "schema_validation.json").write_text(
                json.dumps(validation, indent=2), encoding="utf-8"
            )
            raise SystemExit("SCHEMA VALIDATION FAILED: " + "; ".join(validation["errors"]))
        inv = inventory(df)
        dups = exact_duplicate_groups(inv)
        qual = quality_audit(inv)

        inv.to_csv(out/"inventory.csv", index=False)
        dups.to_csv(out/"exact_duplicates.csv", index=False)
        qual.to_csv(out/"quality.csv", index=False)
        missingness(df).to_csv(out/"missingness.csv", index=False)
        target_summary(df).to_csv(out/"target_summary.csv", index=False)

        split_report = None
        split_error = None
        try:
            split_parts = []
            for _, part in df.groupby("biomarker"):
                tr, va, te = patient_split(part)
                assert_no_patient_overlap(tr, va, te)
                split_parts.extend([tr, va, te])
            split_report = {"passed": True, "note": "patient-level split verified per biomarker"}
        except Exception as exc:
            split_error = str(exc)
            split_report = {"passed": False, "error": split_error}

        checks, passed = audit_gate(inv, qual, dups, split_report=split_report)
        report = {
            "records": int(len(df)),
            "patients": int(df["patient_id"].nunique()),
            "biomarkers": sorted(df["biomarker"].dropna().unique().tolist()),
            "checks": checks,
            "ready_for_ml": bool(passed),
        }
        (out/"FINAL_DATA_AUDIT.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        print(json.dumps(report, indent=2))
        if not passed:
            raise SystemExit("AUDIT FAILED: dataset is not READY_FOR_ML.")

    elif args.cmd == "split":
        df = pd.read_csv(args.metadata)
        base = Path(args.output)
        base.parent.mkdir(parents=True, exist_ok=True)
        for biomarker, part in df.groupby("biomarker"):
            tr, va, te = patient_split(part)
            assert_no_patient_overlap(tr, va, te)
            tr.to_csv(f"{args.output}_{biomarker}_train.csv", index=False)
            va.to_csv(f"{args.output}_{biomarker}_validation.csv", index=False)
            te.to_csv(f"{args.output}_{biomarker}_test.csv", index=False)

    elif args.cmd == "features":
        extract_dataset(args.metadata, args.output)

    elif args.cmd == "sewa-preflight":
        report = preflight_sewa(load_metadata_table(args.metadata))
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
        print(json.dumps(report.to_dict(), indent=2))
        if not report.passed:
            raise SystemExit("SEWA PREFLIGHT NOT READY: downstream quantitative gates remain closed.")

    elif args.cmd == "fingertip-preflight":
        report = preflight_fingertip(load_metadata_table(args.manifest))
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
        print(json.dumps(report.to_dict(), indent=2))
        if not report.passed:
            raise SystemExit("FINGERTIP PREFLIGHT NOT READY: downstream quantitative gates remain closed.")

    elif args.cmd == "fingertip-video-validate":
        manifest = load_metadata_table(args.manifest)
        report = validate_fingertip_videos(manifest, video_root=args.video_root)
        out = Path(args.output)
        out.mkdir(parents=True, exist_ok=True)
        (out / "validation.json").write_text(
            json.dumps(report.to_dict(), indent=2), encoding="utf-8"
        )
        pd.DataFrame(
            [record.to_dict() for record in report.records]
        ).to_json(out / "records.json", orient="records", indent=2)
        print(json.dumps({
            "rows": report.rows,
            "patients": report.unique_patients,
            "files_found": report.files_found,
            "files_missing": report.files_missing,
            "readable_videos": report.readable_videos,
            "unreadable_videos": report.unreadable_videos,
            "duplicate_files": report.duplicate_files,
            "passed": report.passed,
        }, indent=2))
        if not report.passed:
            raise SystemExit(
                "FINGERTIP VIDEO VALIDATION FAILED: assets are not ready for downstream analysis."
            )

    elif args.cmd == "ingest-sewa":
        result = ingest_sewa_local(args.metadata, output_path=args.output)
        print(json.dumps({
            "records": int(len(result)),
            "patients": int(result["patient_id"].nunique()),
            "output": str(args.output),
            "quantitative_ready": False,
            "note": "Ingestion only; acquisition/provenance gates still required."
        }, indent=2))

    elif args.cmd == "experimental-intake":
        manifest = load_metadata_table(args.manifest)
        report = audit_experimental_intake(
            manifest,
            data_root=args.data_root,
            require_assets=True,
            expected_biomarker=args.biomarker,
            expected_unit=args.unit,
        )
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps({
            "passed": report["passed"],
            "rows": report["n_rows"],
            "patients": report["n_unique_patients"],
            "unique_assets": report["n_unique_assets"],
            "errors": len(report["errors"]),
        }, indent=2))
        if not report["passed"]:
            raise SystemExit("EXPERIMENTAL INTAKE FAILED: quantitative analysis remains closed.")

    elif args.cmd == "optical-audit":
        df = pd.read_csv(args.metadata)
        required = {"image_path", "biomarker", "roi_type", "roi_x0", "roi_y0", "roi_x1", "roi_y1"}
        missing = required - set(df.columns)
        if missing:
            raise SystemExit(f"OPTICAL AUDIT FAILED: missing columns {sorted(missing)}")

        data_root = Path(args.data_root) if args.data_root else None
        records = []
        for idx, row in df.iterrows():
            record = {
                "row": int(idx),
                "image_id": row.get("image_id"),
                "patient_id": row.get("patient_id"),
                "biomarker": row.get("biomarker"),
                "roi_type": row.get("roi_type"),
            }
            try:
                biomarker = str(row["biomarker"]).strip().lower()
                roi_type = str(row["roi_type"]).strip().lower()
                validate_roi_type(biomarker, roi_type)
                path = Path(str(row["image_path"]))
                if data_root is not None and not path.is_absolute():
                    path = data_root / path
                from .features import load_rgb
                image = load_rgb(path)
                roi = roi_from_metadata(image, row)
                result = preprocess_roi(
                    roi,
                    config=OpticalPreprocessConfig(
                        min_valid_fraction=args.min_valid_fraction
                    ),
                )
                record.update(result.summary())
                record["image_path"] = str(path)
                record["passed"] = result.quality_status == "PASS"
            except Exception as exc:
                record.update({
                    "quality_status": "ERROR",
                    "passed": False,
                    "error": str(exc),
                })
            records.append(record)

        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        result_df = pd.DataFrame(records)
        result_df.to_csv(out, index=False)
        summary = {
            "records": int(len(result_df)),
            "passed": int(result_df["passed"].sum()) if len(result_df) else 0,
            "failed": int((~result_df["passed"]).sum()) if len(result_df) else 0,
            "output": str(out),
            "raw_images_modified": False,
            "scientific_status": "engineering_optical_audit_only",
        }
        print(json.dumps(summary, indent=2))
        if summary["failed"]:
            raise SystemExit("OPTICAL AUDIT FAILED: quantitative optical preprocessing remains closed.")

    elif args.cmd == "quality":
        image_root = Path(args.images)
        config_path = Path(args.config)
        out = Path(args.output)
        out.mkdir(parents=True, exist_ok=True)

        if not image_root.exists():
            raise SystemExit(f"IMAGE ROOT NOT FOUND: {image_root}")
        if not config_path.exists():
            raise SystemExit(f"QUALITY CONFIG NOT FOUND: {config_path}")

        cfg = yaml.safe_load(
            config_path.read_text(encoding="utf-8")
        ) or {}

        config = QualityGateConfig(**cfg)

        paths = sorted(
            p for p in image_root.rglob("*")
            if p.is_file()
            and p.suffix.lower() in {
                ".jpg", ".jpeg", ".png",
                ".bmp", ".tif", ".tiff"
            }
        )

        if not paths:
            raise SystemExit(f"NO IMAGES FOUND: {image_root}")

        results = assess_paths(paths, config)
        results.to_csv(out / "quality.csv", index=False)

        status_counts = (
            results["quality_status"]
            .value_counts()
            .reindex(["PASS", "REVIEW", "FAIL"], fill_value=0)
            .astype(int)
            .to_dict()
        )

        summary = {
            "images_root": str(image_root),
            "config": str(config_path),
            "records": int(len(results)),
            "quality_status_counts": status_counts,
            "pass_rate": float(
                (results["quality_status"] == "PASS").mean()
            ),
            "review_rate": float(
                (results["quality_status"] == "REVIEW").mean()
            ),
            "fail_rate": float(
                (results["quality_status"] == "FAIL").mean()
            ),
            "raw_images_modified": False,
            "scientific_status": "engineering_audit_only",
            "note": (
                "Thresholds are engineering starting points, "
                "not clinical thresholds."
            ),
        }

        (out / "summary.json").write_text(
            json.dumps(summary, indent=2),
            encoding="utf-8"
        )

        print(json.dumps(summary, indent=2))

    elif args.cmd == "physics-audit":
        df = pd.read_csv(args.metadata)
        records = []
        for _, row in df.iterrows():
            r = row.to_dict()
            meta = {k: r.get(k) for k in (
                "image_format", "bit_depth", "exposure_us", "iso",
                "white_balance_mode", "raw_available",
                "working_distance_mm", "incidence_angle_deg"
            )}
            records.append({
                "image_id": r.get("image_id"),
                "patient_id": r.get("patient_id"),
                "biomarker": r.get("biomarker"),
                **validate_physical_capture(meta),
            })
        report = {
            "records": len(records),
            "valid_records": sum(x["valid"] for x in records),
            "invalid_records": sum(not x["valid"] for x in records),
            "principle": "RGB/JPEG is not treated as calibrated spectroscopy; tissue scattering/pathlength and camera state are explicit confounders.",
            "records_detail": records,
        }
        out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        print(json.dumps({k: report[k] for k in ("records", "valid_records", "invalid_records")}, indent=2))

if __name__ == "__main__":
    main()
