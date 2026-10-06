"""Conservative optical preprocessing for smartphone acquisitions."""
import numpy as np


def validate_pair_metadata(flash_meta, ambient_meta, required=("device_model", "exposure_us", "iso")):
    # Accept legacy `exposure` as an input alias, but normalize to exposure_us.
    fm = dict(flash_meta)
    am = dict(ambient_meta)
    for d in (fm, am):
        if "exposure_us" not in d and "exposure" in d:
            d["exposure_us"] = d["exposure"]
    missing = [k for k in required if k not in fm or k not in am]
    if missing:
        raise ValueError(f"Cannot compare flash/no-flash: missing metadata {missing}.")
    for key in required:
        if str(fm[key]) != str(am[key]):
            raise ValueError(f"Flash/no-flash mismatch for '{key}'; subtraction is not physically comparable.")
    if str(fm.get("white_balance_mode", "")).lower() in {"auto", "awb"}:
        raise ValueError("Auto white balance is not physically stable for quantitative subtraction.")
    # White balance and geometry can materially change RGB response; if supplied, require equality.
    for key in ("white_balance", "white_balance_mode", "focus_distance", "distance_mm", "roi_geometry", "incidence_angle_deg"):
        if key in fm or key in am:
            if key not in fm or key not in am or str(fm[key]) != str(am[key]):
                raise ValueError(f"Flash/no-flash mismatch for '{key}'.")


def saturation_mask(rgb, low=1, high=254):
    x = np.asarray(rgb)
    if x.ndim != 3 or x.shape[-1] != 3:
        raise ValueError("Expected an RGB image with shape HxWx3.")
    if not (0 <= low < high <= 255):
        raise ValueError("Invalid saturation thresholds.")
    return np.any((x <= low) | (x >= high), axis=-1)


def normalize_rgb(rgb, eps=1e-8):
    # Normalize linearized channel energy, not gamma-encoded RGB codes.
    from .biophysics import srgb_to_linear
    x = srgb_to_linear(np.asarray(rgb, dtype=np.float32)).astype(np.float32)
    if x.ndim != 3 or x.shape[-1] != 3:
        raise ValueError("Expected an RGB image with shape HxWx3.")
    total = x.sum(axis=-1, keepdims=True)
    return x / np.maximum(total, eps)


def flash_minus_ambient(flash, ambient, *, metadata=None, alpha=1.0):
    f = np.asarray(flash, dtype=np.float32)
    a = np.asarray(ambient, dtype=np.float32)
    if f.shape != a.shape:
        raise ValueError("flash and ambient arrays must have identical shapes.")
    if metadata is not None:
        if "flash" not in metadata or "ambient" not in metadata:
            raise ValueError("metadata must contain 'flash' and 'ambient'.")
        validate_pair_metadata(metadata["flash"], metadata["ambient"])
    # A scalar subtraction is only a default approximation. In quantitative
    # work, alpha must be experimentally calibrated per channel.
    if np.isscalar(alpha):
        gains = np.full(3, float(alpha), dtype=np.float32)
    else:
        gains = np.asarray(alpha, dtype=np.float32)
    if gains.shape != (3,) or np.any(~np.isfinite(gains)) or np.any(gains < 0):
        raise ValueError("alpha must be three finite non-negative channel gains.")
    corrected = f - a * gains.reshape((1,) * (f.ndim - 1) + (3,))
    return corrected
