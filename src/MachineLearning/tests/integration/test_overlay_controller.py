import base64
import unittest

import cv2
import numpy as np
from fastapi.testclient import TestClient

from api.dependencies import get_render_overlay_cell_command_handler
from api.main import create_app


class _ExplodingHandler:
    def handle(self, command: object) -> object:
        raise RuntimeError("boom")


class OverlayControllerTests(unittest.TestCase):
    def test_post_overlay_cells_should_return_rendered_image(self) -> None:
        client = TestClient(create_app())

        response = client.post(
            "/ml/sudoku/overlay/cells",
            json=self._build_payload(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mimeType"], "image/png")
        self.assertTrue(response.json()["base64"])

    def test_post_overlay_cells_should_return_422_for_invalid_digit(self) -> None:
        client = TestClient(create_app())

        response = client.post(
            "/ml/sudoku/overlay/cells",
            json=self._build_payload(digit=0),
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["errorType"], "invalid_digit")

    def test_post_overlay_cells_should_return_422_for_invalid_image(self) -> None:
        client = TestClient(create_app())

        response = client.post(
            "/ml/sudoku/overlay/cells",
            json=self._build_payload(image_base64="not-valid-base64"),
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["errorType"], "invalid_image_payload")

    def test_post_overlay_cells_should_return_422_for_invalid_position(
        self,
    ) -> None:
        client = TestClient(create_app())

        response = client.post(
            "/ml/sudoku/overlay/cells",
            json=self._build_payload(row_index=10),
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["errorType"], "invalid_cell_position")

    def test_post_overlay_cells_should_return_500_for_unhandled_error(
        self,
    ) -> None:
        app = create_app()
        app.dependency_overrides[get_render_overlay_cell_command_handler] = (
            lambda: _ExplodingHandler()
        )
        client = TestClient(app)

        response = client.post(
            "/ml/sudoku/overlay/cells",
            json=self._build_payload(),
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["errorType"], "internal_server_error")

    def _build_payload(
        self,
        digit: int = 4,
        image_base64: str | None = None,
        row_index: int | None = 0,
        column_index: int | None = 2,
    ) -> dict[str, object]:
        return {
            "cellImage": {
                "mimeType": "image/png",
                "base64": image_base64 or self._encode_png(self._blank_cell()),
            },
            "digit": digit,
            "rowIndex": row_index,
            "columnIndex": column_index,
        }

    def _encode_png(self, image: np.ndarray) -> str:
        success, encoded = cv2.imencode(".png", image)
        self.assertTrue(success)
        return base64.b64encode(encoded.tobytes()).decode("ascii")

    def _blank_cell(self) -> np.ndarray:
        return np.full((32, 32, 3), 255, dtype=np.uint8)


if __name__ == "__main__":
    unittest.main()
