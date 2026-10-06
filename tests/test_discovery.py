import pandas as pd
from smartbio.schema_discovery import find_candidates

def test_discovery_does_not_modify_dataframe():
    df = pd.DataFrame({"participant_id":["p1"], "Hb":[12], "image_path":["x.jpg"]})
    before = list(df.columns)
    result = find_candidates(df)
    assert list(df.columns) == before
    assert result["patient_id"] == ["participant_id"]
    assert result["target_value"] == ["Hb"]
