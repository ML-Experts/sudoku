import unittest

from fastapi.testclient import TestClient

from api.dependencies import (
    get_extract_cells_command_handler,
    get_preprocess_board_command_handler,
)
from api.main import create_app
from application.features.preprocessing.commands.extract_cells.extract_cells_command_handler import (
    ExtractCellsCommandError,
)
from application.features.preprocessing.commands.extract_cells.extract_cells_command_result_dto import (
    ExtractCellsCommandResultDto,
    ExtractedCellImageDto,
)
from application.features.preprocessing.commands.preprocess_board.preprocess_board_command_handler import (
    PreprocessBoardCommandError,
)
from application.features.preprocessing.commands.preprocess_board.preprocess_board_command_result_dto import (
    PreprocessBoardCommandResultDto,
)


class StubSuccessPreprocessBoardCommandHandler:
    def handle(self, _command: object) -> PreprocessBoardCommandResultDto:
        return PreprocessBoardCommandResultDto(
            mime_type="image/png",
            base64="c3VjY2Vzcw==",
        )


class StubErrorPreprocessBoardCommandHandler:
    def handle(self, _command: object) -> PreprocessBoardCommandResultDto:
        raise PreprocessBoardCommandError(
            error_type="board_not_found",
            message="Nie udało się wykryć krawędzi planszy Sudoku.",
        )


class StubSuccessExtractCellsCommandHandler:
    def handle(self, _command: object) -> ExtractCellsCommandResultDto:
        return ExtractCellsCommandResultDto(
            cells=tuple(
                tuple(
                    ExtractedCellImageDto(
                        mime_type="image/png",
                        base64=f"cell-{row_index}-{col_index}",
                    )
                    for col_index in range(9)
                )
                for row_index in range(9)
            )
        )


class StubErrorExtractCellsCommandHandler:
    def handle(self, _command: object) -> ExtractCellsCommandResultDto:
        raise ExtractCellsCommandError(
            error_type="cells_extraction_failed",
            message="Nie udało się poprawnie podzielić planszy na siatkę 9x9.",
        )


class PreprocessingControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app()
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()

    def test_put_preprocess_board_should_return_image_api_response(self) -> None:
        self.app.dependency_overrides[get_preprocess_board_command_handler] = (
            lambda: StubSuccessPreprocessBoardCommandHandler()
        )
        payload = {
            "mimeType": "image/jpeg",
            "base64": "aW5wdXQ=",
        }

        response = self.client.put("/ml/preprocess/board", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "mimeType": "image/png",
                "base64": "c3VjY2Vzcw==",
            },
        )

    def test_put_preprocess_board_should_map_handler_error_to_422(self) -> None:
        self.app.dependency_overrides[get_preprocess_board_command_handler] = (
            lambda: StubErrorPreprocessBoardCommandHandler()
        )
        payload = {
            "mimeType": "image/jpeg",
            "base64": "aW5wdXQ=",
        }

        response = self.client.put("/ml/preprocess/board", json=payload)

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json(),
            {
                "errorType": "board_not_found",
                "message": "Nie udało się wykryć krawędzi planszy Sudoku.",
            },
        )

    def test_put_preprocess_cells_should_return_cells_grid_api_response(
        self,
    ) -> None:
        self.app.dependency_overrides[get_extract_cells_command_handler] = (
            lambda: StubSuccessExtractCellsCommandHandler()
        )
        payload = {
            "mimeType": "image/png",
            "base64": "aW5wdXQ=",
        }

        response = self.client.put("/ml/preprocess/cells", json=payload)

        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertIn("cells", response_json)
        self.assertEqual(len(response_json["cells"]), 9)
        self.assertTrue(all(len(row) == 9 for row in response_json["cells"]))
        self.assertEqual(
            response_json["cells"][0][0],
            {"mimeType": "image/png", "base64": "cell-0-0"},
        )

    def test_put_preprocess_cells_should_map_handler_error_to_422(
        self,
    ) -> None:
        self.app.dependency_overrides[get_extract_cells_command_handler] = (
            lambda: StubErrorExtractCellsCommandHandler()
        )
        payload = {
            "mimeType": "image/png",
            "base64": "aW5wdXQ=",
        }

        response = self.client.put("/ml/preprocess/cells", json=payload)

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json(),
            {
                "errorType": "cells_extraction_failed",
                "message": (
                    "Nie udało się poprawnie podzielić planszy na siatkę 9x9."
                ),
            },
        )


if __name__ == "__main__":
    unittest.main()
