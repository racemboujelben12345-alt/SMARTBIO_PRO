"""Target-specific ROI contracts for SmartBio.

This module deliberately does not pretend to localize anatomy automatically.
A ROI is either supplied explicitly or produced by a future validated detector.
"""
from dataclasses import dataclass
import numpy as np

TARGET_ROIS = {
    "hemoglobin": {"conjunctiva", "nailbed"},
    "bilirubin": {"forehead", "sternum", "abdomen"},
}

@dataclass(frozen=True)
class ROIBox:
    x0: int
    y0: int
    x1: int
    y1: int

    def validate(self, width: int, height: int) -> None:
        if not (0 <= self.x0 < self.x1 <= width and 0 <= self.y0 < self.y1 <= height):
            raise ValueError("ROI box is outside image bounds or has invalid geometry.")


def validate_roi_type(biomarker: str, roi_type: str) -> None:
    allowed = TARGET_ROIS.get(str(biomarker).lower())
    if allowed is None:
        raise ValueError(f"Unsupported biomarker: {biomarker}")
    if str(roi_type).lower() not in allowed:
        raise ValueError(f"ROI '{roi_type}' is not validated for biomarker '{biomarker}'.")


def crop(image: np.ndarray, box: ROIBox) -> np.ndarray:
    if image.ndim < 2:
        raise ValueError("Image must have at least two dimensions.")
    h, w = image.shape[:2]
    box.validate(w, h)
    return image[box.y0:box.y1, box.x0:box.x1].copy()
