import unittest

from image_processing.image_loader import load_puzzle_from_image
from overlay.overlay_renderer import render_overlay_on_image


class TestOptionalDependencies(unittest.TestCase):
    def test_image_loader_requires_opencv(self):
        with self.assertRaises(RuntimeError):
            load_puzzle_from_image("dummy.png")

    def test_overlay_renderer_requires_opencv(self):
        with self.assertRaises(RuntimeError):
            render_overlay_on_image("dummy.png", [[1]], (0, 0, 10, 10))


if __name__ == "__main__":
    unittest.main()
