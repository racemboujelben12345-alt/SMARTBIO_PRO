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
