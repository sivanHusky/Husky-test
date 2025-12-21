"""Grid detection utilities for Nonogram screenshots."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Tuple


@dataclass
class GridDetectionResult:
    warped: Any
    size: int
    grid_bbox: Tuple[int, int, int, int]
    vertical_lines: List[int]
    horizontal_lines: List[int]


def _require_cv2_and_numpy():
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "OpenCV and NumPy are required for grid detection. Install opencv-python."
        ) from exc
    return cv2, np


def _cluster_positions(values, threshold: int = 3) -> List[int]:
    if values.size == 0:
        return []
    groups: List[List[int]] = [[int(values[0])]]
    for val in values[1:]:
        ival = int(val)
        if abs(ival - groups[-1][-1]) <= threshold:
            groups[-1].append(ival)
        else:
            groups.append([ival])
    return [int(sum(group) / len(group)) for group in groups]


def _extract_line_positions(np, binary, axis: int) -> List[int]:
    projection = np.sum(binary > 0, axis=axis)
    dynamic_threshold = max(5, int(0.3 * projection.max()))
    candidates = np.where(projection >= dynamic_threshold)[0]
    return _cluster_positions(candidates)


def _infer_size(vertical: List[int], horizontal: List[int]) -> int:
    candidates = [5, 10, 15]
    v = max(1, len(vertical) - 1)
    h = max(1, len(horizontal) - 1)
    raw = int(round((v + h) / 2))
    return min(candidates, key=lambda x: abs(x - raw))


def detect_grid(image_bgr) -> GridDetectionResult:
    cv2, np = _require_cv2_and_numpy()

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    bw = cv2.adaptiveThreshold(
        blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        21,
        5,
    )

    contours, _ = cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise ValueError("No contours found; cannot detect nonogram grid")

    grid_contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(grid_contour)
    grid_roi = bw[y : y + h, x : x + w]

    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(10, h // 40)))
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(10, w // 40), 1))

    vertical = cv2.morphologyEx(grid_roi, cv2.MORPH_OPEN, vertical_kernel)
    horizontal = cv2.morphologyEx(grid_roi, cv2.MORPH_OPEN, horizontal_kernel)

    vertical_lines = _extract_line_positions(np, vertical, axis=0)
    horizontal_lines = _extract_line_positions(np, horizontal, axis=1)

    if len(vertical_lines) < 2 or len(horizontal_lines) < 2:
        raise ValueError("Detected grid does not contain enough line separators")

    size = _infer_size(vertical_lines, horizontal_lines)

    return GridDetectionResult(
        warped=grid_roi,
        size=size,
        grid_bbox=(x, y, w, h),
        vertical_lines=vertical_lines,
        horizontal_lines=horizontal_lines,
    )
