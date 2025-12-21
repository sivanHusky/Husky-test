"""Render solved grid overlay on top of the source screenshot."""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

Cell = int


def _require_cv2():
    try:
        import cv2  # type: ignore
    except ImportError as exc:
        raise RuntimeError("OpenCV is required for overlay rendering. Install opencv-python.") from exc
    return cv2


def _draw_x(cv2, canvas, x0: int, y0: int, x1: int, y1: int) -> None:
    pad_x = max(1, (x1 - x0) // 5)
    pad_y = max(1, (y1 - y0) // 5)
    color = (0, 0, 255)
    thickness = max(1, min(x1 - x0, y1 - y0) // 12)
    cv2.line(canvas, (x0 + pad_x, y0 + pad_y), (x1 - pad_x, y1 - pad_y), color, thickness)
    cv2.line(canvas, (x0 + pad_x, y1 - pad_y), (x1 - pad_x, y0 + pad_y), color, thickness)


def render_overlay_on_image(
    image_path: str,
    grid_solution: List[List[Cell]],
    grid_bbox: Tuple[int, int, int, int],
    alpha: float = 0.8,
):
    """Render solved grid on original screenshot and return composed BGR image."""
    cv2 = _require_cv2()

    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Cannot read image: {image_path}")

    size = len(grid_solution)
    if size == 0 or any(len(row) != size for row in grid_solution):
        raise ValueError("grid_solution must be a non-empty square matrix")

    x, y, w, h = grid_bbox
    overlay = image.copy()
    cell_w = w / size
    cell_h = h / size

    for r in range(size):
        for c in range(size):
            state = grid_solution[r][c]
            x0 = int(x + c * cell_w)
            x1 = int(x + (c + 1) * cell_w)
            y0 = int(y + r * cell_h)
            y1 = int(y + (r + 1) * cell_h)

            if state == 1:
                cv2.rectangle(overlay, (x0, y0), (x1, y1), (0, 0, 0), thickness=-1)
            elif state == -1:
                _draw_x(cv2, overlay, x0, y0, x1, y1)

    composed = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)
    return composed


def export_overlay_png(
    image_path: str,
    grid_solution: List[List[Cell]],
    grid_bbox: Tuple[int, int, int, int],
    output_path: str,
    alpha: float = 0.8,
) -> str:
    """Render and export PNG overlay while preserving original image resolution."""
    cv2 = _require_cv2()

    composed = render_overlay_on_image(image_path, grid_solution, grid_bbox, alpha=alpha)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    ok = cv2.imwrite(str(out), composed)
    if not ok:
        raise ValueError(f"Failed to write overlay image: {output_path}")
    return str(out)
