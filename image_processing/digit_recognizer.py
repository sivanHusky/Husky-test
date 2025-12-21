"""Digit recognition for clue strips using pytesseract."""

from __future__ import annotations

from typing import List


def _optional_cv2():
    try:
        import cv2  # type: ignore
    except ImportError:
        return None
    return cv2


def _optional_tesseract():
    try:
        import pytesseract  # type: ignore
    except ImportError:
        return None
    return pytesseract


def _normalize_for_ocr(image_gray):
    cv2 = _optional_cv2()
    if cv2 is None:
        return image_gray
    resized = cv2.resize(image_gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    _, thresh = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh


def recognize_clue_numbers(image_gray) -> List[int]:
    """Recognize multi-number clue text from grayscale snippet."""
    pytesseract = _optional_tesseract()
    if pytesseract is None:
        return []

    processed = _normalize_for_ocr(image_gray)
    config = "--psm 7 -c tessedit_char_whitelist=0123456789 "
    text = pytesseract.image_to_string(processed, config=config)
    tokens = [token for token in text.replace("\n", " ").split(" ") if token.strip()]

    clues: List[int] = []
    for token in tokens:
        if token.isdigit():
            value = int(token)
            if value > 0:
                clues.append(value)
    return clues
