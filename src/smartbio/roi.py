"""Target-specific ROI contracts for SmartBio.

The ROI layer is intentionally deterministic and explicit. It does not claim
clinical anatomical localization. Future automated detectors must be validated
against the same contract before being used for quantitative estimation.
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
        if not (
            0 <= self.x0 < self.x1 <= width
            and 0 <= self.y0 < self.y1 <= height
        ):
            raise ValueError("ROI box is outside image bounds or has invalid geometry.")

    @property
    def width(self) -> int:
        return self.x1 - self.x0

    @property
    def height(self) -> int:
        return self.y1 - self.y0

    @property
    def area(self) -> int:
        return self.width * self.height


def validate_roi_type(biomarker: str, roi_type: str) -> None:
    allowed = TARGET_ROIS.get(str(biomarker).lower())
    if allowed is None:
        raise ValueError(f"Unsupported biomarker: {biomarker}")
    if str(roi_type).lower() not in allowed:
        raise ValueError(f"ROI '{roi_type}' is not validated for biomarker '{biomarker}'.")


def validate_roi_geometry(
    box: ROIBox,
    *,
    image_width: int,
    image_height: int,
    min_width: int = 8,
    min_height: int = 8,
    min_area_fraction: float = 0.01,
    max_area_fraction: float = 0.95,
) -> None:
    """Validate bounds and reject implausibly tiny or dominant ROIs."""
    if min_width < 1 or min_height < 1:
        raise ValueError("Minimum ROI dimensions must be positive.")
    if not (0.0 < min_area_fraction <= max_area_fraction <= 1.0):
        raise ValueError("Invalid ROI area-fraction limits.")
    box.validate(image_width, image_height)

    if box.width < min_width or box.height < min_height:
        raise ValueError("ROI is smaller than the minimum allowed geometry.")

    image_area = image_width * image_height
    fraction = box.area / image_area
    if not min_area_fraction <= fraction <= max_area_fraction:
        raise ValueError("ROI area fraction is outside the allowed range.")


def crop(image: np.ndarray, box: ROIBox) -> np.ndarray:
    if image.ndim < 2:
        raise ValueError("Image must have at least two dimensions.")
    h, w = image.shape[:2]
    box.validate(w, h)
    return image[box.y0:box.y1, box.x0:box.x1].copy()
