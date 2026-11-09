import pandas as pd
import pytest

from smartbio.ingestion import ingest_sewa_local, load_metadata_table


def test_load_csv_and_ingest(tmp_path):
    raw = pd.DataFrame(
        [{
            "patient_uuid": "p1",
            "cbc_hgb_g_dl": 9.4,
            "image_conjunctiva": "p1/conj.jpg",
            "camera_meta_conjunctiva": '{"android.sensor.exposureTime": 8000000}',
        }]
    )
    source = tmp_path / "sewa.csv"
    raw.to_csv(source, index=False)

    loaded = load_metadata_table(source)
    assert list(loaded.columns) == list(raw.columns)

    output = tmp_path / "canonical.csv"
    result = ingest_sewa_local(source, output_path=output)

    assert output.exists()
    assert len(result) == 1
    assert result.loc[0, "patient_id"] == "p1"
    assert result.loc[0, "target_unit"] == "g/dL"
    assert result.loc[0, "exposure_us"] == 8000.0


def test_missing_local_file_fails_closed(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_metadata_table(tmp_path / "missing.parquet")


def test_unsupported_format_fails_closed(tmp_path):
    path = tmp_path / "metadata.txt"
    path.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported metadata format"):
        load_metadata_table(path)
def test_neojaundice_ingestion_preserves_patient_ids(tmp_path):
    from smartbio.ingestion import ingest_neojaundice_local

    images_dir = tmp_path / "images"
    images_dir.mkdir()

    for name in ["0003-1.jpg", "0003-2.jpg"]:
        (images_dir / name).touch()

    source = tmp_path / "neojaundice.csv"
    pd.DataFrame([
        {
            "patient_id": "0003",
            "image_idx": "0003-1.jpg",
            "blood(mg/dL)": 12.2,
            "Treatment": 0,
        },
        {
            "patient_id": "0003",
            "image_idx": "0003-2.jpg",
            "blood(mg/dL)": 12.2,
            "Treatment": 0,
        },
    ]).to_csv(source, index=False)

    output = tmp_path / "processed" / "canonical.csv"

    result = ingest_neojaundice_local(
        source,
        images_dir=images_dir,
        output_path=output,
    )

    assert len(result) == 2
    assert result["patient_id"].eq("0003").all()
    assert result["biomarker"].eq("bilirubin").all()
    assert result["target_value"].eq(12.2).all()
    assert "Treatment" not in result.columns
    assert result["reference_type"].isna().all()
    assert output.exists()
