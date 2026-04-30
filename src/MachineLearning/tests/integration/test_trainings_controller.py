import os
import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import create_app


class TrainingsControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.previous_runner = os.environ.get("ML_TRAINING_RUNNER")
        self.previous_interval = os.environ.get(
            "ML_TRAINING_MOCK_INTERVAL_SECONDS"
        )
        self.previous_callback_max_attempts = os.environ.get(
            "ML_TRAINING_TERMINAL_EVENT_MAX_ATTEMPTS"
        )
        self.previous_allowed_output_roots = os.environ.get(
            "ML_TRAINING_ALLOWED_OUTPUT_ROOTS"
        )
        os.environ["ML_TRAINING_MOCK_INTERVAL_SECONDS"] = "0"
        os.environ["ML_TRAINING_TERMINAL_EVENT_MAX_ATTEMPTS"] = "1"
        os.environ["ML_TRAINING_RUNNER"] = "mock"
        os.environ["ML_TRAINING_ALLOWED_OUTPUT_ROOTS"] = ""
        self.client = TestClient(create_app())

    def tearDown(self) -> None:
        if self.previous_runner is None:
            os.environ.pop("ML_TRAINING_RUNNER", None)
        else:
            os.environ["ML_TRAINING_RUNNER"] = self.previous_runner

        if self.previous_interval is None:
            os.environ.pop("ML_TRAINING_MOCK_INTERVAL_SECONDS", None)
        else:
            os.environ["ML_TRAINING_MOCK_INTERVAL_SECONDS"] = (
                self.previous_interval
            )

        if self.previous_callback_max_attempts is None:
            os.environ.pop("ML_TRAINING_TERMINAL_EVENT_MAX_ATTEMPTS", None)
        else:
            os.environ["ML_TRAINING_TERMINAL_EVENT_MAX_ATTEMPTS"] = (
                self.previous_callback_max_attempts
            )

        if self.previous_allowed_output_roots is None:
            os.environ.pop("ML_TRAINING_ALLOWED_OUTPUT_ROOTS", None)
        else:
            os.environ["ML_TRAINING_ALLOWED_OUTPUT_ROOTS"] = (
                self.previous_allowed_output_roots
            )

    def test_post_trainings_should_accept_and_create_mock_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root_path = Path(temp_directory)
            base_model_path = root_path / "base"
            base_model_path.mkdir(parents=True)
            manifest_path = base_model_path / "model.json"
            artifact_path = base_model_path / "model.keras"
            dataset_path = root_path / "data" / "dataset.npz"
            dataset_path.parent.mkdir(parents=True)
            artifact_path.write_text("mock-base-artifact", encoding="utf-8")
            dataset_path.write_text("mock-dataset", encoding="utf-8")
            manifest_path.write_text(
                json.dumps(
                    {
                        "framework": "pytorch",
                        "architecture": {
                            "type": "custom-cnn-v1",
                            "family": "cnn",
                            "numClasses": 10,
                            "inputChannels": 1,
                            "inputHeight": 28,
                            "inputWidth": 28,
                            "inputProfile": "default-28x28-v1",
                        },
                        "artifacts": {
                            "primaryArtifactRelativePath": "artifacts/model.keras",
                            "format": "pytorch-state-dict",
                        },
                        "capabilities": {
                            "canStartTraining": True,
                            "canUseForInference": False,
                        },
                    }
                ),
                encoding="utf-8",
            )
            output_model_path = root_path / "models" / "mock-run"
            payload = {
                "runName": "mock-run",
                "baseModel": {
                    "name": "cnn-mnist-baseline",
                    "directoryPath": str(base_model_path),
                    "manifestPath": str(manifest_path),
                    "primaryArtifactPath": str(artifact_path),
                    "inputProfile": "default-28x28-v1",
                    "sourceType": "bootstrap",
                },
                "processedDataset": {
                    "name": "sudokuDigitsV1",
                    "filePath": str(dataset_path),
                    "preprocessingProfile": "default-28x28-v1",
                },
                "resolvedConfiguration": {
                    "trainingMode": "fineTuning",
                    "trainingProfileName": "cnn-default-v1",
                    "augmentationProfileName": "digits-light-v1",
                    "benchmarkName": "sudoku-benchmark-v1",
                    "seed": 1234,
                },
                "outputModel": {
                    "name": "mock-run",
                    "directoryPath": str(output_model_path),
                },
                "outputPaths": {
                    "runDirectoryPath": str(root_path / "runs" / "mock-run"),
                    "reportDirectoryPath": str(
                        root_path / "reports" / "mock-run"
                    ),
                    "benchmarkDirectoryPath": str(root_path / "benchmark"),
                    "temporaryWorkingDirectoryPath": str(
                        root_path / "tmp" / "mock-run"
                    ),
                },
            }

            response = self.client.post("/ml/trainings", json=payload)

            self.assertEqual(response.status_code, 202)
            self.assertEqual(response.json()["status"], "queued")
            self.assertTrue(
                (output_model_path / "artifacts" / "model.keras").is_file()
            )
            self.assertTrue(
                (root_path / "reports" / "mock-run" / "summary.json").is_file()
            )


if __name__ == "__main__":
    unittest.main()
