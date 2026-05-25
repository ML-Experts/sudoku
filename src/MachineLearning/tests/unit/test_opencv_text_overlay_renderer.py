import unittest

import cv2
import numpy as np

from infrastructure.vision.opencv_text_overlay_renderer import (
    OpenCvTextOverlayRenderer,
)


class OpenCvTextOverlayRendererTests(unittest.TestCase):
    def setUp(self) -> None:
        self._renderer = OpenCvTextOverlayRenderer()

    def test_render_centered_text_should_render_on_grayscale_canvas(self) -> None:
        canvas = np.full((48, 48), 255, dtype=np.uint8)

        result = self._renderer.render_centered_text(canvas, "8")

        self.assertEqual(result.shape, canvas.shape)
        self.assertFalse(np.array_equal(result, canvas))

    def test_render_centered_text_should_render_on_color_canvas(self) -> None:
        canvas = np.full((48, 48, 3), (10, 20, 30), dtype=np.uint8)

        result = self._renderer.render_centered_text(canvas, "5")

        self.assertEqual(result.shape, canvas.shape)
        self.assertFalse(np.array_equal(result, canvas))
        changed_pixels = result[np.any(result != canvas, axis=2)]
        self.assertGreater(len(changed_pixels), 0)
        self.assertTrue(
            np.any(np.max(changed_pixels, axis=1) > 180)
        )
        self.assertTrue(
            np.any(np.min(changed_pixels, axis=1) < 15)
        )
        self.assertTrue(
            np.any(
                (np.max(changed_pixels, axis=1) < 255)
                & (np.min(changed_pixels, axis=1) > 0)
            )
        )

    def test_calculate_layout_should_fit_text_within_seventy_percent_height(
        self,
    ) -> None:
        layout = self._renderer._calculate_layout("8", 100, 100)
        text_size, _ = cv2.getTextSize(
            "8",
            self._renderer._FONT_FACE,
            layout.font_scale,
            layout.thickness,
        )

        self.assertLessEqual(text_size[1], 70)
        self.assertLessEqual(text_size[0], 70)

    def test_select_overlay_colors_should_boost_inverted_color_when_needed(
        self,
    ) -> None:
        canvas = np.full((48, 48, 3), (128, 128, 128), dtype=np.uint8)

        text_color, outline_color = self._renderer._select_overlay_colors(canvas)
        preferred_inverted = (127, 127, 127)
        background_color = (128, 128, 128)

        self.assertNotEqual(text_color, preferred_inverted)
        self.assertGreaterEqual(
            self._renderer._contrast_ratio(background_color, text_color),
            self._renderer._MIN_CONTRAST_RATIO,
        )
        self.assertIn(
            outline_color,
            (
                self._renderer._LIGHT_TEXT_COLOR,
                self._renderer._DARK_TEXT_COLOR,
            ),
        )

    def test_render_centered_text_should_not_modify_input_in_place(self) -> None:
        canvas = np.full((48, 48, 3), 255, dtype=np.uint8)
        original = canvas.copy()

        _ = self._renderer.render_centered_text(canvas, "3")

        self.assertTrue(np.array_equal(canvas, original))

    def test_render_centered_text_should_keep_drawn_pixels_inside_canvas(
        self,
    ) -> None:
        canvas = np.full((64, 64, 3), 255, dtype=np.uint8)

        result = self._renderer.render_centered_text(canvas, "9")

        changed_pixels = np.argwhere(np.any(result != 255, axis=2))
        self.assertGreater(len(changed_pixels), 0)
        self.assertGreater(int(changed_pixels[:, 0].min()), 0)
        self.assertGreater(int(changed_pixels[:, 1].min()), 0)
        self.assertLess(int(changed_pixels[:, 0].max()), 63)
        self.assertLess(int(changed_pixels[:, 1].max()), 63)


if __name__ == "__main__":
    unittest.main()
