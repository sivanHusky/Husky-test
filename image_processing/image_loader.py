"""Load and parse nonogram puzzle from screenshot image."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from image_processing.cell_state_detector import detect_cell_states
from image_processing.digit_recognizer import recognize_clue_numbers
from image_processing.grid_detector import detect_grid


def _require_cv2():
    try:
        import cv2  # type: ignore
    except ImportError as exc:
        raise RuntimeError("OpenCV is required for image loading. Install opencv-python.") from exc
    return cv2


@dataclass
class ParsedNonogramPuzzle:
    size: int
    row_clues: List[List[int]]
    col_clues: List[List[int]]
    initial_grid: List[List[int]]
    image_path: str
    grid_bbox: Tuple[int, int, int, int]


def _extract_clues(image_bgr, bbox, size: int) -> tuple[List[List[int]], List[List[int]]]:
    cv2 = _require_cv2()

    x, y, w, h = bbox
    top_h = min(y, max(30, int(h * 0.45)))
    left_w = min(x, max(30, int(w * 0.45)))

    top_region = image_bgr[max(0, y - top_h) : y, x : x + w]
    left_region = image_bgr[y : y + h, max(0, x - left_w) : x]

    row_clues: List[List[int]] = []
    col_clues: List[List[int]] = []

    if left_region.size == 0:
        row_clues = [[] for _ in range(size)]
    else:
        row_h = left_region.shape[0] / size
        for r in range(size):
            y0 = int(r * row_h)
            y1 = int((r + 1) * row_h)
            snippet = left_region[y0:y1, :]
            gray = cv2.cvtColor(snippet, cv2.COLOR_BGR2GRAY)
            row_clues.append(recognize_clue_numbers(gray))

    if top_region.size == 0:
        col_clues = [[] for _ in range(size)]
    else:
        col_w = top_region.shape[1] / size
        for c in range(size):
            x0 = int(c * col_w)
            x1 = int((c + 1) * col_w)
            snippet = top_region[:, x0:x1]
            gray = cv2.cvtColor(snippet, cv2.COLOR_BGR2GRAY)
            col_clues.append(recognize_clue_numbers(gray))

    return row_clues, col_clues


def load_puzzle_from_image(image_path: str) -> ParsedNonogramPuzzle:
    cv2 = _require_cv2()

    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    image_bgr = cv2.imread(str(path))
    if image_bgr is None:
        raise ValueError("Failed to load image; unsupported format or corrupted file")

    detection = detect_grid(image_bgr)
    grid_gray = detection.warped
    if len(grid_gray.shape) == 3:
        grid_gray = cv2.cvtColor(grid_gray, cv2.COLOR_BGR2GRAY)

    initial_grid = detect_cell_states(grid_gray, detection.size)
    row_clues, col_clues = _extract_clues(image_bgr, detection.grid_bbox, detection.size)

    return ParsedNonogramPuzzle(
        size=detection.size,
        row_clues=row_clues,
        col_clues=col_clues,
        initial_grid=initial_grid,
        image_path=str(path),
        grid_bbox=detection.grid_bbox,
    )
