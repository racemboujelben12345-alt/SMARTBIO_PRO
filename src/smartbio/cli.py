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
