from dataclasses import dataclass
from typing import Optional

CANONICAL_COLUMNS = [
    "patient_id","image_id","image_path","source_dataset","biomarker",
    "target_value","target_unit","target_source","reference_method",
    "reference_measurement_id","reference_type","target_time_delta_min",
    "roi_type","device_model","illumination","acquisition_id",
    "exposure_us","iso","white_balance_mode","working_distance_mm",
    "incidence_angle_deg","image_format","bit_depth","raw_available",
]

@dataclass(frozen=True)
class ColumnMapping:
    patient_id: str
    image_path: str
    target_value: str
    image_id: Optional[str] = None
    target_source: Optional[str] = None
    reference_method: Optional[str] = None
    reference_measurement_id: Optional[str] = None
    reference_type: Optional[str] = None
    target_time_delta_min: Optional[str] = None
    roi_type: Optional[str] = None
    device_model: Optional[str] = None
    illumination: Optional[str] = None
    acquisition_id: Optional[str] = None
    roi_x0: Optional[str] = None
    roi_y0: Optional[str] = None
    roi_x1: Optional[str] = None
    exposure_us: Optional[str] = None
    iso: Optional[str] = None
    white_balance_mode: Optional[str] = None
    working_distance_mm: Optional[str] = None
    incidence_angle_deg: Optional[str] = None
    image_format: Optional[str] = None
    bit_depth: Optional[str] = None
    raw_available: Optional[str] = None
    roi_y1: Optional[str] = None
