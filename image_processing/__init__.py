"""Image recognition pipeline for nonogram screenshots."""

from image_processing.image_loader import ParsedNonogramPuzzle, load_puzzle_from_image

__all__ = ["ParsedNonogramPuzzle", "load_puzzle_from_image"]
