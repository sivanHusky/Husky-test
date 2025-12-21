"""Detect per-cell state from extracted grid image."""

from __future__ import annotations

from typing import List

Cell = int


def _require_cv2_and_numpy():
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "OpenCV and NumPy are required for cell-state detection. Install opencv-python."
        ) from exc
    return cv2, np


def _detect_x_mark(cell_gray) -> bool:
    cv2, np = _require_cv2_and_numpy()
    edges = cv2.Canny(cell_gray, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=8, minLineLength=6, maxLineGap=2)
    if lines is None:
        return False

    pos_diag = 0
    neg_diag = 0
    for line in lines:
        x1, y1, x2, y2 = line[0]
        dx = x2 - x1
        dy = y2 - y1
        if abs(dx) < 2:
            continue
        slope = dy / dx
        if 0.4 <= slope <= 2.5:
            pos_diag += 1
        elif -2.5 <= slope <= -0.4:
            neg_diag += 1

    return pos_diag > 0 and neg_diag > 0


def detect_cell_states(grid_gray, size: int) -> List[List[Cell]]:
    """Split grid to NxN and classify into {-1, 0, 1}."""
    _, np = _require_cv2_and_numpy()

    h, w = grid_gray.shape
    cell_h = h / size
    cell_w = w / size

    result: List[List[Cell]] = []
    for r in range(size):
        row: List[Cell] = []
        for c in range(size):
            y0 = int(r * cell_h)
            y1 = int((r + 1) * cell_h)
            x0 = int(c * cell_w)
            x1 = int((c + 1) * cell_w)

            cell = grid_gray[y0:y1, x0:x1]
            if cell.size == 0:
                row.append(0)
                continue

            margin_y = max(1, (y1 - y0) // 6)
            margin_x = max(1, (x1 - x0) // 6)
            inner = cell[margin_y:-margin_y or None, margin_x:-margin_x or None]
            if inner.size == 0:
                inner = cell

            black_ratio = float(np.mean(inner < 80))
            if black_ratio > 0.5:
                row.append(1)
            elif _detect_x_mark(inner):
                row.append(-1)
            else:
                row.append(0)
        result.append(row)

    return result
