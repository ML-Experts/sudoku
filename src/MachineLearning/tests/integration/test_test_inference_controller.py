import json
import os
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np
import torch
from fastapi.testclient import TestClient

from api.main import create_app
from infrastructure.training.model.custom_digit_cnn_v1 import CustomDigitCnnV1


class TestInferenceControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._managed_environment_names = (
            "ML_EXAMPLES_UPLOADS_DIR",
            "ML_MODELS_ACTIVE_DIR",
            "ML_MODELS_REGISTRY_DIR",
            "ML_TRAINING_DEVICE",
        )
        self._previous_environment = {
            name: os.environ.get(name) for name in self._managed_environment_names
        }

    def tearDown(self) -> None:
        for name, previous_value in self._previous_environment.items():
            if previous_value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = previous_value

    def test_get_test_inteference_should_return_digit_from_active_model(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root_path = Path(temp_directory)
            examples_path = root_path / "examples"
            active_path = root_path / "models" / "active"
            registry_path = root_path / "models" / "registry"
            model_path = registry_path / "digit-model"
            artifacts_path = model_path / "artifacts"
            examples_path.mkdir(parents=True)
            active_path.mkdir(parents=True)
            artifacts_path.mkdir(parents=True)

            cv2.imwrite(
                str(examples_path / "sample.png"),
                np.full((32, 32, 3), 255, dtype=np.uint8),
            )
            self._write_model(model_path, expected_digit=7)
            (active_path / "inference.json").write_text(
                json.dumps({"modelName": "digit-model"}),
                encoding="utf-8",
            )

            os.environ["ML_EXAMPLES_UPLOADS_DIR"] = str(examples_path)
            os.environ["ML_MODELS_ACTIVE_DIR"] = str(active_path)
            os.environ["ML_MODELS_REGISTRY_DIR"] = str(registry_path)
            os.environ["ML_TRAINING_DEVICE"] = "cpu"
            client = TestClient(create_app())

            response = client.get("/ml/test/inteference/sample")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"digit": 7})

    def _write_model(self, model_path: Path, expected_digit: int) -> None:
        manifest_path = model_path / "model.json"
        artifact_path = model_path / "artifacts" / "model.pt"
        model = CustomDigitCnnV1(num_classes=10)
        state_dict = model.state_dict()
        for key, value in state_dict.items():
            state_dict[key] = torch.zeros_like(value)
        state_dict["classifier.4.bias"][expected_digit] = 1.0

        torch.save(state_dict, artifact_path)
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
                        "primaryArtifactRelativePath": "artifacts/model.pt",
                        "format": "pytorch-state-dict",
                    },
                    "capabilities": {
                        "canStartTraining": True,
                        "canUseForInference": True,
                    },
                }
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
