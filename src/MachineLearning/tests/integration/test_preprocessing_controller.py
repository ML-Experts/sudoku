import unittest

from fastapi.testclient import TestClient

from api.dependencies import get_preprocess_board_command_handler
from api.main import create_app
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
            message="Nie udało się wykryć konturu planszy Sudoku.",
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
                "message": "Nie udało się wykryć konturu planszy Sudoku.",
            },
        )


if __name__ == "__main__":
    unittest.main()
