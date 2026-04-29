import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import create_app


class TrainingsControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.previous_interval = os.environ.get(
            "ML_TRAINING_MOCK_INTERVAL_SECONDS"
        )
        self.previous_callback_max_attempts = os.environ.get(
            "ML_TRAINING_MOCK_CALLBACK_MAX_ATTEMPTS"
        )
        os.environ["ML_TRAINING_MOCK_INTERVAL_SECONDS"] = "0"
        os.environ["ML_TRAINING_MOCK_CALLBACK_MAX_ATTEMPTS"] = "1"
        self.client = TestClient(create_app())

    def tearDown(self) -> None:
        if self.previous_interval is None:
            os.environ.pop("ML_TRAINING_MOCK_INTERVAL_SECONDS", None)
        else:
            os.environ["ML_TRAINING_MOCK_INTERVAL_SECONDS"] = (
                self.previous_interval
            )

        if self.previous_callback_max_attempts is None:
            os.environ.pop("ML_TRAINING_MOCK_CALLBACK_MAX_ATTEMPTS", None)
        else:
            os.environ["ML_TRAINING_MOCK_CALLBACK_MAX_ATTEMPTS"] = (
                self.previous_callback_max_attempts
            )

    def test_post_trainings_should_accept_and_create_mock_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root_path = Path(temp_directory)
            produced_model_path = root_path / "models" / "mock-run" / "artifacts"
            payload = {
                "runName": "mock-run",
                "baseModel": {
                    "name": "cnn-mnist-baseline",
                    "manifestPath": str(root_path / "base" / "model.json"),
                    "primaryArtifactPath": str(root_path / "base" / "model.keras"),
                    "inputProfile": "default-28x28-v1",
                },
                "dataset": {
                    "name": "sudokuDigitsV1",
                    "artifactPath": str(root_path / "data" / "dataset.npz"),
                    "preprocessingProfile": "default-28x28-v1",
                },
                "training": {
                    "mode": "fineTuning",
                    "trainingProfileName": "cnn-default-v1",
                    "augmentationProfileName": "digits-light-v1",
                    "benchmarkName": "sudoku-benchmark-v1",
                    "seed": 1234,
                },
                "output": {
                    "runDirectoryPath": str(root_path / "runs" / "mock-run"),
                    "reportsDirectoryPath": str(root_path / "reports" / "mock-run"),
                    "workingDirectoryPath": str(root_path / "tmp" / "mock-run"),
                    "producedModelName": "mock-run",
                    "producedModelArtifactsDirectoryPath": str(
                        produced_model_path
                    ),
                },
                "callbacks": {
                    "eventsPath": "/internal/ml/trainings/mock-run/events"
                },
            }

            response = self.client.post("/ml/trainings", json=payload)

            self.assertEqual(response.status_code, 202)
            self.assertEqual(response.json()["accepted"], True)
            self.assertTrue((produced_model_path / "model.keras").is_file())
            self.assertTrue(
                (root_path / "reports" / "mock-run" / "report.json").is_file()
            )


if __name__ == "__main__":
    unittest.main()
