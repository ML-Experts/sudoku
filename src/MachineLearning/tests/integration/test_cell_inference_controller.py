import base64
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


class CellInferenceControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._managed_environment_names = (
            "ML_INFERENCE_DEVICE",
            "ML_INFERENCE_SUPPORTED_PROFILES",
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

    def test_put_cells_inference_should_return_digit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            manifest_path, artifact_path = self._write_model(
                Path(temp_directory),
                predicted_class_index=6,
            )
            os.environ["ML_INFERENCE_DEVICE"] = "cpu"
            os.environ["ML_INFERENCE_SUPPORTED_PROFILES"] = "default-28x28-v1"
            client = TestClient(create_app())

            response = client.put(
                "/ml/cells/inference",
                json=self._build_payload(
                    image_base64=self._encode_png(self._digit_like_cell()),
                    manifest_path=manifest_path,
                    artifact_path=artifact_path,
                ),
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"digit": 7})

    def test_put_cells_inference_should_return_null_for_empty_cell(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            manifest_path, artifact_path = self._write_model(
                Path(temp_directory),
                predicted_class_index=6,
            )
            os.environ["ML_INFERENCE_DEVICE"] = "cpu"
            os.environ["ML_INFERENCE_SUPPORTED_PROFILES"] = "default-28x28-v1"
            client = TestClient(create_app())

            response = client.put(
                "/ml/cells/inference",
                json=self._build_payload(
                    image_base64=self._encode_png(self._blank_cell()),
                    manifest_path=manifest_path,
                    artifact_path=artifact_path,
                ),
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"digit": None})

    def test_put_cells_inference_should_return_null_for_sparse_noise_cell(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            manifest_path, artifact_path = self._write_model(
                Path(temp_directory),
                predicted_class_index=6,
            )
            os.environ["ML_INFERENCE_DEVICE"] = "cpu"
            os.environ["ML_INFERENCE_SUPPORTED_PROFILES"] = "default-28x28-v1"
            client = TestClient(create_app())

            response = client.put(
                "/ml/cells/inference",
                json=self._build_payload(
                    image_base64=self._encode_png(self._sparse_noise_cell()),
                    manifest_path=manifest_path,
                    artifact_path=artifact_path,
                ),
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"digit": None})

    def test_put_cells_inference_should_reject_10_class_model(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            manifest_path, artifact_path = self._write_model(
                Path(temp_directory),
                predicted_class_index=6,
                num_classes=10,
            )
            os.environ["ML_INFERENCE_DEVICE"] = "cpu"
            os.environ["ML_INFERENCE_SUPPORTED_PROFILES"] = "default-28x28-v1"
            client = TestClient(create_app())

            response = client.put(
                "/ml/cells/inference",
                json=self._build_payload(
                    image_base64=self._encode_png(self._digit_like_cell()),
                    manifest_path=manifest_path,
                    artifact_path=artifact_path,
                ),
            )

            self.assertEqual(response.status_code, 422)
            self.assertEqual(response.json()["errorType"], "inference_model_not_allowed")

    def _build_payload(
        self,
        image_base64: str,
        manifest_path: str,
        artifact_path: str,
    ) -> dict[str, object]:
        return {
            "image": {
                "mimeType": "image/png",
                "base64": image_base64,
            },
            "activeModel": {
                "name": "digit-model",
                "manifestPath": manifest_path,
                "primaryArtifactPath": artifact_path,
                "inputProfile": "default-28x28-v1",
            },
            "resolvedConfiguration": {
                "inferenceProfileName": "default-28x28-v1",
                "emptyCellInnerMarginRatio": 0.12,
                "emptyCellDarkPixelRatioThreshold": 0.02,
                "centerAreaRatio": 0.5,
                "minComponentAreaRatio": 0.02,
                "lineArtifactMinSpanRatio": 0.5,
                "lineArtifactMaxThicknessRatio": 0.07,
            },
        }

    def _write_model(
        self,
        root_path: Path,
        predicted_class_index: int,
        num_classes: int = 9,
    ) -> tuple[str, str]:
        model_path = root_path / "digit-model"
        artifacts_path = model_path / "artifacts"
        artifacts_path.mkdir(parents=True)

        manifest_path = model_path / "model.json"
        artifact_path = artifacts_path / "model.pt"
        model = CustomDigitCnnV1(num_classes=num_classes)
        state_dict = model.state_dict()
        for key, value in state_dict.items():
            state_dict[key] = torch.zeros_like(value)
        state_dict["classifier.4.bias"][predicted_class_index] = 1.0

        torch.save(state_dict, artifact_path)
        manifest_path.write_text(
            json.dumps(
                {
                    "framework": "pytorch",
                    "architecture": {
                        "type": "custom-cnn-v1",
                        "family": "cnn",
                        "numClasses": num_classes,
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
        return str(manifest_path), str(artifact_path)

    def _encode_png(self, image: np.ndarray) -> str:
        success, encoded = cv2.imencode(".png", image)
        self.assertTrue(success)
        return base64.b64encode(encoded.tobytes()).decode("ascii")

    def _blank_cell(self) -> np.ndarray:
        return np.full((32, 32, 3), 255, dtype=np.uint8)

    def _digit_like_cell(self) -> np.ndarray:
        image = self._blank_cell()
        cv2.putText(
            image,
            "7",
            (8, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 0),
            2,
            cv2.LINE_AA,
        )
        return image

    def _sparse_noise_cell(self) -> np.ndarray:
        image = self._blank_cell()
        image[15:17, 15:17] = (0, 0, 0)
        return image


if __name__ == "__main__":
    unittest.main()
