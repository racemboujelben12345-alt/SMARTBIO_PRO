import pandas as pd
import pytest
from smartbio.canonical import build_canonical
from smartbio.schema import ColumnMapping

def raw():
    return pd.DataFrame({
        "pid":["p1","p2"],"path":["a.jpg","b.jpg"],"hb":[11.,12.],
        "source":["lab","lab"],"method":["CBC","CBC"],"rid":["r1","r2"],
        "rtype":["laboratory","laboratory"],"device":["D1","D1"],
        "exp":[10000.,10000.],"iso":[100.,100.],"wb":["locked","locked"],
        "dist":[50.,50.],"angle":[0.,0.],"illum":["flash","flash"],
    })

def mapping():
    return ColumnMapping("pid","path","hb",target_source="source",
        reference_method="method",reference_measurement_id="rid",
        reference_type="rtype",device_model="device",exposure_us="exp",
        iso="iso",white_balance_mode="wb",working_distance_mm="dist",
        incidence_angle_deg="angle",illumination="illum")

def test_provenance_is_mapped():
    out=build_canonical(raw(),mapping(),"demo","hemoglobin","g/dL",require_target_provenance=True)
    assert out["reference_measurement_id"].tolist()==["r1","r2"]

def test_missing_provenance_fails_strict():
    m=mapping()
    m=ColumnMapping("pid","path","hb",device_model=m.device_model,exposure_us=m.exposure_us,
        iso=m.iso,white_balance_mode=m.white_balance_mode,working_distance_mm=m.working_distance_mm,
        incidence_angle_deg=m.incidence_angle_deg,illumination=m.illumination)
    with pytest.raises(ValueError,match="target provenance"):
        build_canonical(raw(),m,"demo","hemoglobin","g/dL",require_target_provenance=True)


def test_strict_roi_provenance_requires_explicit_geometry():
    m = mapping()
    with pytest.raises(ValueError, match="ROI provenance"):
        build_canonical(raw(), m, "demo", "hemoglobin", "g/dL", require_roi_provenance=True)


def test_strict_roi_provenance_accepts_explicit_geometry():
    frame = raw()
    frame["roi_type"] = ["conjunctiva", "conjunctiva"]
    frame["x0"] = [10, 20]
    frame["y0"] = [10, 20]
    frame["x1"] = [100, 120]
    frame["y1"] = [100, 120]
    frame["w"] = [200, 240]
    frame["h"] = [200, 240]
    m = mapping()
    m = ColumnMapping(**{**m.__dict__, "roi_type":"roi_type", "roi_x0":"x0", "roi_y0":"y0", "roi_x1":"x1", "roi_y1":"y1", "image_width":"w", "image_height":"h"})
    out = build_canonical(frame, m, "demo", "hemoglobin", "g/dL", require_target_provenance=True, require_roi_provenance=True)
    assert out[["roi_x0", "roi_y0", "roi_x1", "roi_y1"]].notna().all().all()
